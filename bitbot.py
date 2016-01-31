import os, sys
import sqlite3
import time
import datetime
import requests,json
import utils
from bitcoin_trader import *
from bitconfig import *
from bit_wallet import *
from event_manager import *
import warnings
import random

class BitDataSource(object):
  def __init__(self, should_persist=False, query_rate=1.0):
    self.should_persist = should_persist
    self.query_rate = query_rate

  def query(self):
    return 0.0

class BitstampDataSource(BitDataSource):
  BITSTAMP_URL = 'http://www.bitstamp.net/api/ticker/'

  def __init__(self):
    super(BitstampDataSource, self).__init__(True, 5.0)

  def query(self):
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      r = requests.get(self.BITSTAMP_URL)
    priceFloat = float(json.loads(r.text)['last'])
    return priceFloat

class LinearDataSource(BitDataSource):
  def __init__(self, start_price = 420.00, growth_rate = 1.0, query_rate=1.0):
    self.last_price = start_price
    self.growth_rate = growth_rate
    super(LinearDataSource, self).__init__(False, query_rate)

  def query(self):
    self.last_price += self.growth_rate
    return self.last_price

class BounceDataSource(BitDataSource):
  def __init__(self, start_price = 420.00, min_price= 300.00, max_price=500.00, growth_rate = 1.0, query_rate=1.0):
    self.last_price = start_price
    self.growth_rate = growth_rate
    self.min_price = min_price
    self.max_price = max_price

    self.current_growth_rate = growth_rate
    super(BounceDataSource, self).__init__(False, query_rate)

  def query(self):
    self.last_price += self.current_growth_rate
    if(self.last_price > self.max_price):
      self.last_price = self.max_price
      self.current_growth_rate *= -1
    elif(self.last_price < self.min_price):
      self.last_price = self.min_price
      self.current_growth_rate *= -1
    return self.last_price

class BitBot:
  """Bitcoin trading bot"""
  SECONDS_PER_MINUTE = 60
  SECONDS_PER_HOUR = 3600
  DROP_TABLE_QUERY = "DROP TABLE bitcoin_prices;"
  CREATE_TABLE_QUERY = "CREATE TABLE bitcoin_prices(id INTEGER PRIMARY KEY AUTOINCREMENT, quote_time INTEGER, price FLOAT, slope FLOAT DEFAULT 0);"
  RECENT_PRICES_QUERY = 'SELECT quote_time, price, slope FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time} ORDER BY quote_time ASC'


  def __init__(self, data_source, starting_cash):
    self.conn = utils.connect_to_database('bitcoin.sqlite')
    self.c = self.conn.cursor()
    self.config = BitConfig()

    self.last_price = 0.0
    self.last_time = 0
    current_time = int(time.time())
    self.db_results = self.query_db(current_time - data_source.query_rate, current_time)
    self.register_traders(self.db_results, starting_cash)
    self.data_source = data_source
    if(self.data_source.should_persist):
      EventManager.add_subscription("price_change", [], self.handle_price_event)

  def initialize_db(self):
    try:
      self.c.execute(self.DROP_TABLE_QUERY)
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def handle_price_event(self, event):
    self.insert(event.metadata['price'], event.metadata['time'], event.metadata['slope'])

  def insert(self, price, time, slope):
    query = "INSERT INTO bitcoin_prices (quote_time, price, slope) VALUES ('{quote_time}', '{quote_price}', '{quote_slope}');"\
        .format(quote_time=time, quote_price=price, quote_slope=slope)
    self.c.execute(query)

  def query_db(self, min_time, max_time):
    query = self.RECENT_PRICES_QUERY.format(min_quote_time=min_time, max_quote_time=max_time)
    self.c.execute(query)
    return self.c.fetchall()

  def print_db_results(self, db_results):
    for row in db_results:
      date_string = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S')
      self.last_price = row[1]
      print date_string + "\t" + utils.format_dollars(self.last_price) + "\t" + utils.format_slope(row[2])

  def register_traders(self, db_results, starting_cash):
    min_earnings = self.config.getfloat("Trader", "minearningspershare")
    trade_threshold = self.config.getfloat("Trader", "priceequivalencythreshold")
    wallet = BitWallet(starting_cash)
    TraderManager.add_trader(HighLowTrader(wallet, db_results, trade_threshold, min_earnings))

  def init_monitor(self):
    self.last_price = 0.0
    self.last_time = 0
    current_time = int(time.time())
    db_results = self.query_db(current_time - self.data_source.query_rate, current_time)
    self.print_db_results(db_results)

  def print_header(self):
    print "Time\t\t\tPrice\tSlope\t\tRecommendation"

  def monitor(self):
    self.print_header()
    self.init_monitor()

    while True:
      self.on_awake()
      time.sleep(self.data_source.query_rate)

  def print_price_data(self, price, time, slope, recommendations):
    date_string = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
    rec_string = ""
    for rec in recommendations:
      rec_string = rec_string + ", (" + rec[0] + "," + rec[1] + ")"
      print date_string + "\t" + utils.format_dollars(price)  + "\t" + utils.format_slope(slope) + "\t" + rec_string

  def compute_slope(self, price, time):
    return (price - self.last_price) / (time - self.last_time)

  def on_price_change(self, current_price):
    current_time = int(time.time())
    if self.last_time != current_time:
      slope = self.compute_slope(current_price, current_time)
      EventManager.notify(Event("price_change", [], {'price':current_price, 'time': current_time, 'slope': slope }))

      recommendations = TraderManager.compute_recommended_actions()
      self.print_price_data(current_price, current_time, slope, recommendations)
      self.last_time = current_time

  def on_awake(self):
    try:
      current_price = self.data_source.query()
      if utils.format_dollars(self.last_price) != utils.format_dollars(current_price):
        self.on_price_change(current_price)
        self.last_price = current_price
    except ValueError:
      print "Error querying Bitstamp API"
    except requests.ConnectionError:
      print "Error querying Bitstamp API"

  def __del__(self):
    self.conn.commit()
    self.conn.close()

starting_cash = 1000.00
#data_source = BitstampDataSource()
#data_source = LinearDataSource(start_price = 420.00, growth_rate = 1.0, query_rate=1)
data_source = BounceDataSource(start_price = 420.00, min_price= 300.00, max_price=500.00, growth_rate = 1.0, query_rate=0.1)
bitbot = BitBot(data_source, starting_cash)
bitbot.monitor()

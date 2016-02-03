import os, sys
import sqlite3
import time
import datetime
import requests,json
import utils
import math
from bitcoin_trader import *
from bitconfig import *
from bit_wallet import *
from bit_data_sources import *
from db import *
from event_manager import *
import warnings
import random

class BitBot:
  """Bitcoin trading bot"""
  SECONDS_PER_MINUTE = 60
  SECONDS_PER_HOUR = 3600
  DROP_TABLE_QUERY = "DROP TABLE bitcoin_prices;"
  CREATE_TABLE_QUERY = "CREATE TABLE bitcoin_prices(id INTEGER PRIMARY KEY AUTOINCREMENT, quote_time INTEGER, price FLOAT, slope FLOAT DEFAULT 0);"
  RECENT_PRICES_QUERY = 'SELECT quote_time, price, slope FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time} ORDER BY quote_time ASC'

  def __init__(self, wallet, data_source, trader):
    self.last_price = 0.0
    self.last_time = 0
    self.trader = trader
    self.trader.register_listeners()

    self.wallet = wallet
    current_time = int(time.time())
    query = self.RECENT_PRICES_QUERY.format(min_quote_time=int(current_time - self.SECONDS_PER_HOUR), max_quote_time=int(current_time))
    self.db_results = DB.query(DB.BITCOIN_DB, query)
    self.data_source = data_source

    if(self.data_source.should_persist):
      EventManager.add_subscription("price_change", [], self.handle_price_event)

  def initialize_db(self):
    try:
      DB.execute(DB.BITCOIN_DB, self.DROP_TABLE_QUERY)
      DB.execute(DB.BITCOIN_DB, self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def handle_price_event(self, event):
    self.insert(event.metadata['price'], event.metadata['time'], event.metadata['slope'])

  def insert(self, price, time, slope):
    query = "INSERT INTO bitcoin_prices (quote_time, price, slope) VALUES ('{quote_time}', '{quote_price}', '{quote_slope}');"\
        .format(quote_time=time, quote_price=price, quote_slope=slope)
    DB.execute(DB.BITCOIN_DB, query)

  def print_db_results(self, db_results):
    for row in db_results:
      date_string = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S')
      self.last_price = row[1]
      print date_string + "\t" + utils.format_dollars(self.last_price) + "\t" + utils.format_slope(row[2])

  def init_monitor(self):
    self.last_price = 0.0
    self.last_time = 0
    current_time = int(time.time())
    self.print_db_results(self.db_results)

  def print_header(self):
    print "Time\t\t\tPrice\tSlope\t\tRecommendation"

  def monitor(self):
    self.print_header()
    self.init_monitor()

    try:
      while True:
        self.on_awake()
        time.sleep(self.data_source.query_rate)
    except KeyboardInterrupt:
      print "Closing"

  def print_price_data(self, price, time, slope, recommendations):
    date_string = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
    rec_string = ""
    try:
      for rec in recommendations:
        rec_string = rec_string + ", (" + rec[0] + "," + rec[1] + ")"
        print date_string + "\t" + utils.format_dollars(price)  + "\t" + utils.format_slope(slope) + "\t" + rec_string
    except ValueError:
      return ValueError

  def compute_slope(self, price, time):
    slope = 0.0
    if(time > self.last_time):
      slope = (price - self.last_price) / (time - self.last_time)
    return slope

  def on_price_change(self, current_price):
    current_time = int(time.time())
    if self.last_time != current_time:
      slope = self.compute_slope(current_price, current_time)
      recommendation = self.trader.compute_recommended_action()
      EventManager.notify(Event("price_change", [recommendation[0]], {'price':current_price, 'time': current_time, 'slope': slope }))

      self.print_price_data(current_price, current_time, slope, [recommendation])
      self.last_time = current_time
      self.last_price = current_price      

  def on_awake(self):
    try:
      current_price = self.data_source.query()
    except ValueError:
      print "Error querying Bitstamp API"
    except requests.ConnectionError:
      print "Error querying Bitstamp API"
    if utils.format_dollars(self.last_price) != utils.format_dollars(current_price):
      self.on_price_change(current_price)

  def __del__(self):
    for db in DB.conn:
      DB.conn[db].commit()
      DB.conn[db].close()


DB.query(DB.WALLET_DB, "DELETE FROM investments")

#INPUTS
starting_cash = 1000.00
wallet = BitWallet(starting_cash)
config = BitConfig()

# DATA SOURCES
bitstamp_data_source = BitstampDataSource()
linear_data_source = LinearDataSource(start_price = 420.00, growth_rate = 1.0, query_rate=1)
bounce_data_source = BounceDataSource(start_price = 420.00, min_price= 300.00, max_price=500.00, growth_rate = 1.0, query_rate=0.1)

#TRADERS
min_earnings = config.getfloat("Trader", "minearningspershare")
trade_threshold = config.getfloat("Trader", "priceequivalencythreshold")
trend_count_threshold = config.getint("Trader", "trendcountthreshold")

high_low_trader = HighLowTrader(wallet, [], trade_threshold, min_earnings)
stop_loss_trader = StopLossTrader(wallet, [], trade_threshold, trend_count_threshold)

#INITIALIZE
bitbot = BitBot(wallet, bounce_data_source, stop_loss_trader)
bitbot.monitor()

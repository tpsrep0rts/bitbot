import os, sys
import sqlite3
import time
import datetime
import requests,json
import utils
from bitcoin_trader import *
import warnings
import random

class BitBot:
  """Bitcoin trading bot"""

  BITSTAMP_URL = 'http://www.bitstamp.net/api/ticker/'
  SECONDS_PER_MINUTE = 60
  SECONDS_PER_HOUR = 3600
  REFRESH_INTERVAL = 5
  QUERY_INTERVAL = 3600
  DROP_TABLE_QUERY = "DROP TABLE bitcoin_prices;"
  CREATE_TABLE_QUERY = "CREATE TABLE bitcoin_prices(id INTEGER PRIMARY KEY AUTOINCREMENT, quote_time INTEGER, price FLOAT, slope FLOAT DEFAULT 0);"
  RECENT_PRICES_QUERY = 'SELECT quote_time, price, slope FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time} ORDER BY quote_time ASC'


  def __init__(self):
    self.conn = utils.connect_to_database('bitcoin.sqlite')
    self.c = self.conn.cursor()

  def initialize_db(self):
    try:
      self.c.execute(self.DROP_TABLE_QUERY)
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def insert(self, price, time, slope):
    query = "INSERT INTO bitcoin_prices (quote_time, price, slope) VALUES ('{quote_time}', '{quote_price}', '{quote_slope}');"\
        .format(quote_time=time, quote_price=price, quote_slope=slope)
    self.c.execute(query)

  def query_bitstamp(self):
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      r = requests.get(self.BITSTAMP_URL)
    priceFloat = float(json.loads(r.text)['last'])
    return priceFloat

  def query_db(self, min_time, max_time):
    self.c.execute(self.RECENT_PRICES_QUERY.format(min_quote_time=min_time, max_quote_time=max_time))
    return self.c.fetchall()

  def print_db_results(self, db_results):
    for row in db_results:
      date_string = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S')
      self.last_price = row[1]
      print date_string + "\t" + utils.format_dollars(self.last_price) + "\t" + utils.format_slope(row[2])


  def register_traders(self, db_results):
    TraderManager.add_trader(HighLowTrader(db_results, 0.1))

  def monitor(self):
    self.last_price = 0.0
    self.last_time = 0

    print "Time\t\t\tPrice\tSlope\t\tRecommendation"
    current_time = int(time.time())
    db_results = self.query_db(current_time - self.QUERY_INTERVAL, current_time)
    self.print_db_results(db_results)
    self.register_traders(db_results)

    while True:
      self.on_awake()
      time.sleep(self.REFRESH_INTERVAL)

  def on_price_change(self, current_price):
    current_time = int(time.time())
    if self.last_time != current_time:
      slope = (current_price - self.last_price) / (current_time - self.last_time)
      self.insert(current_price, current_time, slope)
      TraderManager.add_bitcoin_data(current_price, slope, current_time)
      recommendations = TraderManager.compute_recommended_actions()

      date_string = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
      rec_string = ""
      for rec in recommendations:
        rec_string = rec_string + ", (" + rec[0] + "," + rec[1] + ")"
      print date_string + "\t" + utils.format_dollars(current_price)  + "\t" + utils.format_slope(slope) + "\t" + rec_string
      self.last_time = current_time


  def on_awake(self):
    try:
      current_price = self.query_bitstamp()
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

bitbot = BitBot()
bitbot.monitor()

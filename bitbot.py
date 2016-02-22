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

  def get_data_source(self, config):
    data_sources = {
      "BitstampDataSource":  BitstampDataSource(),
      "LinearDataSource":  LinearDataSource.from_config(config),
      "BounceDataSource":  BounceDataSource.from_config(config),
      "RandomBounceDataSource": RandomBounceDataSource.from_config(config)
    }

    data_source_string = config.get("BitBot", "selecteddatasource")
    if data_source_string in data_sources:
      selected_data_source = data_sources[data_source_string]
    else:
      print "Data source not found: " + data_source_string
      selected_data_source = data_sources["BitstampDataSource"]
    return selected_data_source

  def get_trader(self, config, wallet, db_results = []):
    traders = {
      "HighLowTrader":  HighLowTrader.from_config(config, wallet, db_results),
      "StopLossTrader":  StopLossTrader.from_config(config, wallet, db_results)
    }

    trader_string = config.get("BitBot", "selectedtrader")
    if trader_string in traders:
      selected_trader = traders[trader_string]
    else:
      print "Trader not found: " + trader_string
      selected_trader = traders["StopLossTrader"]
    return selected_trader

  def get_wallet(self, config):
    return BitWallet.from_config(config)

  def __init__(self):
    DB.query(DB.WALLET_DB, "DELETE FROM investments")


    self.last_price = 0.0
    self.last_time = 0

    current_time = int(time.time())
    query = self.RECENT_PRICES_QUERY.format(min_quote_time=int(current_time - self.SECONDS_PER_HOUR), max_quote_time=int(current_time))
    self.db_results = DB.query(DB.BITCOIN_DB, query)

    self.config = BitConfig()
    self.data_source = self.get_data_source(self.config)
    self.wallet = self.get_wallet(self.config)
    self.trader = self.get_trader(self.config, self.wallet, self.db_results)
    self.trader.register_listeners()

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
    print "Time\t\t\tPrice\tSlope\t\t" + self.trader.get_recommendation().get_header()

  def monitor(self):
    self.print_header()
    self.init_monitor()
    
    try:
      while True:
        self.on_awake()
        time.sleep(self.data_source.query_rate)
    except KeyboardInterrupt:
      pass

  def print_price_data(self, price, time, slope, recommendation):
    date_string = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
    print date_string + "\t" + utils.format_dollars(price)  + "\t" + utils.format_slope(slope) + "\t" + str(recommendation)


  def compute_slope(self, price, time):
    slope = 0.0
    if(time > self.last_time):
      slope = (price - self.last_price) / (time - self.last_time)
    return slope

  def on_price_change(self, current_price):
    current_time = int(time.time())
    if self.last_time != current_time:
      slope = self.compute_slope(current_price, current_time)
      recommendation_obj = self.trader.get_recommendation()
      EventManager.notify(Event("price_change", [recommendation_obj.recommendation], {'price':current_price, 'time': current_time, 'slope': slope }))
      self.print_price_data(current_price, current_time, slope, recommendation_obj)
      self.last_time = current_time
      self.last_price = current_price      

  def on_awake(self):
    try:
      current_price = self.data_source.query()
      if utils.format_dollars(self.last_price) != utils.format_dollars(current_price):
        self.on_price_change(current_price)
    except ValueError:
      print "Error querying Bitstamp API"
    except requests.ConnectionError:
      print "Error querying Bitstamp API"

bitbot = BitBot()
bitbot.monitor()

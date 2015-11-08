import os, sys
import sqlite3
import time
import datetime
import requests,json
import utils
from bitcoin_trader import *
import warnings

class BitBot:
  """Bitcoin trading bot"""

  BITSTAMP_URL = 'http://www.bitstamp.net/api/ticker/'
  SECONDS_PER_MINUTE = 60
  SECONDS_PER_HOUR = 3600
  REFRESH_INTERVAL = 5
  QUERY_INTERVAL = 300
  DROP_TABLE_QUERY = "DROP TABLE bitcoin_prices;"
  CREATE_TABLE_QUERY = "CREATE TABLE bitcoin_prices(id INTEGER PRIMARY KEY AUTOINCREMENT, quote_time INTEGER , price FLOAT);"

  def __init__(self):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'bitcoin.sqlite')
    self.c = self.conn.cursor()

  def initialize_db(self):
    try:
      self.c.execute(self.DROP_TABLE_QUERY)
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def insert(self, price, time):
    query = "INSERT INTO bitcoin_prices (quote_time, price) VALUES ('{quote_time}', '{quote_price}');"\
        .format(quote_time=time, quote_price=price)
    self.c.execute(query)

  def query_bitstamp(self):
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      r = requests.get(self.BITSTAMP_URL)
    priceFloat = float(json.loads(r.text)['last'])
    TraderManager.add_bitcoin_data(priceFloat)
    return priceFloat

  def query_db(self, min_time, max_time):
    self.c.execute('SELECT quote_time, price FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time}'.\
        format(min_quote_time=min_time, max_quote_time=max_time))
    return self.c.fetchall()

  def print_db_results(self, db_results):
    for row in db_results:
      date_string = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S')
      self.last_price = self.format_dollars(row[1])
      print self.last_price + "\t" + date_string

  def format_dollars(self, dollars):
    return  "{:.2f}".format(dollars)

  def register_traders(self, db_results):
    TraderManager.add_trader(ContentTrader(db_results))
    TraderManager.add_trader(BullTrader(db_results))
    TraderManager.add_trader(BearTrader(db_results))
    TraderManager.add_trader(HoldUntilDeclineAmt(db_results, 1.0))
    TraderManager.add_trader(HoldUntilDeclinePct(db_results, 1.0))

  def start(self):
    self.last_price = "0.00"
    print "Price\tTime"
    current_time = int(time.time())
    db_results = self.query_db(current_time - self.QUERY_INTERVAL, current_time)
    self.print_db_results(db_results)
    self.register_traders(db_results)

    while True:
      self.on_awake()
      time.sleep(self.REFRESH_INTERVAL)

  def on_awake(self):
    try:
      current_price =self.format_dollars(self.query_bitstamp())

      current_time = int(time.time())
      date_string = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')

      if(self.last_price != current_price):
        TraderManager.add_bitcoin_data(current_price)
        self.insert(current_price, current_time)
        self.last_price = current_price
        recommendations = TraderManager.compute_recommended_actions()
        
        print current_price  + "\t" + date_string + " Recommendations: " + ",".join(recommendations)
      else:
        print current_price  + "\t" + date_string
    except requests.ConnectionError:
      print "Error querying Bitstamp API"

  def __del__(self):
    self.conn.commit()
    self.conn.close()

bitbot = BitBot()
bitbot.start()

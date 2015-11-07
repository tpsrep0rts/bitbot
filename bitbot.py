import os, sys
import sqlite3
import time
import datetime
import requests,json
import utils
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
    return priceFloat

  def query_db(self, min_time, max_time):
    self.c.execute('SELECT * FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time}'.\
        format(min_quote_time=min_time, max_quote_time=max_time))
    return self.c.fetchall()

  def print_db_results(self, db_results):
    for row in db_results:
      date_string = datetime.datetime.fromtimestamp(row[1]).strftime('%Y-%m-%d %H:%M:%S')
      self.last_price = "{:.2f}".format(row[2])
      print self.last_price + "\t" + date_string

  def start(self):
    self.last_price = "0.00"
    print "Price\tTime"
    current_time = int(time.time())
    db_results = self.query_db(current_time - self.QUERY_INTERVAL, current_time)
    self.print_db_results(db_results)

    while True:
      try:
        current_price = "{:.2f}".format(self.query_bitstamp())
        current_time = int(time.time())
        date_string = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
        print current_price  + "\t" + date_string

        if(self.last_price != current_price):
          self.insert(current_price, current_time)
          self.last_price = current_price
      except requests.ConnectionError:
        print "Error querying Bitstamp API"
      time.sleep(self.REFRESH_INTERVAL)

  def __del__(self):
    self.conn.commit()
    self.conn.close()

bitbot = BitBot()
bitbot.start()
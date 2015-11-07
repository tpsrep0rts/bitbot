import os
import sqlite3
import time
import datetime
import requests,json

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

  def query_db(self, min_time, max_time):
    self.c.execute('SELECT * FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time}'.\
        format(min_quote_time=min_time, max_quote_time=max_time))
    all_rows = self.c.fetchall()
    for row in all_rows:
      date_string = datetime.datetime.fromtimestamp(row[1]).strftime('%Y-%m-%d %H:%M:%S')
      print "{:.2f}".format(row[2])  + "\t" + date_string

  def insert(self, price, time):
    query = "INSERT INTO bitcoin_prices (quote_time, price) VALUES ('{quote_time}', '{quote_price}');"\
        .format(quote_time=time, quote_price=price)
    self.c.execute(query)

  def query_bitstamp(self):
    r = requests.get(self.BITSTAMP_URL)
    priceFloat = float(json.loads(r.text)['last'])
    return priceFloat

  def start(self):
    print "Price\tTime"
    current_time = int(time.time())
    self.query_db(current_time - self.QUERY_INTERVAL, current_time)
    last_price = "0.00"
    
    while True:
      try:
        current_price = self.query_bitstamp()
        current_time = int(time.time())
        date_string = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
        print "{:.2f}".format(current_price)  + "\t" + date_string

        if(last_price != current_price):
          self.insert(current_price, current_time)
          last_price = current_price
      except requests.ConnectionError:
        print "Error querying Bitstamp API"
      time.sleep(self.REFRESH_INTERVAL)

  def __del__(self):
    self.conn.commit()
    self.conn.close()

bitbot = BitBot()
bitbot.start()

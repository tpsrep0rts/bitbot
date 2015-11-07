import os
import sqlite3
import time
import datetime

class BitBot:
  """Bitcoin trading bot"""
  def __init__(self):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'bitcoin.sqlite')
    self.c = self.conn.cursor()

  def initialize_db(self):
    try:
      self.c.execute("DROP TABLE bitcoin_prices;")
      self.c.execute("CREATE TABLE bitcoin_prices(id INTEGER PRIMARY KEY AUTOINCREMENT, quote_time INTEGER , price FLOAT);")
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def query(self, min_time, max_time):
    self.c.execute('SELECT * FROM bitcoin_prices WHERE quote_time >= {min_quote_time} AND quote_time <= {max_quote_time}'.\
        format(min_quote_time=min_time, max_quote_time=max_time))
    all_rows = self.c.fetchall()
    print "Price\tTime"
    for row in all_rows:
      date_string = datetime.datetime.fromtimestamp(row[1]).strftime('%Y-%m-%d %H:%M:%S')
      print str(row[2]) + "\t" + date_string

  def insert(self, price, time):
    query = "INSERT INTO bitcoin_prices (quote_time, price) VALUES ('{quote_time}', '{quote_price}');"\
        .format(quote_time=time, quote_price=price)
    self.c.execute(query)

  def __enter__(self):
    return self

  def __del__(self):
    self.conn.commit()
    self.conn.close()

bitbot = BitBot()
bitbot.insert('420.00', int(time.time()))

bitbot.query(time.time() - 3600, time.time())
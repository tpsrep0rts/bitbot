import os
import sqlite3
import time
import datetime
import requests,json
import msvcrt #for testing menu

class Register:
  """Currency Register"""

  REFRESH_INTERVAL = 5
  CREATE_TABLE_QUERY = "CREATE TABLE currency_register(id INTEGER PRIMARY KEY AUTOINCREMENT, usd_change FLOAT, btc_change FLOAT, trade_time INTEGER);"

  def __init__(self):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'register.sqlite')
    self.c = self.conn.cursor()

  def initialize_db(self):
    try:
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def query_db(self):
    self.c.execute("SELECT * FROM currency_register")
    all_rows = self.c.fetchall()
    print "USD+/-\tBTC+-\tTime"
    for row in all_rows:
      date_string = datetime.datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')
      print str(row[0]) + "\t" + str(row[1]) + "\t" + date_string

  def insert(self, usd, btc, trade_time):
    query = "INSERT INTO currency_register (usd_change, btc_change, trade_time) VALUES ('{usd_change}', '{btc_change}', '{trade_time}');"\
        .format(usd_change=usd, btc_change=btc, trade_time=trade_time)
    self.c.execute(query)

  def menu(self):
    print "(D)eposit USD, (W)ithdraw USD, (B)uy BTC, (S)ell BTC\r >" 
    self.choice = msvcrt.getch().lower()
    current_time = int(time.time())
    if self.choice == "d":
      self.insert(5, 0, current_time)
    elif self.choice == "w":
      self.insert(-5, 0, current_time)
    elif self.choice == "b":
      self.insert(-2, 0.05, current_time)
    elif self.choice == "s":
      self.insert(3, -0.05, current_time)

  def start(self):
    while True:
      try:
        self.query_db()
        self.menu()        
        #self.insert(current_price, int(time.time()))
        #self.query_db(time.time() - self.SECONDS_PER_HOUR, time.time())
      except requests.ConnectionError:
        print "Something went wrong"
      time.sleep(self.REFRESH_INTERVAL)
  
  def __del__(self):
    self.conn.commit()
    self.conn.close()

register = Register()
register.initialize_db()
register.start()

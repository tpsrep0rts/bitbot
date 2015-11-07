import os
import sqlite3
import time
import datetime
import requests,json

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
    row1total = 0.00
    row2total = 0.00000000
    print "ID\tUSD+/-\tBTC+-\t\tDate\t\tTime"
    for row in all_rows:
      date_string = datetime.datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d\t%H:%M:%S')
      line = str(row[0]) + "\t$"      
      if row[1]:
        row1 = "{:.2f}".format(row[1])
        row1total += row[1]
        line += str(row1);
      else: 
        line += "0.00"
      line += "\t"
      if row[2]:
        row2 = "{:.8f}".format(row[2])
        row2total += row[2]
        line+= str(row2)
      else:
        line += "0.00000000"
      line += "\t" + date_string      
      print line
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "\t$" + str(row1total) + "\t" + str(row2total)


  def insert(self, usd, btc, trade_time):
    query = "INSERT INTO currency_register (usd_change, btc_change, trade_time) VALUES ('{usd_change}', '{btc_change}', '{trade_time}');"\
        .format(usd_change=usd, btc_change=btc, trade_time=trade_time)
    self.c.execute(query)

  def menu(self):
    #print "(D)eposit USD, (W)ithdraw USD, (B)uy BTC, (S)ell BTC\r >" 
    self.choice = raw_input("\n\n(D)eposit USD, (W)ithdraw USD, (B)uy BTC, (S)ell BTC, or (Q)uery the database\n")
    current_time = int(time.time())
    if self.choice == "d":
      self.insert(5, 0, current_time)
    elif self.choice == "w":
      self.insert(-5, 0, current_time)
    elif self.choice == "b":
      self.insert(-2, 0.05, current_time)
    elif self.choice == "s":
      self.insert(3, -0.05, current_time)
    elif self.choice == "q":
      self.query_db()

  def start(self):
    self.query_db()
    while True:
      try:        
        self.menu()        
        #self.insert(current_price, int(time.time()))
        #self.query_db(time.time() - self.SECONDS_PER_HOUR, time.time())
      except requests.ConnectionError:
        print "Something went wrong"
      #time.sleep(self.REFRESH_INTERVAL)
  
  def __del__(self):
    self.conn.commit()
    self.conn.close()

register = Register()
register.initialize_db()
register.start()

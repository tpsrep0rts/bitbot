import time
import sqlite3
import os

class BitWallet:
  #DROP_TABLE_QUERY = "DROP TABLE investments;"
  CREATE_TABLE_QUERY = "CREATE TABLE investments(id INTEGER PRIMARY KEY AUTOINCREMENT, qty FLOAT, price FLOAT, standing FLOAT, purchase_time  INTEGER);"

  def __init__(self, dollars = 0, bitcoin_records = []):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'investments.sqlite')
    self.c = self.conn.cursor()
    self.dollars = dollars
    self.bitcoin_records = bitcoin_records

  def initialize_db(self):
    try:
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)

  def query_db(self):
    self.c.execute("SELECT * FROM investments")
    self.bitcoin_records = self.c.fetchall()

  def add_dollars(self, dollars):
    self.dollars += dollars

  def purchase_bitcoin(self, bitcoin_qty, bitcoin_price):
    dollar_cost = bitcoin_qty * bitcoin_price
    self.dollars -= dollar_cost
    self.bitcoin_records.append( [bitcoin_qty, bitcoin_price, dollar_cost * -1, int(time.time())] )

  def convert_bitcoin_by_index(self, index, bitcoin_pct, bitcoin_price):
    amount = self.bitcoin_records[index][0] * bitcoin_pct * bitcoin_price
    self.dollars += amount
    self.bitcoin_records[index][2] += amount
    self.bitcoin_records[index][0] = self.bitcoin_records[index][0] - self.bitcoin_records[index][0] * bitcoin_pct;

    if bitcoin_pct == 1.0:
      del self.bitcoin_records[index:index+1]

  def __str__(self):
    return "Records: " + str(self.bitcoin_records) + "\nDollars:" + str(self.dollars)


wallet = BitWallet(1000.00)

wallet.add_dollars(500.00)

wallet.purchase_bitcoin(1.5, 420)
wallet.purchase_bitcoin(.5, 420)


print wallet


wallet.convert_bitcoin_by_index(0,.5,500)
print wallet

wallet.convert_bitcoin_by_index(0,.5,500)
print wallet

wallet.convert_bitcoin_by_index(0,1.0,500)
print wallet
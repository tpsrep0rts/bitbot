import time
import sqlite3
import os
import utils

class BitWalletRecord(object):
  QTY_INDEX = 0
  PRICE_INDEX = 1
  PURCHASE_TIME_INDEX = 2

  def __init__(self, qty, price, purchase_time, index):
    self.qty = qty
    self.price = price
    self.purchase_time = purchase_time
    self.index = index


  @staticmethod
  def create(db_row, index):
    return BitWalletRecord(db_row[BitWalletRecord.QTY_INDEX], db_row[BitWalletRecord.PRICE_INDEX], 
                           db_row[BitWalletRecord.PURCHASE_TIME_INDEX], index)

  def __str__(self):
    return "index={index}, qty={qty}, price=${price}, purchase_time={purchase_time}".format(index = self.index, qty = self.qty, price = self.price, purchase_time = self.purchase_time)

class BitcoinSale(BitWalletRecord):
  def __init__(self, qty, price, profit):
    self.profit = profit
    super(self.__class__, self).__init__(qty, price, time.time(), 0.0)

class BitWallet:
  DROP_TABLE_QUERY = "DROP TABLE investments;"
  CREATE_TABLE_QUERY = "CREATE TABLE investments(id INTEGER PRIMARY KEY AUTOINCREMENT, qty FLOAT, price FLOAT, purchase_time  INTEGER);"
  SELECT_QUERY = "SELECT qty, price, purchase_time FROM investments"
  INSERT_QUERY = "INSERT INTO investments (qty, price, purchase_time) VALUES ('{bitcoin_qty}', '{bitcoin_price}', '{ptime}');"
  DELETE_QUERY = "DELETE FROM investments WHERE id='{id}';"

  def __init__(self, dollars = 0, reset_data = False):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'investments.sqlite')
    self.c = self.conn.cursor()
    self.dollars = dollars

    if(reset_data):
      self.initialize_db()
    self.sync_wallet_with_db()

  def initialize_db(self):
    try:
      self.c.execute(self.DROP_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "Table doesn't exist."   
    try:
      self.c.execute(self.CREATE_TABLE_QUERY)
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)      

  def query_db(self):
    self.c.execute(self.SELECT_QUERY)
    db_rows = self.c.fetchall()
    return db_rows

  def sync_wallet_with_db(self):
    self.bitcoin_records = {}
    self.add_db_records(self.query_db())

  def add_db_record(self, record):
    self.bitcoin_records[record.index] = record

  def add_db_records(self, db_rows):
    for index, db_row in enumerate(db_rows):
      self.add_db_record(BitWalletRecord.create(db_row, index))

  def get_account_value(self, current_bitcoin_price):
    value = self.dollars
    for index, record in self.bitcoin_records.items():
      value += record.qty * current_bitcoin_price
    return value

  def print_status(self, current_bitcoin_price):
    print "================================================================"
    print "Account value: ${value}".format(value = self.get_account_value(current_bitcoin_price))
    print "----------------------------------------------------------------"
    print "Bitcoin value: ${value}".format(value=current_bitcoin_price)
    print "----------------------------------------------------------------"
    print "Cash: ${cash}".format(cash=self.dollars)
    print "----------------------------------------------------------------"
    for index, record in self.bitcoin_records.items():
      print record
    print "================================================================\n"

  def add_dollars(self, dollars):
    self.dollars += dollars

  def add_dollars(self, dollars):
    self.dollars += dollars

  def purchase_bitcoin(self, bitcoin_qty, bitcoin_price):
    value = bitcoin_qty * bitcoin_price
    if self.dollars >= value:
      self.dollars -= value
      ptime = int(time.time())
      query = self.INSERT_QUERY.format(bitcoin_qty=bitcoin_qty, bitcoin_price=bitcoin_price, ptime = ptime)
      try:
        self.c.execute(query)
        record = BitWalletRecord(bitcoin_qty, bitcoin_price, ptime, self.c.lastrowid)
        self.add_db_record(record)
        self.conn.commit()
      except sqlite3.OperationalError as e:
        print "sqlite3 error: " + str(e)
      success = True
    else:
      success = False
    return success

  def delete_wallet_record_by_index(self, index):
    query = self.DELETE_QUERY.format(id = index)
    try:
      self.c.execute(query)
      self.conn.commit()
      del self.bitcoin_records[index]
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e) 

  def sell_bitcoin_by_index(self, index, current_bitcoin_price):
    list_record = self.bitcoin_records[index]
    value = current_bitcoin_price * list_record.qty
    profit = (current_bitcoin_price - list_record.price) * list_record.qty

    #Begin Transaction
    self.add_dollars(value)
    self.delete_wallet_record_by_index(list_record.index)
    #End Transaction
    return BitcoinSale(list_record.qty, list_record.price, profit)

  def sell_bitcoin_by_target_price(self, target_price, current_bitcoin_price):
    profit = 0.0
    qty = 0.0
    purchase_price = 0.0
    for index, record in self.bitcoin_records.items():
      if record.price <= target_price:
        purchase_sale = self.sell_bitcoin_by_index(record.index, current_bitcoin_price)
        profit += purchase_sale.profit
        qty += purchase_sale.qty
        purchase_price += purchase_sale.price

    return BitcoinSale(qty, purchase_price, profit)

  def __del__(self):
    self.conn.commit()
    self.conn.close()

reset_data = True
starting_funds = 1000.00
bitcoin_value = 100.00

wallet = BitWallet(starting_funds, reset_data)
wallet.print_status(bitcoin_value)

wallet.purchase_bitcoin(1.0, bitcoin_value)
wallet.print_status(bitcoin_value)

bitcoin_value = 200.00
wallet.purchase_bitcoin(1.0, bitcoin_value)
wallet.print_status(bitcoin_value)

bitcoin_value = 300.00
purchase_sale = wallet.sell_bitcoin_by_target_price(150.00, bitcoin_value)
print "================================================================"
print "Sold {qty} BTC @ ${bitcoin_value} purchased for ${purchase_price} for profit of: ${profit}".format(bitcoin_value=bitcoin_value, purchase_price=purchase_sale.price, qty = purchase_sale.qty, profit=purchase_sale.profit)
print "================================================================\n"
wallet.print_status(bitcoin_value)
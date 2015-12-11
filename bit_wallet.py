import time
import sqlite3
import os

class BitWallet:
  DROP_TABLE_QUERY = "DROP TABLE investments;"
  CREATE_TABLE_QUERY = "CREATE TABLE investments(id INTEGER PRIMARY KEY AUTOINCREMENT, qty FLOAT, price FLOAT, standing FLOAT, purchase_time  INTEGER);"

  def __init__(self, dollars = 0, bitcoin_records = []):
    self.conn = sqlite3.connect( os.getcwd() + os.path.sep + 'investments.sqlite')
    self.c = self.conn.cursor()
    self.dollars = dollars
    self.bitcoin_records = bitcoin_records

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
    self.c.execute("SELECT * FROM investments")
    self.bitcoin_records = self.c.fetchall()
    print "\n\n All Records: " + str(self.bitcoin_records)

  def add_dollars(self, dollars):
    self.dollars += dollars
    print "\n$" + str(dollars) + " added\n\n"

  def purchase_bitcoin(self, bitcoin_qty, bitcoin_price):    
    investment_standing = bitcoin_qty * bitcoin_price * -1
    self.dollars += investment_standing
    ptime = int(time.time())
    self.bitcoin_records.append( [bitcoin_qty, bitcoin_price, investment_standing, ptime] )
    query = "INSERT INTO investments (qty, price, standing, purchase_time) VALUES ('{bitcoin_qty}', '{bitcoin_price}', '{investment_standing}', '{ptime}');"\
        .format(bitcoin_qty=bitcoin_qty, bitcoin_price=bitcoin_price, investment_standing=investment_standing, ptime = ptime)
    try:
      self.c.execute(query)
      self.conn.commit()      
      print "\nPurchased " + str(bitcoin_qty) + " bitcoin @ " + str(bitcoin_price) +"\n"
      self.query_db()
    except sqlite3.OperationalError as e:
      print "sqlite3 error: " + str(e)  
    

  def convert_bitcoin_by_index(self, index, bitcoin_qty, bitcoin_price):
    for i in self.bitcoin_records:
      if i[0] == index:
        list_record = list(i)
    dollar_amount = bitcoin_qty * bitcoin_price
    self.dollars += dollar_amount    
    list_record[3] += dollar_amount
    list_record[1] -= bitcoin_qty
    print "Selected record: " + str(list_record)
    if list_record[1] == 0:      
      query = "DELETE FROM investments WHERE id='{id}';"\
          .format(id = index)
      print "\n" + query
      try:
        self.c.execute(query)
        self.conn.commit()
        print "Investment removed with a profit of: $" + str(list_record[3])
        self.query_db()             
      except sqlite3.OperationalError as e:
        print "sqlite3 error: " + str(e)     
    #self.bitcoin_records[index] = list_record
    elif list_record[1] > 0:
      query = "UPDATE investments SET qty='{bitcoin_qty}', standing='{investment_standing}' WHERE id='{id}';"\
          .format(bitcoin_qty=list_record[1], investment_standing=list_record[3], id = index)
      #query = "UPDATE investments SET qty=(?), price=(?), standing=(?), purchase_time=(?) WHERE id=(?);"\
      #    (list_record[1],list_record[2],list_record[3],list_record[4],index)   
      print "\n" + query 
      try:
        self.c.execute(query)
        self.conn.commit()
        self.query_db()
        print "\nConverted " + str(bitcoin_qty) + " bitcoin @ " + str(bitcoin_price) + " worth $" + str(dollar_amount) + "\n"      
      except sqlite3.OperationalError as e:
        print "sqlite3 error: " + str(e)     
  
  def investment_finder(self, cur_price, margin):
    index_array = []
    target_price = cur_price * (1-margin)
    print "\nTarget price: " + str(target_price)
    for i in self.bitcoin_records:
      if i[2] <= target_price:
        index_array.append(i)
    return index_array

  def __str__(self):
    return "\nRecords: " + str(self.bitcoin_records) + "\nDollars:" + str(self.dollars)

  def __del__(self):
    self.conn.commit()
    self.conn.close()


wallet = BitWallet(1000.00)
wallet.initialize_db()
wallet.query_db()
wallet.add_dollars(500.00)
wallet.purchase_bitcoin(1.5, 320.00)
print wallet.investment_finder(400, 0.05)
wallet.purchase_bitcoin(0.5, 350.00)
print wallet.investment_finder(390, 0.05)
wallet.convert_bitcoin_by_index(1,0.5,500.00)
wallet.convert_bitcoin_by_index(1,1.0,500.00)
wallet.convert_bitcoin_by_index(2,0.5,500.00)
print(wallet)
import time

class BitWallet:
  def __init__(self, dollars = 0, bitcoin_records = []):
    self.dollars = dollars
    self.bitcoin_records = bitcoin_records

  def add_dollars(self, dollars):
    self.dollars += dollars

  def purchase_bitcoin(self, bitcoin_qty, bitcoin_price):
    dollar_cost = bitcoin_qty * bitcoin_price
    self.dollars -= dollar_cost
    self.bitcoin_records.append( [bitcoin_qty, bitcoin_price, dollar_cost, int(time.time())] )

  def convert_bitcoin_by_index(self, index, bitcoin_pct, bitcoin_price):
    self.dollars += self.bitcoin_records[index][0] * bitcoin_pct * bitcoin_price
    self.bitcoin_records[index][0] = self.bitcoin_records[index][0] - self.bitcoin_records[index][0] * bitcoin_pct;

    if bitcoin_pct == 1.0:
      del self.bitcoin_records[index:index+1]

  def __str__(self):
    return "Records: " + str(self.bitcoin_records) + "\nDollars:" + str(self.dollars)


wallet = BitWallet(1000.00)

wallet.add_dollars(500.00)

wallet.purchase_bitcoin(1.5, 420)

print wallet


wallet.convert_bitcoin_by_index(0,.5,500)
print wallet

wallet.convert_bitcoin_by_index(0,.5,500)
print wallet

wallet.convert_bitcoin_by_index(0,1.0,500)
print wallet
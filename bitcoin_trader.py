import time

class BitcoinTrader(object):
  """Base class for Bitcoin trading behaviors"""
  ACTION_BUY = "buy"
  ACTION_SELL = "sell"
  ACTION_HOLD = "hold"

  MAX_HISTORY = 60

  def __init__(self, historical_data = []):
    self.last_price = 0.0
    self.last_slope = 0.0
    length = len(historical_data)
    if length > 0:
      self.last_price = historical_data[length - 1][1]
      self.last_slope = historical_data[length - 1][2]
      
    self.historical_data = historical_data
    self.prune_history()
  def prune_history(self):
    length = len(self.historical_data)
    if length > self.MAX_HISTORY:
      del self.historical_data[:length - self.MAX_HISTORY]

  def add_bitcoin_data(self, price, slope, timestamp = 0):
    if timestamp == 0:
      timestamp = int(time.time())
    self.historical_data = [(timestamp, price, slope)] + self.historical_data
    self.prune_history()
    self.last_price = price
    self.last_slope = slope
    
  def compute_recommended_action(self):
    return self.ACTION_HOLD

class BullTrader(BitcoinTrader):
  """Recommends buying Bitcoin for USD"""
  def compute_recommended_action(self):
    
    return self.ACTION_BUY

class BearTrader(BitcoinTrader):
  """Recommends selling Bitcoin for USD"""
  def compute_recommended_action(self):
    return self.ACTION_SELL

class ContentTrader(BitcoinTrader):
  """Does not recommending adjusting the portfolio"""
  def compute_recommended_action(self):
    return self.ACTION_HOLD

class HoldUntilDeclineAmt(BitcoinTrader):
  """Holds Bitcoin until it begins to decline"""

  def __init__(self, db_results, decline_amt):
  	super(HoldUntilDeclineAmt, self).__init__(db_results)
  	self.decline_amt = decline_amt

  def compute_recommended_action(self):
    return self.ACTION_HOLD #Fill out this logic based on historical_data

class HoldUntilDeclinePct(BitcoinTrader):
  """Holds Bitcoin until it begins to decline"""

  def __init__(self, db_results, decline_pct):
  	super(HoldUntilDeclinePct, self).__init__(db_results)
  	self.decline_pct = decline_pct

  def compute_recommended_action(self):
    return self.ACTION_HOLD #Fill out this logic based on historical_data

class TraderManager:
  traders = []

  @staticmethod
  def add_trader(trader):
    TraderManager.traders.append(trader)

  @staticmethod
  def add_bitcoin_data(price, timestamp = 0):
    if timestamp == 0:
      timestamp = int(time.time())

    for trader in TraderManager.traders:
      trader.add_bitcoin_data(price, timestamp)

  @staticmethod
  def compute_recommended_actions():
    result = []
    for trader in TraderManager.traders:
      result.append(trader.compute_recommended_action())
    return result

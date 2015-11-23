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
    self.max_price = 0.0
    self.min_price = 999999999.0

    self.historical_data = []

    for item in historical_data:
      price = item[1]
      slope =  item[2]
      timestamp =  item[0]
      self.add_bitcoin_data(price, slope, timestamp)
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

    if self.last_price > self.max_price:
      self.max_price = self.last_price
  
    if self.last_price < self.min_price:
      self.min_price = self.last_price

  def get_range(self):
    return self.max_price - self.min_price

  def is_at_minimum(self, threshold):
    return self.last_price < self.min_price + self.get_range() * threshold

  def is_at_maximum(self, threshold):
    return self.last_price > self.max_price - self.get_range() * threshold

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

class HighLowTrader(BitcoinTrader):
  """Buy low sell high"""

  def __init__(self, db_results, threshold):
    super(HighLowTrader, self).__init__(db_results)
    self.threshold = threshold

  def compute_recommended_action(self):
    recommendation = self.ACTION_HOLD
    reason = "no action"
    new_reason = "Last Price: " + str(self.last_price) + ", Daily Minimum: " + str(self.min_price) + ", Daily Maximum: " + str(self.max_price) + ", Range: " + str(self.get_range()) + ", Threshold: " + str(self.threshold) + ", Min Threshold: " + str(self.min_price + self.threshold * self.get_range()) + ", Max Threshold: " + str(self.max_price - self.threshold * self.get_range())
    
    if self.is_at_minimum(self.threshold):
      recommendation = self.ACTION_BUY
      reason = str(self.last_price) + " < " + str(self.min_price + self.threshold * self.get_range())
    if self.is_at_maximum(self.threshold):
      recommendation = self.ACTION_SELL
      reason = str(self.last_price) + " > " + str(self.max_price - self.threshold * self.get_range())
    return (recommendation, reason) #Fill out this logic based on historical_data

class TraderManager:
  traders = []

  @staticmethod
  def add_trader(trader):
    TraderManager.traders.append(trader)

  @staticmethod
  def add_bitcoin_data(price, slope, timestamp = 0):
    if timestamp == 0:
      timestamp = int(time.time())

    for trader in TraderManager.traders:
      trader.add_bitcoin_data(price, slope, timestamp)

  @staticmethod
  def compute_recommended_actions():
    result = []
    for trader in TraderManager.traders:
      result.append(trader.compute_recommended_action())
    return result

import time

class BitcoinTrader:
  """Base class for Bitcoin trading behaviors"""
  ACTION_BUY = "buy"
  ACTION_SELL = "sell"
  ACTION_HOLD = "hold"

  MAX_HISTORY = 2

  def __init__(self, historical_data = []):
    self.historical_data = historical_data
    self.prune_history()

  def prune_history(self):
    length = len(self.historical_data)
    if length > self.MAX_HISTORY:
      del self.historical_data[:length - self.MAX_HISTORY]

  def add_bitcoin_data(self, price, timestamp = 0):
    if timestamp == 0:
      timestamp = int(time.time())
    self.historical_data.append( (timestamp, price) )
    self.prune_history()
    
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

class HoldUntilDecline(BitcoinTrader):
  """Does not recommending adjusting the portfolio"""
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

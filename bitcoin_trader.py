import time
from utils import *
from event_manager import *

class BitcoinTrader(object):
  """Base class for Bitcoin trading behaviors"""
  ACTION_BUY = "buy"
  ACTION_SELL = "sell"
  ACTION_HOLD = "hold"

  MAX_HISTORY = 60

  def __init__(self, wallet, historical_data = []):
    self.last_price = 0.0
    self.last_slope = 0.0
    self.max_price = 0.0
    self.min_price = 999999999.0
    self.wallet = wallet
    self.target_profit_margin = 0.10

    self.historical_data = []

    for item in historical_data:
      price = item[1]
      slope =  item[2]
      timestamp =  item[0]
      self.add_bitcoin_data(price, slope, timestamp)
    self.prune_history()
    print "subscribing to price event"
    EventManager.add_subscription("price_change", [], self.handle_price_event)

  def prune_history(self):
    length = len(self.historical_data)
    if length > self.MAX_HISTORY:
      del self.historical_data[:length - self.MAX_HISTORY]

  def handle_buy_recommendation(self, event):
    investment_rate = 0.5
    investable_cash = self.wallet.dollars * investment_rate
    bitcoin_qty = investable_cash / event.metadata['price']
    self.wallet.purchase_bitcoin(bitcoin_qty, event.metadata['price'])
    
  def handle_sell_recommendation(self, event):
    self.wallet.sell_bitcoin_by_target_pct(self.target_profit_margin, event.metadata['price'])

  def handle_price_event(self, event):
    self.add_bitcoin_data(event.metadata['price'], event.metadata['slope'], event.metadata['time'])
    recommendation = self.compute_recommended_action()
    actions = { self.ACTION_BUY : self.handle_buy_recommendation,
                self.ACTION_SELL : self.handle_sell_recommendation }

    if(recommendation[0] in actions):
      actions[recommendation[0]](event)

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

  def __init__(self, wallet, db_results, decline_amt):
    super(HoldUntilDeclineAmt, self).__init__(wallet, db_results)
    self.decline_amt = decline_amt

  def compute_recommended_action(self):
    return self.ACTION_HOLD #Fill out this logic based on historical_data

class HoldUntilDeclinePct(BitcoinTrader):
  """Holds Bitcoin until it begins to decline"""

  def __init__(self, wallet, db_results, decline_pct):
    super(HoldUntilDeclinePct, self).__init__(wallet, db_results)
    self.decline_pct = decline_pct

  def compute_recommended_action(self):
    return self.ACTION_HOLD #Fill out this logic based on historical_data

class HighLowTrader(BitcoinTrader):
  """Buy low sell high"""

  def __init__(self, wallet, db_results, threshold, min_earnings):
    super(HighLowTrader, self).__init__(wallet, db_results)
    self.threshold = threshold
    self.min_earnings = min_earnings

  def compute_recommended_action(self):
    recommendation = self.ACTION_HOLD
    reason = "no action"
    new_reason = "Last Price: " + str(self.last_price) + ", Daily Minimum: " + str(self.min_price) + ", Daily Maximum: " + str(self.max_price) + ", Range: " + str(self.get_range()) + ", Threshold: " + str(self.threshold) + ", Min Threshold: " + str(self.min_price + self.threshold * self.get_range()) + ", Max Threshold: " + str(self.max_price - self.threshold * self.get_range())
    
    if (self.max_price - self.min_price) >= self.min_earnings:
      if self.is_at_minimum(self.threshold):
        recommendation = self.ACTION_BUY
        reason = str(self.last_price) + " < " + str(self.min_price + self.threshold * self.get_range())
      if self.is_at_maximum(self.threshold):
        recommendation = self.ACTION_SELL
        reason = str(self.last_price) + " > " + str(self.max_price - self.threshold * self.get_range())
    reason = reason + "(" + format_dollars(self.wallet.dollars) + ", " + format_dollars(self.wallet.get_bitcoin_value(self.last_price)) + ")"
    return (recommendation, reason) #Fill out this logic based on historical_data

class TraderManager:
  traders = []

  @staticmethod
  def add_trader(trader):
    TraderManager.traders.append(trader)

  @staticmethod
  def compute_recommended_actions():
    result = []
    for trader in TraderManager.traders:
      result.append(trader.compute_recommended_action())
    return result

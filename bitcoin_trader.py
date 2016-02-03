import time
import utils
from utils import *
from event_manager import *

class BitcoinTrader(object):
  """Base class for Bitcoin trading behaviors"""
  ACTION_BUY = "buy"
  ACTION_SELL = "sell"
  ACTION_HOLD = "hold"

  TREND_INCREASING = "increasing"
  TREND_DECREASING = "decreasing"
  TREND_FLAT = "flat"

  MAX_HISTORY = 60

  def __init__(self, wallet, historical_data = []):
    self.last_price = 0.0
    self.last_slope = 0.0
    self.trend = self.TREND_FLAT
    self.trend_count = 0
    self.max_price = 0.0
    self.min_price = 999999999.0
    self.wallet = wallet
    self.target_profit_margin = 0.03

    self.historical_data = []

    for item in historical_data:
      price = item[1]
      slope =  item[2]
      timestamp =  item[0]
      self.add_bitcoin_data(price, slope, timestamp)
    self.prune_history()

  def register_listeners(self):
    EventManager.add_subscription("price_change", [], self.handle_price_event)
    EventManager.add_subscription("price_change", [self.ACTION_BUY], self.handle_buy_recommendation)
    EventManager.add_subscription("price_change", [self.ACTION_SELL], self.handle_sell_recommendation)

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
    self.update_trend(event)

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

  def get_trend_from_slope(self, slope):
    trend = self.TREND_FLAT
    if(not approximately_zero(slope)):
      trend = self.TREND_INCREASING if slope > 0.0 else self.TREND_DECREASING
    return trend

  def get_computed_trend(self, slope):
    trend = self.get_trend_from_slope(slope)
    if(not self.trend == trend and not self.trend == self.TREND_FLAT):
      trend = self.TREND_FLAT
    return trend

  def handle_trend_disruption(self, old_trend, new_trend):
    pass

  def update_trend(self, event):
    new_trend = self.get_computed_trend(event.metadata['slope'])
    if (new_trend == self.trend):
      self.trend_count += 1
    else:
      self.handle_trend_disruption(new_trend)
      self.trend_count = 0
    self.trend = new_trend
    self.last_slope = event.metadata['slope'] 

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
    reason = reason + "(dollars: " + format_dollars(self.wallet.dollars) + ", bitcoin value: " + format_dollars(self.wallet.get_bitcoin_value(self.last_price)) +  ", bitcoin qty: " + format_btc(self.wallet.get_bitcoin_qty()) + ")"
    return (recommendation, reason) #Fill out this logic based on historical_data

class StopLossTrader(BitcoinTrader):
  """Buy when stable, sell when market dips"""

  def __init__(self, wallet, db_results, threshold, trend_count_threshold):
    super(StopLossTrader, self).__init__(wallet, db_results)    
    self.threshold = threshold
    self.trend_count_threshold = trend_count_threshold
    self.next_recommendation = self.ACTION_HOLD
    self.has_purchased_this_trend = False
    self.has_sold_this_trend = False

  def handle_trend_disruption(self, new_trend):
    self.has_purchased_this_trend = False
    self.has_sold_this_trend = False

  def is_trend_stable(self):
    return (self.trend_count > self.trend_count_threshold)

  def compute_recommended_action(self):   
    recommendation = self.ACTION_HOLD
    reason = "no action"
    new_reason = "Last Price: " + str(self.last_price) + ", Daily Minimum: " + str(self.min_price) + ", Daily Maximum: " + str(self.max_price) + ", Range: " + str(self.get_range()) + ", Threshold: " + str(self.threshold) + ", Min Threshold: " + str(self.min_price + self.threshold * self.get_range()) + ", Max Threshold: " + str(self.max_price - self.threshold * self.get_range())
    is_stable = self.is_trend_stable()
    if(is_stable):
      if(self.trend == self.TREND_DECREASING and not self.has_sold_this_trend):
        reason = "stop loss"
        recommendation = self.ACTION_SELL
        self.has_sold_this_trend = True
      elif(self.trend == self.TREND_INCREASING and not self.has_purchased_this_trend):
        reason = "base buy"
        recommendation = self.ACTION_BUY
        self.has_purchased_this_trend = True
    reason = reason + ", Stable: " + str(is_stable) + ", Trend: " + str(self.trend) + ", Trend Count: " + str(self.trend_count) + " (dollars: " + format_dollars(self.wallet.dollars) + ", bitcoin value: " + format_dollars(self.wallet.get_bitcoin_value(self.last_price)) +  ", bitcoin qty: " + format_btc(self.wallet.get_bitcoin_qty()) + ")"
    return (recommendation, reason) #Fill out this logic based on historical_data 
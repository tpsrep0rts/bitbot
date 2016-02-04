import time
import utils
from utils import *
from event_manager import *

class BitRecommendation(object):
  def __init__(self, recommendation, reason=None, data = {}, header = []):
    self.recommendation = recommendation
    self.reason = reason
    base_data = {
      "recommendation":recommendation,
      "reason":reason
    }
    self.data = merge_dictionaries(base_data, data)
    self.header = ["recommendation", "reason"] + header

  def format_column(self, column):
    return "{:>10}".format(str(column))

  def format_array(self, data):
    result_data = []
    for column in data:
      result_data.append(self.format_column(column))
    return self.format_row(result_data)

  def get_header(self):
    return self.format_array(self.header)

  def format_row(self, data):
    return "\t".join(data)

  def get_mapped_columns(self):
    result_data = []
    for key in self.header:
      result_data.append(self.format_column(self.data[key]))
    return result_data

  def __str__(self):
    return self.format_row(self.get_mapped_columns())

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
    self.data = {}
    self.historical_data = []
    self.recommendation = self.ACTION_HOLD
    self.reason = "no reason"

    for item in historical_data:
      price = item[1]
      slope =  item[2]
      timestamp =  item[0]
      self.add_bitcoin_data(price, slope, timestamp)
    self.prune_history()

  def get_base_data(self):
    return {
      "last_price":self.last_price,
      "dollars":format_dollars(self.wallet.dollars),
      "bitcoin_value":format_dollars(self.wallet.get_bitcoin_value(self.last_price)),
      "bitcoin_qty":format_btc(self.wallet.get_bitcoin_qty()),
      "daily_min":self.min_price,
      "daily_max":self.max_price,
      "range":self.get_range(),
      "min_threshold":self.min_price + self.threshold * self.get_range(),
      "max_threshold":self.max_price - self.threshold * self.get_range()
    }

  def get_data(self):
    return self.get_base_data()

  def get_recommendation(self):
    self.compute_recommended_action()
    data = merge_dictionaries(self.get_base_data(), self.get_data())
    return BitRecommendation(self.recommendation, self.reason, data, self.get_header())

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

  def get_header(self):
    pass

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
    self.recommendation = self.ACTION_HOLD
    self.reason = "no reason"

class BullTrader(BitcoinTrader):
  """Recommends buying Bitcoin for USD"""
  def compute_recommended_action(self):
    self.recommendation = self.ACTION_BUY
    self.reason = "no reason"

class BearTrader(BitcoinTrader):
  """Recommends selling Bitcoin for USD"""
  def compute_recommended_action(self):
    self.recommendation = self.ACTION_SELL
    self.reason = "no reason"

class ContentTrader(BitcoinTrader):
  """Does not recommending adjusting the portfolio"""
  def compute_recommended_action(self):
    self.recommendation = self.ACTION_HOLD
    self.reason = "no reason"

class HoldUntilDeclineAmt(BitcoinTrader):
  """Holds Bitcoin until it begins to decline"""

  def __init__(self, wallet, db_results, decline_amt):
    super(HoldUntilDeclineAmt, self).__init__(wallet, db_results)
    self.decline_amt = decline_amt

  def compute_recommended_action(self):
    self.recommendation = self.ACTION_HOLD
    self.reason = "no reason"

class HoldUntilDeclinePct(BitcoinTrader):
  """Holds Bitcoin until it begins to decline"""

  def __init__(self, wallet, db_results, decline_pct):
    super(HoldUntilDeclinePct, self).__init__(wallet, db_results)
    self.decline_pct = decline_pct

  def compute_recommended_action(self):
    self.recommendation = self.ACTION_HOLD

class HighLowTrader(BitcoinTrader):
  """Buy low sell high"""

  
  def __init__(self, wallet, db_results, threshold, min_earnings):
    super(HighLowTrader, self).__init__(wallet, db_results)
    self.threshold = threshold
    self.min_earnings = min_earnings
  
  def get_data(self):
    return {
      "min_earnings":self.min_earnings,
      "threshold":self.threshold
    }

  def compute_recommended_action(self):
    self.recommendation = self.ACTION_HOLD
    self.reason = "no action"

    if (self.max_price - self.min_price) >= self.min_earnings:
      if self.is_at_minimum(self.threshold):
        self.recommendation = self.ACTION_BUY
        self.reason = str(self.last_price) + " < " + str(self.min_price + self.threshold * self.get_range())
      if self.is_at_maximum(self.threshold):
        self.recommendation = self.ACTION_SELL
        self.reason = str(self.last_price) + " > " + str(self.max_price - self.threshold * self.get_range())

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

  def get_header(self):
    return ["stable",  "dollars", "bitcoin_value", "bitcoin_qty"]

  def get_data(self):
    return {
      "trend_count_threshold":self.trend_count_threshold,
      "threshold":self.threshold,
      "stable":self.is_trend_stable()
    }

  def compute_recommended_action(self):   
    self.recommendation = self.ACTION_HOLD
    self.reason = "no action"
    if(self.is_trend_stable()):
      if(self.trend == self.TREND_DECREASING and not self.has_sold_this_trend):
        self.reason = "stop loss"
        self.recommendation = self.ACTION_SELL
        self.has_sold_this_trend = True
      elif(self.trend == self.TREND_INCREASING and not self.has_purchased_this_trend):
        self.reason = "base buy"
        self.recommendation = self.ACTION_BUY
        self.has_purchased_this_trend = True
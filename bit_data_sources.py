
import warnings, random
import requests,json

class BitDataSource(object):
  def __init__(self, should_persist=False, query_rate=1.0):
    self.should_persist = should_persist
    self.query_rate     = query_rate

  def query(self):
    return 0.0

class BitstampDataSource(BitDataSource):
  BITSTAMP_URL = 'http://www.bitstamp.net/api/ticker/'

  def __init__(self):
    super(BitstampDataSource, self).__init__(True, 5.0)

  def query(self):
    with warnings.catch_warnings():
      warnings.simplefilter("ignore")
      r = requests.get(self.BITSTAMP_URL)
    priceFloat = float(json.loads(r.text)['last'])
    return priceFloat

class LinearDataSource(BitDataSource):
  @staticmethod
  def from_config(config):
    start_price = config.getfloat("LinearDataSource", "startprice")
    growth_rate = config.getfloat("LinearDataSource", "growthrate")
    query_rate = config.getint("LinearDataSource", "queryrate")
    return LinearDataSource(start_price, growth_rate, query_rate)

  def __init__(self, start_price = 420.00, growth_rate = 1.0, query_rate=1.0):
    self.last_price   = start_price
    self.growth_rate  = growth_rate
    super(LinearDataSource, self).__init__(False, query_rate)

  def query(self):
    self.last_price = max(0.0, self.last_price + self.growth_rate)
    return self.last_price

class BounceDataSource(BitDataSource):
  @staticmethod
  def from_config(config):
    start_price = config.getfloat("BounceDataSource", "startprice")
    min_price = config.getfloat("BounceDataSource", "minprice")
    max_price = config.getfloat("BounceDataSource", "maxprice")
    growth_rate = config.getfloat("BounceDataSource", "growthrate")
    query_rate = config.getint("BounceDataSource", "queryrate")
    return BounceDataSource(start_price, min_price, max_price, growth_rate, query_rate)

  def __init__(self, start_price = 420.00, min_price= 300.00, max_price=500.00, growth_rate = 1.0, query_rate=1.0):
    self.last_price   = start_price
    self.growth_rate  = growth_rate
    self.min_price    = min_price
    self.max_price    = max_price

    self.current_growth_rate = growth_rate
    super(BounceDataSource, self).__init__(False, query_rate)

  def query(self):
    self.last_price += self.current_growth_rate
    if(self.last_price > self.max_price):
      self.last_price = self.max_price
      self.current_growth_rate *= -1
    elif(self.last_price < self.min_price):
      self.last_price = self.min_price
      self.current_growth_rate *= -1
    return self.last_price


class RandomBounceDataSource(BounceDataSource):
  @staticmethod
  def from_config(config):
    random_threshold = config.getfloat("RandomBounceDataSource", "randomthreshold")
    start_price = config.getfloat("RandomBounceDataSource", "startprice")
    min_price = config.getfloat("RandomBounceDataSource", "minprice")
    max_price = config.getfloat("RandomBounceDataSource", "maxprice")
    growth_rate = config.getfloat("RandomBounceDataSource", "growthrate")
    query_rate = config.getint("RandomBounceDataSource", "queryrate")
    return RandomBounceDataSource(random_threshold, start_price, min_price, max_price, growth_rate, query_rate)

  def __init__(self, random_threshold = 0.2, start_price = 420.00, min_price= 300.00, max_price=500.00, growth_rate = 1.0, query_rate=1.0):
    self.random_threshold = random_threshold
    super(RandomBounceDataSource, self).__init__(start_price, min_price, max_price, growth_rate, query_rate)

  def query(self):
    if(random.random() < self.random_threshold):
      self.current_growth_rate *= -1
    return super(RandomBounceDataSource, self).query()

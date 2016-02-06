import time
import utils
from utils import *
from event_manager import *

class BitRecommendation(object):
  COLUMN_RECOMMENDATION = "recommendation"
  COLUMN_REASON         = "reason"

  def __init__(self, recommendation, reason=None, data = {}, header = []):
    self.recommendation = recommendation
    self.reason         = reason
    base_data           = {
      self.COLUMN_RECOMMENDATION  : recommendation,
      self.COLUMN_REASON          : reason
    }
    self.data           = merge_dictionaries(base_data, data)
    self.header         = [self.COLUMN_RECOMMENDATION, self.COLUMN_REASON] + header

  def format_column(self, column):
    return "{:>10}".format(str(column))

  def format_array(self, data):
    result_data         = []
    for column in data:
      result_data.append(self.format_column(column))
    return self.format_row(result_data)

  def get_header(self):
    return self.format_array(self.header)

  def format_row(self, data):
    return "\t".join(data)

  def get_mapped_columns(self):
    result_data           = []
    for key in self.header:
      result_data.append(self.format_column(self.data[key]))
    return result_data

  def __str__(self):
    return self.format_row(self.get_mapped_columns())
import ConfigParser
import os, sys

class BitConfig:
  """Reads BitBot configuration"""

  CONFIG_FILE = "bitbot.cfg"

  def __init__(self):
    self.config = ConfigParser.ConfigParser()
    self.config.read( os.getcwd() + os.path.sep + self.CONFIG_FILE)

  def get(self, section_name, option_name):
    result = "undefined"
    try:
      result = self.config.get(section_name, option_name)
    except: # catch *all* exceptions
      e = sys.exc_info()[0]
      print "[" + section_name + ", " + option_name +"]: " + str(e)
    return result

  def getfloat(self, section_name, option_name):
    result = 0.0
    try:
      result = self.config.getfloat(section_name, option_name)
    except: # catch *all* exceptions
      e = sys.exc_info()[0]
      print "[" + section_name + ", " + option_name +"]: " + str(e)
    return result

  def getboolean(self, section_name, option_name):
    result = False
    try:
      result = self.config.getboolean(section_name, option_name)
    except: # catch *all* exceptions
      e = sys.exc_info()[0]
      print "[" + section_name + ", " + option_name +"]: " + str(e)
    return result

  def getint(self, section_name, option_name):
    result = -1
    try:
      result = self.config.getint(section_name, option_name)
    except: # catch *all* exceptions
      e = sys.exc_info()[0]
      print "[" + section_name + ", " + option_name +"]: " + str(e)
    return result
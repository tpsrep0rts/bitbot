from contextlib import contextmanager
import sys, os
import sqlite3

ZERO = 0.000001
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def connect_to_database(db_file_name):
   return sqlite3.connect( os.getcwd() + os.path.sep + db_file_name)

def close_database(conn):
    conn.commit()
    conn.close()

def format_dollars(dollars):
  return "${:.2f}".format(dollars)

def format_btc(btc):
  return  "{:.5f}".format(btc)

def format_slope(slope):
  return  "{:>10.5f}".format(slope)

def approximately_zero(value):
  return value > -ZERO and value < ZERO

def merge_dictionaries(dict1, dict2):
  result = dict1.copy()
  for index, key in enumerate(dict2):
    result[key] = dict2[key]
  return result
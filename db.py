import os, sys
import sqlite3
import utils
class DB(object):
  BITCOIN_DB = 'bitcoin.sqlite'
  WALLET_DB = 'investments.sqlite'

  conn = {}
  c = {}
  initialized = {}

  @staticmethod
  def require_initialized(db):
    if(not db in DB.initialized):
      DB.initialized[db] = True
      DB.init(db)

  @staticmethod
  def init(db):
    DB.conn[db] = utils.connect_to_database(db)
    DB.c[db] = DB.conn[db].cursor()

  @staticmethod
  def query(db, query):
    DB.require_initialized(db)
    DB.execute(db, query)
    return DB.c[db].fetchall()

  @staticmethod
  def execute(db, query):
    DB.require_initialized(db)
    DB.c[db].execute(query)
    DB.conn[db].commit()

  @staticmethod
  def insert(db, query):
    DB.require_initialized(db)
    DB.execute(db, query)
    #return insert id

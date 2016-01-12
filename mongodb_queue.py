#
# This is a class which implements 
# a capped collection which is used 
# as a queue
#
#
import pymongo
from pymongo import MongoClient

class Mongo_Queue():

   def __init__(self, db, name , size, number ):
      self.db = db
      self.capped_collection  =  db.create_collection( name,capped=True,size=size_in_bytes,max=number,autoIndexId=False)

   def append_document( self, document ):
     self.capped_collection.insert( document, manipulate=False)
   
   def pop_document( self ):
     pass

   def get_document_number( self ):
     return self.capped_collection.count()

   
   def get_index( self, index ):
     pass


if __name__ == "__main__":
  client = MongoClient()
  db = client.test_database
  x = Mongo_Queue( db,"queue_1",100000,25)
  print x.get_document_number()
  x.append_document( "[1,2,3,4,5]")
  x.append_document( "[6,7,8,9,10]")
  print x.get_document_number()
  # create document
  # print out document number
  # apppend document
  # append document
  # print out document number
  # test out index
  # pop document
  # pop document
  # print out document

#!/usr/bin/env python
import pika
import json
import base64
import time
import os
import redis
import logging

global connection
from web_access import *

class Remote_Interface_server():

   def __init__(self,redis ):
        self.redis                 = redis
        self.cmds                  = {}
        self.cmds["GET_WEB_PAGE"]  = self.get_web_page
        self.cmds["POST_WEB_PAGE"] = self.post_web_page
        self.cmds["PING"]          = self.ping

   def get_web_page( self, command_data ):
       
       results = web_client.get_path( command_data["path"] )
       return results

   def post_web_page( self, command_data ):
       results = web_client.post_path( path = command_data["path"], payload = command_data["data"] )
       
       return results

   def ping( self, command_data ):
      pass

          


   def process_commands( self, command_data ):
       print "command ",command_data["command"]
       try:
           object_data = {}
           command = command_data["command"]
           if self.cmds.has_key( command ):
               result = self.cmds[command]( command_data)
               return  json.dumps( result )
           else:
              object_data = {}
              object_data["reply"] = "BAD_COMMAND"
              return json.dumps(object_data)
      
       except:
           print "exception"
           object_data = {}
           object_data["reply"] = "BAD_COMMAND"
           object_data["results"] = None
           return json.dumps(object_data)                  

rt = None
def on_request(ch, method, props, body):
    global rt
    
    try:
       input_data   = json.loads( base64.b64decode(body))
      
       output_data  = rt.process_commands( input_data )
       
    except:
       print "exception"
       output_data = {}
       output_data["reply"] = "BAD_COMMAND"
       object_data["results"] = None
       output_data = json.dumps(output_data)

    response     = base64.b64encode(  output_data )
    
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),
                     body= str(response) )
    ch.basic_ack(delivery_tag = method.delivery_tag)

  
if __name__ == "__main__":
   redis_startup       = redis.StrictRedis( host = "127.0.0.1", port=6379, db = 1 )

   user_name = redis_startup.hget("gateway", "user_name" )
   password  = redis_startup.hget("gateway", "password"  )
   vhost     = redis_startup.hget("gateway", "vhost"     )
   queue     = redis_startup.hget("gateway", "queue"     )
   port      = int(redis_startup.hget("gateway", "port"  ))
   server    = redis_startup.hget("gateway", "server"    )

   web_client = Web_Client_Interface( )
   logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.CRITICAL)
   redis               = redis.StrictRedis( host = 'localhost', port=6379, db = 0 )
   
   rt = Remote_Interface_server(redis )
   credentials = pika.PlainCredentials( user_name, password )
   parameters = pika.ConnectionParameters(server,
                                           port,  #ssl port
                                           vhost,
                                           credentials,
                                           ssl = True ,
                                          heartbeat_interval=20 )
   connection = pika.BlockingConnection(parameters)
   channel = connection.channel()
   #connection.socket.settimeout(10000)
   channel.queue_delete(queue=queue)
   channel.queue_declare(queue=queue)
   channel.basic_qos(prefetch_count=1)
   channel.basic_consume(on_request, queue=queue)
   print " [x] Awaiting RPC requests"
   channel.start_consuming()

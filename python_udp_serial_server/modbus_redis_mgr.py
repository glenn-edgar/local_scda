import struct
import redis
import json


class ModbusRedisServer():
   def __init__(self, message_handler ):
       self.redis            = redis.StrictRedis( host = "127.0.0.1", port=6379, db = 0 )
       self.message_handler = message_handler
       self.actions              = {}
       self.actions["counter"]   = self.counter_functions
       self.actions["ping"]      = self.ping_functions


   def counter_functions( self, parameters ):
      sub_action       = parameters["sub_action"]
      sub_parameter    = parameters["sub_parameter"]
      register_actions = {"clear_all_counters": self.clear_all_counters,
                          "get_all_counters": self.get_all_counters,
                          "clear_counter_list": self.clear_counter_list }
      return register_actions[ sub_action ](sub_parameter)
		    
                          
   def clear_counter_list( self , parameters ):
       for i in parameters:
          self.message_handler.clear_counter( i )
       return None
   
   def get_all_counters( self, parameters = None ):
        return self.message_handler.get_counters()
        

   def clear_all_counters( self,parameters = None ):
        self.message_handler.clear_all_counters()
        return None

   def ping_functions( self, parameters ):
      
      sub_action    = parameters["sub_action"]
      sub_parameters = parameters["sub_parameter"]
      print "ping functions",sub_action,sub_parameters
      register_actions = {"ping_device":        self.ping_device_a,
                          "ping_all_devices":   self.ping_all_devices_a }

      return register_actions[ sub_action ](sub_parameters)    

              
   def ping_device_a( self, parameters  ):
        return self.message_handler.ping_devices(parameters)
        

   def ping_all_devices_a( self,parameters = None ):
        return self.message_handler.ping_all_devices()
      

   def process_msg( self, address, msg, counter  ):
       
       #try:
           
           function_code  = ord(msg[1])
           json_string    = msg[2:-2]
           
           
	   msg_list = []
	   msg_list.append(msg[0:2])
           json_object = json.loads(json_string)
           
           result = json.dumps(None)
	   if function_code == 254:
              temp_dict = {}
              keys = json_object
           else:
              keys = json_object.keys()
           for i in keys:
               if function_code == 255:
                   self.redis.set( i, json_object[i] )
               if function_code == 254:
		   temp_dict[i] = self.redis.get(i)
           if function_code == 254:
                result = json.dumps(temp_dict)
                
	   
           if function_code == 253:
               action     = json_object["action"]
               parameters = json_object["parameters"]
              
               if self.actions.has_key( action ):
                   result = json.dumps( self.actions[action](parameters) ) 
                   print "result",result
               

           msg_list.append(result)

	   master_string = "".join(msg_list)
	   
	   master_string = master_string +self._calculateCrcString(master_string)
           return master_string
           
       #except:
        #   pass
          

   def _calculateCrcString(self,inputstring):
       """Calculate CRC-16 for Modbus.
          Args:
             inputstring (str): An arbitrary-length message (without the CRC).
          Returns:
             A two-byte CRC string, where the least significant byte is first.
          Algorithm from the document 'MODBUS over serial line specification and implementation guide V1.02'.
       """
 

       # Constant for MODBUS CRC-16
       POLY = 0xA001

       # Preload a 16-bit register with ones
       register = 0xFFFF

       for character in inputstring:

           # XOR with each character
           register = register ^ ord(character)

           # Rightshift 8 times, and XOR with polynom if carry overflows
           for i in range(8):
               carrybit = register & 1
               register = register >> 1
               
    

               if carrybit == 1:
                register = register ^ POLY
       
       return struct.pack('<H', register)



if __name__ == "__main__":          

   server = ModbusRedisServer(None)
   msg_list = []
   msg_list.append([chr(23),chr(255)])
   msg_list.append( json.dumps({ "test_1":21,"test_2":22 }))
   msg_string = "".join(msg_list[0])
   msg_string = msg_string + msg_list[1] +"dc"

   return_string = server.process_msg(msg_string)
   print "return string",return_string
   msg_list = []
   msg_list.append([chr(23),chr(254)])
   msg_list[0] = "".join(msg_list[0])
   msg_list.append( json.dumps( [ "test_1","test_2" ]))
   msg_list.append("dc")
   msg_string = "".join(msg_list)

   return_string = server.process_msg(msg_string)
   print "return string",return_string[2:-2]

   
    

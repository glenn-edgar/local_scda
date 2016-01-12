#
#
# Stand Alone Modbus Program
#
#
#
#
import time
from   myModbus_udp import *


class ModbusUDPDeviceClient():
   def __init__( self, remotes,address ):
       self.instrument = Instrument_UDP()  # 10 is instrument address
       self.remotes          = remotes
       self.instrument.debug = None
       self.instrument.set_ip(address)
    
   def read_bit(self, remote , registeraddress ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_bit( registeraddress )
      
   def write_bit(self, remote, registeraddress, value ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       self.instrument.write_bit( registeraddress, value)
        
   def write_registers(self,remote,starting_register,data_list ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.write_registers( starting_register,data_list )

   def read_registers( self, remote, starting_register, number ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_registers( starting_register,number )
  

   def read_float(self, remote , registeraddress ):
       device = self.remotes[remote] 
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_float( registeraddress ) 

   def write_float( self, remote, registeraddess,value ):
       device = self.remotes[remote]    
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.write_float( registeraddress,address ) 

   def read_long(self, remote, registeraddress ):
       device = self.remotes[remote] 
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_long( registeraddress ) 

   def write_long( self, remote, registeraddess,value ): 
       device = self.remotes[remote]   
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.write_long( registeraddress,address ) 

   # string length is 32 
   def read_string(self,remote, registeraddress ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_string( registeraddress )
 
   # string length is 32
   def write_string(self,remote,registeraddress, textstring):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.write_string(registeraddress, textstring )
   

   def redis_write( self,  server_ip, json_data ):
       self.instrument.set_ip( server_ip )
       self.instrument.address = device["address"]
       return self.instrument.redis_communicate( 255,255, json_data )

   def redis_read( self,  server_ip, json_data):
       self.instrument.set_ip( server_ip )
       self.instrument.address = device["address"]
       return self.instrument.redis_communicate( 255,254, json_data)

   def ping_device( self, server_ip, address_list ):
       self.instrument.set_ip( server_ip )
       json_data = {"action":"ping"   ,"parameters":{ "sub_action":"ping_device"   , "sub_parameter":address_list   } }
       return self.instrument.redis_communicate( 255,253, json_data)

   def ping_all_devices( self, server_ip ):
       self.instrument.set_ip( server_ip )
       json_data = {"action":"ping"  ,"parameters":{ "sub_action":"ping_all_devices"    , "sub_parameter": None  } }
       return self.instrument.redis_communicate( 255,253, json_data)

   def clear_all_counters( self , server_ip):
       self.instrument.set_ip( server_ip )
       json_data = {"action":"counter"   ,"parameters":{ "sub_action":"clear_all_counters"   , "sub_parameter":None   } }
       return self.instrument.redis_communicate(255,253, json_data)

   def get_all_counters( self, server_ip ):
       self.instrument.set_ip( server_ip )
       json_data = {"action":"counter"   ,"parameters":{ "sub_action": "get_all_counters" , "sub_parameter":None   } }
       return self.instrument.redis_communicate(255,253, json_data)

   def clear_counter_list( self, server_ip, address_list ):
       self.instrument.set_ip( server_ip )
       json_data = {"action":"counter"   ,"parameters":{ "sub_action":"clear_counter_list"   , "sub_parameter":address_list   } }
       return self.instrument.redis_communicate( 255,253, json_data)




class Modbus_Device_RTU( ModbusUDPDeviceClient ):

   def __init__(self, remotes,address):
          ModbusUDPDeviceClient.__init__(self,remotes,address)

   def special_command(self,remote, registeraddress, values):
       device = self.remotes[remote] 
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.special_command(registeraddress, values)

   def read_eeprom_registers_byte( self, remote, starting_register,number):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_eeprom_registers( starting_register, number )

   def write_eeprom_registers_byte( self, remote, starting_address, data_list ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.write_eeprom_registes( starting_address, data_list )

   def  read_fifo( self, remote, queue, max_number ):
       device = self.remotes[remote]
       self.instrument.set_ip(device["UDP"])
       self.instrument.address = device["address"]
       return self.instrument.read_fifo( queue, max_number )

   def  read_eeprom_registers( self,remote, queue, max_number ):
        device = self.remotes[remote]
        temp = self.read_eeprom_registers_byte( device,queue,max_number)
        return_value = []
        for i in temp:
           return_value.append( (i[0]<<24)|(i[1]<<16)|(i[2]<<8)|i[3] )
        return return_value

   def  write_eeprom_registers( self,remote, starting_address, data_list ):
        device = self.remotes[remote]
        temp1 = []
        for i in data_list:
          temp2 = []
          temp2.append( (i>>24)&0xff )
          temp2.append( (i>>16)&0xff )
          temp2.append( (i>>8)&0xff)
          temp2.append( (i)&0xff)
          temp1.append( temp2)
        return write_eeprom_registers_byte( self, device, starting_address, temp1 )
   



if __name__ == "__main__":     
   pass

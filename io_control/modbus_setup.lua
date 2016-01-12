---
--- File: modbus_setup.lua
--- 
--- The purpose of this file is to set up a
--- higher level interface for modbus interface
---
--- note remote_name is set by
--- set_up_modbus_interface
---



local slave_remote
local modbus_retries = 10
local delay_time_us = 10000
local slave_id
local remote_name
local redis_connection


function store_alarm_queue( event, status, data )
    log_data = {}
    log_data["event"] = event
    log_data["data"]  = data
    log_data["time" ] = time.time()
    log_data["status"] = status
    json_data = json.encode(log_data)
    json_data = base64.encode(json_data)
    redis.job_queue.push( redis_connection, "cloud_alarm_queue", json_data )
    os.sleep(5)  --- allow redis to write data
end

--[[
function post_error( error_type, slave, registers )
  local temp
  
  temp = {}
  temp["error_type"] = error_type
  temp["slave" ] = slave
  temp["register"] = registers
  scratch = json.encode( temp )
  scratch = '"'..scratch..'"'
  redis.job_queue.push( redis_connection, "cloud_alarm_queue", scratch )
  os.sleep(5) --- let redis write out error before restarting
  
end
--]]


function add_counter( redis_key )
  local flag, data
  flag,data = redis.data_store.get( redis_connection, redis_key )
  if data == nil then
    data = 0
  else
    data = tonumber(data)
    data = data + 1
  end
  flag = redis.data_store.set( redis_connection,redis_key,data)

end

function construct_modbus_counters()
  local flag
  local dictionary
  dictionary = ""
  for i,j in pairs( remote_devices ) do
    if dictionary == "" then
       dictionary = i
    else
       dictionary = dictionary.."|"..i
    end

    flag = redis.data_store.set( redis_connection, "modbus_"..i.."_count", 0 )
    flag = redis.data_store.set( redis_connection, "modbus_"..i.."_success", 0 )
    flag = redis.data_store.set( redis_connection, "modbus_"..i.."_error", 0 )
  end
  flag = redis.data_store.set( redis_connection,"modbus_dictionary",dictionary)
end

function modbus_read_float( device, connection, address )
  local retries
  local returnValue
  local alert_data
  local number
  local float_number
  
  number = 2
  alert_data = {}
  
  address = click_reg_address[address]
 
  assert( address ~= nil )
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     returnValue = device.read_registers_tbl( connection, address, 2)
     if returnValue[1] == number then 
       add_counter("modbus_"..remote_name.."_success")
       float_number = device.get_float( returnValue[4],returnValue[5])
       return float_number
     end
     if i == modbus_retries/2 then
       
       store_alarm_queue( "read_float_warning",remote_name, address )
       os.sleep(2) -- allow for long reset
     end

  end
 
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "read_float_error",remote_name, address )
  assert(false,"modbus read bit error" )
end


function modbus_read_float_server( device, connection, address )
  local retries
  local returnValue
  local alert_data
  local number
  local float_number

  for i = 1, modbus_retries do
     
     returnValue = device.read_registers_tbl( connection, address, 2)
     if returnValue[1] == 2 then 
       float_number = device.get_float( returnValue[4],returnValue[5])
       return {"True", float_number }
     end
    
  end
  return {"False",0}
  
end

function modbus_write_float_server( device, connection, address, float_value )
  local retries
  local returnValue
  local alert_data
  local number

  local table_data 
  local reg1
  local reg2

  
  reg1,reg2 = device.set_float( float_value)
  table_data = {reg1,reg2}
 
  for i = 1, modbus_retries do
    
     write_number = device.write_registers_tbl( connection, address, table_data )
     if write_number == 2 then    
        return {"TRUE"}
     end
  end
  return {"FALSE"}
end

function modbus_write_float( device, connection, address, float_value )
  local retries
  local returnValue
  local alert_data
  local number

  local table_data 
  local reg1
  local reg2

  number = 2
  alert_data = {}
 
  reg1,reg2 = device.set_float( float_value)
 

  table_data = {reg1,reg2}
  address = click_reg_address[address]
 
  assert( address ~= nil )
 
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     write_number = device.write_registers_tbl( connection, address, table_data )
     if write_number == #table_data then  
        add_counter("modbus_"..remote_name.."_success")  
        return  
     end
  
     if i == modbus_retries/2 then
       store_alarm_queue( "write_float_warning",remote_name, address )
       os.sleep(2) -- allow for long reset
     end

  end
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "write_float_error",remote_name, address )
  assert(false,"modbus read bit error" )
end

function modbus_read_bits_tbl( device, connection, address, number )
  local retries
  local returnValue
  local alert_data
  alert_data = {}
  
  
  address = click_bit_address[address]
  assert( address ~= nil )
  
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     returnValue = device.read_bits_tbl( connection, address, number )

     
     if returnValue[1] == number then 
         add_counter("modbus_"..remote_name.."_success")        
         return returnValue 
     end
     if i == modbus_retries/2 then
      store_alarm_queue( "read_bit_warning",remote_name, address )
      os.sleep(2) -- allow for long reset
     end

  end
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "read_bit_warning",remote_name, address )
  assert(false,"modbus read bit error" )
end


function modbus_read_coil_server( device, connection, address  )
  local retries
  local results
  local return_value
  local temp
 
  for i = 1, modbus_retries do
     result = device.read_bits_tbl( connection, address, 1 )
     if result[1] ==  1 then
         return_value = {"TRUE"}
         return_value[2] = result[4]
         return return_value
     end
    
    

  end
  return_value = {"False"}
  return return_value
end

function modbus_read_register_server( device, connection, address  )
  local retries
  local returnValue
  local result
  local temp
 
  for i = 1, modbus_retries do
     --print("address",address)
     result = device.read_registers_tbl( connection, address, 1 )
     --ts.dump(result)
     if result[1] == 1 then
          return_value = {"TRUE"}
          return_value[2] = result[4]
          return return_value
     end
    
    

  end
  return_value = {"False"}
  return return_value
end



function modbus_read_registers_tbl( device, connection, address, number )
  local retries
  local returnValue
  local alert_data
  alert_data = {}

  

  address = click_reg_address[address]
  assert( address ~= nil )
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     returnValue = device.read_registers_tbl( connection, address, number )

     if returnValue[1] == number then 
        add_counter("modbus_"..remote_name.."_success")   
        return returnValue 
     end
     if i == modbus_retries/2 then
       store_alarm_queue( "read_registers_warning",remote_name, address )
       os.sleep(2)
     end
    
     
  end
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "read_registers_error",remote_name, address )
  assert( false,"modbus read register error")

end

function modbus_write_bits_tbl( device, connection, address, table_data )
  local retries
  local write_number
  local alert_data
  alert_data = {}

  --print("address",address)
  address = click_bit_address[address]
  assert( address ~= nil)
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     write_number = device.write_bits_tbl( connection, address, table_data )

     if write_number == #table_data then 
         add_counter("modbus_"..remote_name.."_success")
         return  
     end
     if i > modbus_retries/2 then
       store_alarm_queue( "write_bits_error",remote_name, address )
       os.sleep(2)
     end

  end
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "write_bits_error",remote_name, address )
  assert(false,"modbus write bits error")

end


function modbus_write_coil_register_server( device, connection, address, data )
  local retries
  local write_number
  
  table_data = { data }
  for i = 1, modbus_retries do
     write_number = device.write_bits_tbl( connection, address, table_data )
     --print( "write number is ",write_number)
     if write_number == 1 then 
         return  {"True"}
     end

  end
  return {"False"}

end



function modbus_write_register_server( device, connection, address, data ) 
  local retries
  local write_number
  local alert_data

  table_data = { data }
  for i = 1, modbus_retries do
     --print("write register")
     --ts.dump(table_data)
     write_number = device.write_registers_tbl( connection, address, table_data )
     if write_number == 1 then 
         return {"True"}  
     end
   
  end
  return {"False"}
end






function modbus_write_registers_tbl( device, connection, address, table_data ) 
  local retries
  local write_number
  local alert_data
  alert_data = {}
 
  address = click_reg_address[address]
  assert( address ~= nil )
  for i = 1, modbus_retries do
     add_counter("modbus_"..remote_name.."_count")
     os.usleep(delay_time_us) -- give room for plc
     write_number = device.write_registers_tbl( connection, address, table_data )

     if write_number == #table_data then 
           add_counter("modbus_"..remote_name.."_success")
           return  
     end
     if i == modbus_retries/2 then
       store_alarm_queue( "write_registers_warning",remote_name, address )
       os.sleep(2)
     end
  end
  add_counter("modbus_"..remote_name.."_error")
  store_alarm_queue( "write_registers_error",remote_name, address )
  assert(false,"modbus write register error")
end

---
---
---  modbus_tbl has the following format
---     position 4 which is nil is the handle
---     the fifth position is a slave that should be present on the interface or the physical interface is placed in position 1
---     { nil, ModbusRtuClient, 38400, nil, "satellite_1" }
---
---
--- 
function special_set_up_modbus_interface( remote, slave_address )

   assert( remote_devices[remote] ~= nil,"unrecognized device "..remote )

   interface  = remote_devices[remote][1]
   slave_id   = remote_devices[remote][2]
 
   assert( interface ~= nil,"invalid device " ..interface )  
     
   device = modbus_tbl[interface]

   device[2].set_slave(device[4], slave_address)
   return device

end

function set_up_modbus_interface( remote )
   

  
   assert( remote ~= nil)

   assert( remote_devices[remote] ~= nil,"unrecognized device "..remote )

   
   interface  = remote_devices[remote][1]
   slave_id   = remote_devices[remote][2]
 
   assert( interface ~= nil,"invalid device " ..interface )  
     
   device = modbus_tbl[interface]

   device[2].set_slave(device[4],slave_id)
   slave_remote = slave_id
   remote_name = remote
   return device

end

function set_up_redis_connection( redis_conn )
   assert( redis_conn ~= nil)
   redis_connection = redis_conn
end






function start_up_remotes(  )
   local interfaces
   local valid_interfaces

   --print("construct modbus")
   construct_modbus_counters()
   --print("find serial devices")   
   interfaces = find_serial_interfaces()
   interfaces = strip_out_specified_interfaces( interfaces ) -- strip out interfaces that are fixed
   --print("open modbus")
   open_modbus_interfaces( interfaces )
   ping_devices()
  
  
end
   


function find_serial_interfaces()
   local interfaces_function
   local returnValue
   -- find available interfaces
   os.execute("ls /dev/ttyUS* > serial_files.txt")
   interfaces_function = io.lines ("serial_files.txt")
   returnValue = {}
   for i,j in interfaces_function do
      table.insert(returnValue,i)
   end
   return returnValue
end


function strip_out_specified_interfaces( interfaces )
  local interface_map
  local dev
  local returnValue
  interface_map = {}

  for i,j in pairs(interfaces) do
   interface_map[j] = true
  end
  
  for i,j in pairs( modbus_tbl ) do
       dev = j[1]
       if dev ~= nil then
         interface_map[dev] = nil
       end
  end

  returnValue = {}
  for i,j in pairs( interface_map) do
   table.insert(returnValue,i)
  end
  return returnValue
end

function open_modbus_interfaces( interfaces )
  for i,j in pairs( modbus_tbl) do
     if j[1] ~= nil then
       open_fixed_interface( j )
       
     else

       open_floating_interface( interfaces, i,j )

       interfaces = strip_out_specified_interfaces( interfaces )
     end
     
   end
end

function open_floating_interface( interfaces, name, mod_entry )
  for i,j in pairs( interfaces) do
    --print("j",j)
    if try_interface( j, mod_entry ) == true then

       if try_ping( mod_entry ) == true then
        
          return
       else
         mod_entry[2].close(mod_entry[4],dev) -- close the interface
       end -- end if
    end -- end if
  end -- end for

  assert(false,"cannot open interface for "..name)
end





function open_fixed_interface( j )
    local flag 
    local conn 
    local mod 
    local dev
    local baud

    
    dev = j[1]
    mod = j[2]
    baud = j[3]
    flag, conn = mod.open( dev, baud )
    mod.set_debug(conn, 0 )
    if flag == false then
      equipment_alerts.open_modbus_interface( dev,1)
      store_alarm_queue( "interface_error",dev, " " )
    end
    assert( flag == true ,"cannot open interface  "..dev )
    j[4] = conn
     
end


function ping_devices()
  local device
  local remote
  local table_data

  for i, j in pairs( remote_devices) do
      --print("ping remote "..i)
      remote = i
      device = set_up_modbus_interface( remote )
      table_data = modbus_read_bits_tbl( device[2], device[4], j[5], 1 )
      if table_data[4] == 0 then
         store_alarm_queue( "controller_not_in_run_mode",remote, address )
         assert(false,"controller is not in run mode")
      end

  end
end

function  try_interface( interface, mod_entry )
    local flag 
    local conn 
    local mod 
    local dev
    local baud

    dev =  interface
    mod =  mod_entry[2]
    baud = mod_entry[3]
    flag, conn = mod.open( dev, baud )
    if flag == true then
      mod.set_debug(conn, 0 )
    end
    mod_entry[4] = conn
    return true
end


function try_ping( mod_entry )
      local testValue
      local returnValue
      remote = mod_entry[5]
 
      device = set_up_modbus_interface( remote )
 
      testValue = modbus_read_bits_tbl_raw( device[2], device[4], remote_devices[remote][3], 1 )

      if testValue ~= nil then
        returnValue = true
      else
        returnValue = false
      end
      return returnValue
end

function modbus_read_bits_tbl_raw( device, connection, address, number )
  local retries
  local returnValue
  local alert_data
  alert_data = {}
  
  
  address = click_bit_address[address]
  assert( address ~= nil,"address is nil")

  for i = 1, modbus_retries do
     os.usleep(delay_time_us) -- give room for plc
     returnValue = device.read_bits_tbl( connection, address, number )

     
     if returnValue[1] == number then return returnValue end
  

  end
  return nil
end


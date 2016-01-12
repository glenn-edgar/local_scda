---
---
--- sprinkler_ctrl.lua
---
---
---


---
---
--- This data structure will be automated in the future
---
---
---
---

--- these are the remote interfaces  position 4 which is nil is the handle
--- the fifth position is a slave that should be present on the interface
modbus_tbl = { }
modbus_tbl[ "rtu_1" ] = { nil, ModbusRtuClient, 38400, nil, "satellite_1" } 
--modbus_tbl[ "rtu_2" ] = {nil, ModbusRtuClient, 38400, nil,"satellite_3" }

remote_devices = {}
remote_devices["satellite_1"] = { "rtu_1",100 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit            
remote_devices["satellite_2"] = { "rtu_1",125 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit  
remote_devices["satellite_3"] = { "rtu_1",170 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit       
--remote_devices["satellite_3"] = { "rtu_1",150 , "C1", "C200", "SC10","SC11" } -- interface, modbus address , turnoff bit, wd bit

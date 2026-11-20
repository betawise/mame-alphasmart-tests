local machine = manager.machine
local cpu = machine.devices[':maincpu']
local space = cpu.spaces.program
local output = assert(os.getenv('MAME_VALIDATION_OUTPUT'))
local trace = assert(io.open(output..'/trace.tsv', 'w'))
local screen = machine.screens[':screen']
local n = 0
local function field(port, name)
 for _,f in pairs(machine.ioport.ports[port].fields) do if f.name==name then return f end end
 error('Missing input '..port..' '..name)
end
local function input(name, value)
 for _,p in pairs(machine.ioport.ports) do
  for _,f in pairs(p.fields) do
   if f.name==name then if value==nil then f:clear_value() else f:set_value(value) end;return end
  end
 end
 error('Missing input '..name)
end
local capture = {[120]=true,[300]=true,[420]=true,[600]=true,[720]=true,[840]=true,[960]=true,[1080]=true,[1200]=true}
emu.register_frame_done(function()
 n=n+1
 if capture[n] then
  local prefix=output..'/'..string.format('%04d',n)
  local pixels,w,h=screen:pixels()
  local f=assert(io.open(prefix..'.pixels','wb'));f:write(pixels);f:close()
  screen:snapshot(prefix..'.png')
  trace:write(string.format('%d\t%d\t%d\t%x\t%x\t%x\t%x\t%x\n',n,w,h,cpu.state.PC.value,cpu.state.SR.value,space:read_u32(0xfffff304),space:read_u32(0xfffff30c),space:read_u32(0xfffff310)));trace:flush()
 end
 -- Normal input events, without modifying guest RAM or firmware.
 if n==330 then input('Pen X',80);input('Pen Y',80);input('Pen Button',1) end
 if n==336 then input('Pen Button',nil) end
 if n==630 then input('Button 1',1) end
 if n==636 then input('Button 1',nil) end
 if n==870 or n==990 then input('Power',1) end
 if n==876 or n==996 then input('Power',nil) end
 if n==1200 then trace:close();machine:exit() end
end)

-- license:BSD-3-Clause
-- Exercise the real ST7565R devices through the Neo's parallel bus mapping.
-- No firmware addresses or syscall implementations are used in these checks.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local mem = cpu.spaces.program
local screen = machine.screens[":screen"]
local ports = {0x1008000, 0x1000000}
local cases = {}
local checks = 0
local function check(value, message)
    checks = checks + 1
    assert(value, message)
end
local function command(n, value) mem:write_u8(ports[n], value) end
local function write(n, value) mem:write_u8(ports[n] + 1, value) end
local function read(n) return mem:read_u8(ports[n] + 1) end
local function status(n) return mem:read_u8(ports[n]) end
local function address(n, page, col)
    command(n, 0xee)
    command(n, 0xb0 | page)
    command(n, 0x10 | (col >> 4))
    command(n, col & 15)
end
local function item(n, name)
    local index = assert(machine.devices[":lcd" .. (n - 1)].items["0/" .. name], name)
    return emu.item(index):read(0)
end
local function hold_cpu()
    mem:write_u16(0x70000, 0x60fe)
    cpu.state.SR.value = 0x2700
    cpu.state.SP.value = 0x78000
    cpu.state.PC.value = 0x70000
end
local function case(fn) cases[#cases + 1] = fn end

case(function()
    hold_cpu()
    for n = 1, 2 do
        command(n, 0xa0)
        command(n, 0xae)
        check(status(n) & 0x60 == 0x20, "display off/ADC status")
        command(n, 0xaf)
        check(status(n) & 0x60 == 0, "display on status is active low")
        command(n, 0xa1)
        check(status(n) & 0x40 == 0x40, "ADC status")
        command(n, 0xa0)
        address(n, 2, 7)
        write(n, 0x12 + n)
        write(n, 0x34 + n)
        address(n, 2, 7)
        read(n)
        check(item(n, "m_column") == 7, "dummy read advanced")
        -- Real debugger memory expressions must not consume the data latch.
        local before = item(n, "m_read_latch")
        machine.debugger:command(string.format("print b@%x", ports[n] + 1))
        machine.debugger:command(string.format("print b@%x", ports[n] + 1))
        check(item(n, "m_read_latch") == before, "debugger changed latch")
        check(item(n, "m_column") == 7, "debugger advanced column")
        check(read(n) == 0x12 + n, "first sequential byte")
        check(read(n) == 0x34 + n, "second sequential byte")
        address(n, 2, 7)
        command(n, 0xe0)
        read(n)
        check(read(n) == 0x12 + n, "RMW read")
        check(read(n) == 0x12 + n and item(n, "m_column") == 7, "RMW advanced")
        write(n, 0x56 + n)
        read(n)
        check(read(n) == 0x34 + n, "dummy read after RMW write")
        command(n, 0xee)
        check(item(n, "m_column") == 7, "END did not restore column")
        read(n)
        check(read(n) == 0x56 + n, "RMW write did not update RAM")
        address(n, 8, 0)
        write(n, 0xfe)
        write(n, 0xff)
        address(n, 8, 0)
        read(n)
        check(read(n) == 0 and read(n) == 1, "icon page is not one bit wide")
        address(n, 0, 131)
        write(n, 0x5a)
        write(n, 0xa5)
        read(n)
        check(read(n) == 0xa5 and item(n, "m_column") == 131, "column 131 saturation")
        address(n, 0, 255)
        write(n, 0xcc)
        address(n, 0, 131)
        read(n)
        check(read(n) == 0xa5, "invalid column aliased valid RAM")
        address(n, 0, 7)
        write(n, 0x77)
        address(n, 9, 7)
        write(n, 0xcc)
        address(n, 0, 7)
        read(n)
        check(read(n) == 0x77, "invalid page aliased valid RAM")
        command(n, 0x81)
        command(n, 0x0c)
        check(item(n, "m_volume") == 0x0c, "volume parameter decoded as command")
        command(n, 0xf8)
        command(n, 0x01)
        check(item(n, "m_booster_ratio") == 1, "booster parameter")
        command(n, 0xad)
        command(n, 0x03)
        check(item(n, "m_indicator_mode") == 3, "static indicator parameter")
        command(n, 0xa1)
        command(n, 0xa7)
        command(n, 0xa5)
        command(n, 0x2f)
        command(n, 0xc8)
        command(n, 0xe2)
        check(item(n, "m_display_on") == 1 and item(n, "m_adc") == 1,
            "software reset changed hardware-reset-only registers")
        check(item(n, "m_reverse") == 1 and item(n, "m_all_points") == 1,
            "software reset changed display mode")
        check(item(n, "m_power") == 7 and item(n, "m_volume") == 0x20,
            "software reset register defaults")
        check(item(n, "m_com_reverse") == 0 and item(n, "m_page") == 0,
            "software reset address/direction")
        address(n, 0, 7)
        read(n)
        check(read(n) == 0x77, "software reset cleared RAM")
    end
    -- Persist an in-progress multi-byte command and a primed read latch.
    command(1, 0x81)
    address(2, 0, 7)
    read(2)
    local saved = machine:buffer_save()
    command(1, 0x00)
    command(2, 0xb1)
    machine:buffer_load(saved)
    command(1, 0x0d)
    check(item(1, "m_volume") == 0x0d, "pending command not restored")
    check(read(2) == 0x77, "read latch/column not restored")
    for n = 1, 2 do
        command(n, 0xa0); command(n, 0xa6); command(n, 0xa4); command(n, 0xc0)
        command(n, 0x40); command(n, 0xaf)
        for page = 0, 7 do address(n, page, 0); for col = 0, 131 do write(n, 0) end end
    end
    address(1, 0, 0); write(1, 1)
end)

local light, dark
case(function()
    dark, light = screen:pixel(0, 0), screen:pixel(1, 0)
    check(dark ~= light, "pixel not rendered")
    check(screen:pixel(132, 0) == light, "controllers are not independent")
    command(1, 0xa1)
end)
case(function()
    check(screen:pixel(131, 0) == dark and screen:pixel(0, 0) == light, "SEG reversal")
    command(1, 0xa0); command(1, 0xc8)
end)
case(function()
    check(screen:pixel(0, 63) == dark and screen:pixel(0, 0) == light, "COM reversal")
    command(1, 0xc0); command(1, 0x7f)
end)
case(function()
    check(screen:pixel(0, 1) == dark and screen:pixel(0, 0) == light, "64-line scroll wrap")
    command(1, 0x40); command(1, 0xa7)
end)
case(function()
    check(screen:pixel(0, 0) == light and screen:pixel(1, 0) == dark, "display inversion")
    command(1, 0xa5)
end)
case(function()
    check(screen:pixel(0, 0) == dark and screen:pixel(131, 63) == dark, "all-points priority")
    command(1, 0xae)
end)
case(function()
    check(screen:pixel(0, 0) == light and screen:pixel(131, 63) == light, "display/power-save off")
end)

local reset_requested = false
local reset_notifier = emu.add_machine_reset_notifier(function()
    if reset_requested then
        local ok, err = pcall(function()
            hold_cpu()
            for n = 1, 2 do
                check(status(n) == 0x20, "hardware reset defaults")
                address(n, 0, 7); read(n)
                -- The renderer setup cleared normal RAM but did not touch the icon page.
                address(n, 8, 1); read(n)
                check(read(n) == 1, "hardware reset cleared display RAM")
            end
        end)
        if ok then print("PASS ST7565R parallel bus, rendering, save state and reset (" .. checks .. " checks)")
        else print("FAIL ST7565R: " .. tostring(err)) end
        machine:exit()
    end
end)
case(function() reset_requested = true; machine:soft_reset() end)

local frame, index, failed = 0, 0, false
emu.register_frame_done(function()
    frame = frame + 1
    if reset_notifier and frame >= 120 and (frame - 120) % 3 == 0 and not failed and not reset_requested then
        index = index + 1
        local ok, err = pcall(cases[index])
        if not ok then failed = true; print("FAIL ST7565R: " .. tostring(err)); machine:exit() end
    end
end)

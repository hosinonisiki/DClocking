import uart
import bus
import module_signal_router
import spi

ser = uart.MySerial("COM3", baudrate = 57600, parity = "E", timeout = 0.5)
bus = bus.Bus(ser)
router = module_signal_router.ModuleSignalRouter(bus)
sp = spi.Spi(ser)

VERBOSE = False
if VERBOSE:
    # refresh
    print("refreshing bus modules")
    ser.post(b":BUS_.ROUT.CTRL.RSTR!")
    ser.post(b":BUS_.ROUT.CTRL.SETR!")
    ser.post(b":BUS_.ROUT.CTRL.RSTC!")
    ser.post(b":BUS_.ROUT.CTRL.SETC!")
    ser.post(b":BUS_.TRIG.CTRL.RSTR!")
    ser.post(b":BUS_.TRIG.CTRL.SETR!")
    ser.post(b":BUS_.TRIG.CTRL.RSTC!")
    ser.post(b":BUS_.TRIG.CTRL.SETC!")
    ser.post(b":BUS_.ACCM.CTRL.RSTR!")
    ser.post(b":BUS_.ACCM.CTRL.SETR!")
    ser.post(b":BUS_.ACCM.CTRL.RSTC!")
    ser.post(b":BUS_.ACCM.CTRL.SETC!")

    # initialize
    print("writing parameters")
    ser.post(b":BUS_.ACCM.WRTE.ADDR.\x00\x00\x00\x01.DATA.\x01\x00\x00\x00.HOLD!")
    ser.post(b":BUS_.ACCM.WRTE.ADDR.\x00\x00\x00\x00.DATA.\x00\x00\x00\x00!")

    # FL9781 initial settings
    print("writing configuration for CLK1")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x00\x3C\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x00\x18\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x04\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x10\x7C\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x11\x01\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x12\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x13\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x14\x0A\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x15\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x16\x04\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x17\xB4\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x18\x06\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x19\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x1A\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x1B\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x1C\x02\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x1D\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x02\x32\x01\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF0\x08\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF1\x0A\x00!") # former value 0x08
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF2\x08\x00!") # former value 0x08
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF3\x0A\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF4\x0A\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\xF5\x0A\x00!") # former value 0x0A
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x90\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x91\x80\x00!") # former value 0x00
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x92\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x93\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x94\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x95\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x96\x44\x00!") # former value 0x11
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x97\x80\x00!") # former value 0x00
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\x98\x00\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\xE0\x02\x00!") # former value 0x00
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x01\xE1\x02\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x00\x18\x07\x00!")
    ser.post(b":SPI_.CLK1.\x00\x00\x17\x17.\x02\x32\x01\x00!")

    print("writing configuration for DAC1")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x02\x00\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x04\x59\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x05\x06\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x0B\x00\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x0C\x02\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x0D\x00\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x0E\x02\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x0F\x00\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x10\x02\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x11\x00\x00\x00!")
    ser.post(b":SPI_.DAC1.\x00\x00\x0F\x0F.\x12\x00\x00\x00!")

    print("writing configuration for DAC2")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x02\x00\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x04\x59\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x05\x06\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x0B\x00\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x0C\x02\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x0D\x00\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x0E\x02\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x0F\x00\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x10\x02\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x11\x00\x00\x00!")
    ser.post(b":SPI_.DAC2.\x00\x00\x0F\x0F.\x12\x00\x00\x00!")

    ser.post(b":SPI_.ADC1.\x00\x00\x17\x17.\x00\x14\x41\x00!")
    ser.post(b":SPI_.ADC1.\x00\x00\x17\x17.\x00\x17\x06\x00!")
    ser.post(b":SPI_.ADC1.\x00\x00\x17\x17.\x00\xFF\x01\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\x14\x41\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\x17\x06\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\xFF\x01\x00!")

    router.set_routing(2, 0)
    router.set_routing(3, 1)
    router.set_routing(4, 5)
    router.set_routing(5, 4)
    #router.implement_routing()
    router.upload()
else:
    ser.post(b":SPI_.ADC1.\x00\x00\x0F\x17.\x80\x02\x00\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\x14\x41\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\x17\x06\x00!")
    ser.post(b":SPI_.ADC2.\x00\x00\x17\x17.\x00\xFF\x01\x00!")
    
    ser.post(b":BUS_.ACCM.WRTE.ADDR.\x00\x00\x00\x01.DATA.\x00\x10\x00\x00.HOLD!")
    ser.post(b":BUS_.ACCM.WRTE.ADDR.\x00\x00\x00\x00.DATA.\x00\x00\x00\x00!")

    router.set_routing(0, 0)
    router.set_routing(1, 1)
    router.set_routing(4, 5)
    router.set_routing(5, 4)
    #router.implement_routing()
    router.upload()

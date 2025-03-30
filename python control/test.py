import uart
import bus
import module
import module_signal_router
import spi
from port_numbers import *

ser = uart.MySerial("COM5", baudrate = 19200, parity = "E", timeout = 0.5)
bus = bus.Bus(ser)
router = module_signal_router.ModuleSignalRouter(bus)
tri = module.ModuleBase(bus, "TRIG")
acc = module.ModuleBase(bus, "ACCM")
sclr = module.ModuleScaler(bus, "SCLR")
pid = module.ModulePID(bus, "PIDC")
spi = spi.Spi(ser)

VERBOSE = True
if VERBOSE:
    # refresh
    print("refreshing bus modules")
    router.reset()
    tri.reset()
    acc.reset()

    # initialize
    print("writing parameters")
    acc.write(1, "01000000", hold = True)
    acc.write(0, "00000000")

    # FL9781 initial settings
    print("writing configuration for CLK1")
    spi.write("CLK1", 3, 3, "00003C")
    spi.write("CLK1", 3, 3, "000018")
    spi.write("CLK1", 3, 3, "000400")
    spi.write("CLK1", 3, 3, "00107C")
    spi.write("CLK1", 3, 3, "001101")
    spi.write("CLK1", 3, 3, "001200")
    spi.write("CLK1", 3, 3, "001300")
    spi.write("CLK1", 3, 3, "00140A")
    spi.write("CLK1", 3, 3, "001500")
    spi.write("CLK1", 3, 3, "001604")
    spi.write("CLK1", 3, 3, "0017B4")
    spi.write("CLK1", 3, 3, "001806")
    spi.write("CLK1", 3, 3, "001900")
    spi.write("CLK1", 3, 3, "001A00")
    spi.write("CLK1", 3, 3, "001B00")
    spi.write("CLK1", 3, 3, "001C02")
    spi.write("CLK1", 3, 3, "001D00")
    spi.write("CLK1", 3, 3, "023201")
    spi.write("CLK1", 3, 3, "00F008")
    spi.write("CLK1", 3, 3, "00F10A") # former value 0x08
    spi.write("CLK1", 3, 3, "00F208") # former value 0x08
    spi.write("CLK1", 3, 3, "00F30A")
    spi.write("CLK1", 3, 3, "00F40A")
    spi.write("CLK1", 3, 3, "00F50A") # former value 0x0A
    spi.write("CLK1", 3, 3, "019000")
    spi.write("CLK1", 3, 3, "019180") # former value 0x00
    spi.write("CLK1", 3, 3, "019200")
    spi.write("CLK1", 3, 3, "019300")
    spi.write("CLK1", 3, 3, "019400")
    spi.write("CLK1", 3, 3, "019500")
    spi.write("CLK1", 3, 3, "019644") # former value 0x11
    spi.write("CLK1", 3, 3, "019780") # former value 0x00
    spi.write("CLK1", 3, 3, "019800")
    spi.write("CLK1", 3, 3, "01E002") # former value 0x00
    spi.write("CLK1", 3, 3, "01E102")
    spi.write("CLK1", 3, 3, "001807")
    spi.write("CLK1", 3, 3, "023201")

    print("writing configuration for DAC1")
    spi.write("DAC1", 2, 2, "0200")
    spi.write("DAC1", 2, 2, "0459")
    spi.write("DAC1", 2, 2, "0506")
    spi.write("DAC1", 2, 2, "0B00")
    spi.write("DAC1", 2, 2, "0C02")
    spi.write("DAC1", 2, 2, "0D00")
    spi.write("DAC1", 2, 2, "0E02")
    spi.write("DAC1", 2, 2, "0F00")
    spi.write("DAC1", 2, 2, "1002")
    spi.write("DAC1", 2, 2, "1100")
    spi.write("DAC1", 2, 2, "1200")

    print("writing configuration for DAC2")
    spi.write("DAC2", 2, 2, "0200")
    spi.write("DAC2", 2, 2, "0459")
    spi.write("DAC2", 2, 2, "0506")
    spi.write("DAC2", 2, 2, "0B00")
    spi.write("DAC2", 2, 2, "0C02")
    spi.write("DAC2", 2, 2, "0D00")
    spi.write("DAC2", 2, 2, "0E02")
    spi.write("DAC2", 2, 2, "0F00")
    spi.write("DAC2", 2, 2, "1002")
    spi.write("DAC2", 2, 2, "1100")
    spi.write("DAC2", 2, 2, "1200")

    print("writing configuration for ADC1")
    spi.write("ADC1", 3, 3, "001441")
    spi.write("ADC1", 3, 3, "001706")
    spi.write("ADC1", 3, 3, "00FF01")

    print("writing configuration for ADC2")
    spi.write("ADC2", 3, 3, "001441")
    spi.write("ADC2", 3, 3, "001706")
    spi.write("ADC2", 3, 3, "00FF01")

    router.set_routing(OUTPUT_C, SCALER_OUT)
    router.set_routing(SCALER_IN, PID_OUT)
    router.set_routing(PID_IN, INPUT_C)
    #router.implement_routing()
    router.upload()
else:
    spi.write("ADC1", 3, 3, "001441")
    spi.write("ADC1", 3, 3, "001706")
    spi.write("ADC1", 3, 3, "00FF01")
    spi.write("ADC2", 3, 3, "001441")
    spi.write("ADC2", 3, 3, "001706")
    spi.write("ADC2", 3, 3, "00FF01")
    
    acc.write(1, "01000000", hold = True)
    acc.write(0, "00000000")

    router.set_routing(OUTPUT_C, PID_OUT)
    router.set_routing(OUTPUT_D, SCALER_OUT)
    router.set_routing(SCALER_IN, PID_OUT)
    router.set_routing(PID_IN, INPUT_D)
    #-26000 -50000 -18000
    # 20000
    #router.set_routing(OUTPUT_C, TRI_SIN)
    #router.set_routing(OUTPUT_D, TRI_COS)
    #router.implement_routing()
    router.upload()

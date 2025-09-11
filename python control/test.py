import uart
import bus
import module
import module_signal_router
import spi
from port_numbers import *
import time

import code

ser = uart.MySerial("COM6", baudrate = 19200, parity = "E", timeout = 0.5)
bus = bus.Bus(ser)
router = module_signal_router.ModuleSignalRouter(bus)
tri = module.ModuleBase(bus, "TRIG")
acc = module.ModuleAccumulator(bus, "ACCM")
sclr = module.ModuleScaler(bus, "SCLR")
pid = module.ModulePID(bus, "PIDC")
spi = spi.Spi(ser)

def recal():
    spi.write("CLK2", 3, 3, "001806")
    spi.write("CLK2", 3, 3, "023201")
    spi.write("CLK2", 3, 3, "001807")
    spi.write("CLK2", 3, 3, "023201")
    spi.write("CLK2", 3, 2, "801F") # Check if PLL caled

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

    '''
    print("writing configuration for ADC1")
    spi.write("ADC1", 3, 3, "001441")
    spi.write("ADC1", 3, 3, "001706")
    spi.write("ADC1", 3, 3, "00FF01")

    print("writing configuration for ADC2")
    spi.write("ADC2", 3, 3, "001441")
    spi.write("ADC2", 3, 3, "001706")
    spi.write("ADC2", 3, 3, "00FF01")
    '''

    print("writing configuration for CLK2")
    spi.write("CLK2", 3, 3, "00003C") # Soft Reset
    spi.write("CLK2", 3, 3, "000018") # Set
    spi.write("CLK2", 3, 3, "000401") # Read Back Active Register
    spi.write("CLK2", 3, 3, "00107C") # PLL power-down deassert
    spi.write("CLK2", 3, 3, "001101") # PLL R divider LSB
    spi.write("CLK2", 3, 3, "001200") # PLL R divider MSB
    spi.write("CLK2", 3, 3, "001300") # PLL A counter
    spi.write("CLK2", 3, 3, "00140A") # PLL B divider LSB
    spi.write("CLK2", 3, 3, "001500") # PLL B divider MSB
    spi.write("CLK2", 3, 3, "001604") # PLL control 1
    spi.write("CLK2", 3, 3, "0017B4") # PLL control 2
    spi.write("CLK2", 3, 3, "001806") # PLL control 3
    spi.write("CLK2", 3, 3, "001900") # PLL control 4
    spi.write("CLK2", 3, 3, "001A00") # PLL control 5
    spi.write("CLK2", 3, 3, "001B00") # PLL control 6
    spi.write("CLK2", 3, 3, "001C02") # PLL control 7
    spi.write("CLK2", 3, 3, "001D00") # PLL control 8
    spi.write("CLK2", 3, 3, "023201") # Update all registers
    spi.write("CLK2", 3, 3, "00F008") # LVPECL output 0
    spi.write("CLK2", 3, 3, "00F108") # LVPECL output 1
    spi.write("CLK2", 3, 3, "00F208") # LVPECL output 2
    spi.write("CLK2", 3, 3, "00F30A") # LVPECL output 3
    spi.write("CLK2", 3, 3, "00F408") # LVPECL output 4
    spi.write("CLK2", 3, 3, "00F50A") # LVPECL output 5
    spi.write("CLK2", 3, 3, "019011") # Divider 0
    spi.write("CLK2", 3, 3, "019100") # Divider 0
    spi.write("CLK2", 3, 3, "019200") # Divider 0
    spi.write("CLK2", 3, 3, "019311") # Divider 1
    spi.write("CLK2", 3, 3, "019400") # Divider 1
    spi.write("CLK2", 3, 3, "019500") # Divider 1
    spi.write("CLK2", 3, 3, "019611") # Divider 2
    spi.write("CLK2", 3, 3, "019700") # Divider 2
    spi.write("CLK2", 3, 3, "019800") # Divider 2
    spi.write("CLK2", 3, 3, "01E000") # VCO devider
    spi.write("CLK2", 3, 3, "01E102") # Input clock select
    spi.write("CLK2", 3, 3, "001807") # VCO cal now
    spi.write("CLK2", 3, 3, "023201") # Update all registers

    while True:
        spi.write("CLK2", 3, 2, "801F") # Check if PLL caled
        break


    #FL9613 initial settings
    print("writing configuration for ADC1")
    #spi.write("ADC1", 3, 3, "00003C") # Soft Reset
    #spi.write("ADC1", 3, 3, "000018") # Set
    spi.write("ADC1", 3, 3, "000503") # Enable
    spi.write("ADC1", 3, 3, "000800") # Power mode
    spi.write("ADC1", 3, 3, "000901") # Global clock
    spi.write("ADC1", 3, 3, "000B00") # Clock divide
    spi.write("ADC1", 3, 3, "000D00") # Test mode control
    spi.write("ADC1", 3, 3, "001000") # Offset adjust
    spi.write("ADC1", 3, 3, "001405") # Output Mode
    spi.write("ADC1", 3, 3, "001501") # Output adjust
    spi.write("ADC1", 3, 3, "001600") # Clock phase control
    spi.write("ADC1", 3, 3, "001789") # DCO clock delay
    spi.write("ADC1", 3, 3, "001800") # Input span select
    spi.write("ADC1", 3, 3, "00FF01") # Transfer

    print("writing configuration for ADC2")
    #spi.write("ADC2", 3, 3, "00003C") # Soft Reset
    #spi.write("ADC2", 3, 3, "000018") # Set
    spi.write("ADC2", 3, 3, "000503") # Enable
    spi.write("ADC2", 3, 3, "000800") # Power mode
    spi.write("ADC2", 3, 3, "000901") # Global clock
    spi.write("ADC2", 3, 3, "000B00") # Clock divide
    spi.write("ADC2", 3, 3, "000D00") # Test mode control
    spi.write("ADC2", 3, 3, "001000") # Offset adjust
    spi.write("ADC2", 3, 3, "001405") # Output Mode
    spi.write("ADC2", 3, 3, "001501") # Output adjust
    spi.write("ADC2", 3, 3, "001600") # Clock phase control
    spi.write("ADC2", 3, 3, "001789") # DCO clock delay
    spi.write("ADC2", 3, 3, "001800") # Input span select
    spi.write("ADC2", 3, 3, "00FF01") # Transfer

    router.set_routing(OUTPUT_C, SCALER_OUT)
    router.set_routing(SCALER_IN, PID_OUT)
    router.set_routing(PID_IN, INPUT_C)
    #router.implement_routing()
    router.upload()

    code.interact(local=locals())
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

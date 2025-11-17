import spi as sp
import time

def init_AD9680(spi, port, chip):
    print("Configuring AD9680 on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000081")
    time.sleep(0.5)
    chip.write("057115")
    chip.write("05BD1F")
    chip.write("058F2F")
    chip.write("05902F")
    chip.write("057088")
    chip.write("056E00")
    chip.write("058B83")
    chip.write("01200A")
    chip.write("057114")
    time.sleep(0.5)
    ret = chip.read("856F") # x80 when locked
    if ret != "80":
        raise Exception("AD9680 not locked, status: " + ret + " at x056F.")

def init_AD9152(spi, port, chip):
    print("Configuring AD9152 on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000081")
    time.sleep(0.5)
    chip.write("000000")
    chip.write("001100")
    chip.write("008000")
    chip.write("008100")
    chip.write("011200")
    chip.write("011000")
    chip.write("020000")
    chip.write("020100")
    chip.write("023028")
    chip.write("031220")
    chip.write("030000")
    chip.write("045000")
    chip.write("045100")
    chip.write("045204")
    chip.write("045383")
    chip.write("045400")
    chip.write("04551F")
    chip.write("045601")
    chip.write("04570F")
    chip.write("04582F")
    chip.write("045920")
    chip.write("045A80")
    chip.write("045D49")
    chip.write("047801")
    chip.write("046C0F")
    chip.write("047601")
    chip.write("047D0F")
    chip.write("02A608")
    chip.write("0248AA")
    chip.write("02AAB7")
    chip.write("02AB87")
    chip.write("02A701")
    chip.write("031401")
    chip.write("023028")
    chip.write("020600")
    chip.write("020601")
    chip.write("028904")
    '''
    chip.write("003A00")
    chip.write("008004")
    chip.write("008110")
    '''
    chip.write("028001")
    chip.write("028005")
    time.sleep(0.5)
    ret = chip.read("8281") # x03 when locked
    if ret != "03":
        raise Exception("AD9152 not locked, status: " + ret + " at x0281.")
    chip.write("026862")

    chip.write("030808")
    chip.write("030913")

    chip.write("030101")
    chip.write("030400")
    chip.write("03060A")
    chip.write("003A01")
    chip.write("003A81")

    chip.write("003AC1")
    
    chip.write("030001")
    chip.write("00E730")
    '''
    chip.write("030606")
    chip.write("031200")
    chip.write("031300")
    chip.write("031400")
    chip.write("045200")
    '''

def init_AD9528(spi, port, chip):
    print("Configuring AD9528 (no external ref) on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000081")
    time.sleep(0.5)
    chip.write("000000")
    chip.write("000100")
    chip.write("000F01") # update all

    chip.write("010001")
    chip.write("010100")
    chip.write("010201")
    chip.write("010300")
    chip.write("01040A")
    chip.write("010500")
    chip.write("010680") # 01060A to enable pll1
    chip.write("010700") # 010723 to enable pll1
    chip.write("010829")
    chip.write("010914")
    chip.write("010A06")
    chip.write("02000A")
    chip.write("02010A")
    chip.write("020203")
    chip.write("020300") # 020301 to calib pll2 and 020300 to clear
    chip.write("020404")
    chip.write("02053A")
    chip.write("020600")
    chip.write("020701")
    chip.write("020809")

    # channel 1, 0303 to 0305, sysref to adc, 3.90625MHz
    chip.write("030000")
    chip.write("030100")
    chip.write("0302FF")
    # channel 2, 0306 to 0308, device clk to adc, 1GHz
    chip.write("030600")
    chip.write("030700")
    chip.write("030800")
    # channel 3, 0309 to 030B, refclk to dac, 250MHz
    chip.write("030900")
    chip.write("030A00")
    chip.write("030B03")
    # channel 4, 030C to 030E, device clk to dac, 1GHz
    chip.write("030C00")
    chip.write("030D00")
    chip.write("030E00")
    # channel 5, 030F to 0311, sysref to dac, 3.90625MHz
    chip.write("030F00")
    chip.write("031000")
    chip.write("0311FF")
    # channel 6, 0312 to 0314, dac core clk to fpga, 250MHz
    chip.write("031200")
    chip.write("031300")
    chip.write("031403")
    # channel 7, 0315 to 0317, dac refclk to fpga, 250MHz
    chip.write("031500")
    chip.write("031600")
    chip.write("031703")
    # channel 8, 0318 to 031A, dac sysref to fpga, 3.90625MHz
    chip.write("031800")
    chip.write("031900")
    chip.write("031AFF")
    # channel 9, 031B to 031D, adc sysref to fpga, 3.90625MHz
    chip.write("031B00")
    chip.write("031C00")
    chip.write("031DFF")
    # channel 10, 031E to 0320, adc core clk to fpga, 250MHz
    chip.write("031E00")
    chip.write("031F00")
    chip.write("032003")
    # channel 13, 0327 to 0329, adc refclk to fpga, 250MHz
    chip.write("032700")
    chip.write("032800")
    chip.write("032903")

    chip.write("032A00") # 032A01 then 032A00 to sync all
    chip.write("032B00")
    chip.write("032C00")
    chip.write("032D00")
    chip.write("032E00")
    chip.write("040040")
    chip.write("040100")
    chip.write("040218")
    chip.write("040396") # 040397 to req sysref, 040396 to clear
    chip.write("040404")

    chip.write("050010")
    chip.write("050100")
    chip.write("050200")
    chip.write("0503FF")
    chip.write("0504FF")
    chip.write("000F01") # update all

    chip.write("040397") # req sysref
    chip.write("000F01") # update all
    time.sleep(0.5)
    chip.write("020301") # calib pll2
    chip.write("000F01") # update all
    chip.write("020300") # clear
    chip.write("000F01") # update all
    chip.write("032A01") # set
    chip.write("000F01") # update all
    chip.write("032A00") # sync all
    chip.write("000F01") # update all
    time.sleep(0.5)
    ret = chip.read("8508")
    if not ret in ["f2", "f3", "e6", "e7"]:
        raise Exception("AD9528 not locked, status: " + ret + " at x0508.")
    if ret[0] == "f":
        print("Info: no external reference detected by AD9528.")
    else:
        print("Warning: external reference detected by AD9528. Make sure you don't want reference.")
    if ret[1] == "2" or ret[1] == "6":
        print("Info: PLL1 not locked.")
    else:
        print("Warning: PLL1 locked. Make sure you don't want reference.")

def init_AD9528_ext_ref(spi, port, chip):
    print("Configuring AD9528 (external ref) on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000081")
    time.sleep(0.5)
    chip.write("000000")
    chip.write("000100")
    chip.write("000F01") # update all

    chip.write("010001")
    chip.write("010100")
    chip.write("010201")
    chip.write("010300")
    chip.write("01040A")
    chip.write("010500")
    chip.write("01060A") # 010680 to disable pll1
    chip.write("010723") # 010700 to disable pll1
    chip.write("010829")
    chip.write("010914")
    chip.write("010A06")
    chip.write("02000A")
    chip.write("02010A")
    chip.write("020203")
    chip.write("020300") # 020301 to calib pll2 and 020300 to clear
    chip.write("020404")
    chip.write("02053A")
    chip.write("020600")
    chip.write("020701")
    chip.write("020809")

    # channel 1, 0303 to 0305, sysref to adc, 3.90625MHz
    chip.write("030000")
    chip.write("030100")
    chip.write("0302FF")
    # channel 2, 0306 to 0308, device clk to adc, 1GHz
    chip.write("030600")
    chip.write("030700")
    chip.write("030800")
    # channel 3, 0309 to 030B, refclk to dac, 250MHz
    chip.write("030900")
    chip.write("030A00")
    chip.write("030B03")
    # channel 4, 030C to 030E, device clk to dac, 1GHz
    chip.write("030C00")
    chip.write("030D00")
    chip.write("030E00")
    # channel 5, 030F to 0311, sysref to dac, 3.90625MHz
    chip.write("030F00")
    chip.write("031000")
    chip.write("0311FF")
    # channel 6, 0312 to 0314, dac core clk to fpga, 200MHz, used as system reference clk
    chip.write("031200")
    chip.write("031300")
    chip.write("031404")
    # channel 7, 0315 to 0317, dac refclk to fpga, 250MHz
    chip.write("031500")
    chip.write("031600")
    chip.write("031703")
    # channel 8, 0318 to 031A, dac sysref to fpga, 3.90625MHz
    chip.write("031800")
    chip.write("031900")
    chip.write("031AFF")
    # channel 9, 031B to 031D, adc sysref to fpga, 3.90625MHz
    chip.write("031B00")
    chip.write("031C00")
    chip.write("031DFF")
    # channel 10, 031E to 0320, adc core clk to fpga, 200MHz, used as system reference clk
    chip.write("031E00")
    chip.write("031F00")
    chip.write("032004")
    # channel 13, 0327 to 0329, adc refclk to fpga, 250MHz
    chip.write("032700")
    chip.write("032800")
    chip.write("032903")

    chip.write("032A00") # 032A01 then 032A00 to sync all
    chip.write("032B00")
    chip.write("032C00")
    chip.write("032D00")
    chip.write("032E00")
    chip.write("040040")
    chip.write("040100")
    chip.write("040218")
    chip.write("040396") # 040397 to req sysref, 040396 to clear
    chip.write("040404")

    chip.write("050010")
    chip.write("050100")
    chip.write("050200")
    chip.write("0503FF")
    chip.write("0504FF")
    chip.write("000F01") # update all

    chip.write("040397") # req sysref
    chip.write("000F01") # update all
    time.sleep(0.5)
    chip.write("020301") # calib pll2
    chip.write("000F01") # update all
    chip.write("020300") # clear
    chip.write("000F01") # update all
    chip.write("032A01") # set
    chip.write("000F01") # update all
    chip.write("032A00") # sync all
    chip.write("000F01") # update all
    time.sleep(0.5)
    ret = chip.read("8508")
    if not ret in ["f2", "f3", "e6", "e7"]:
        raise Exception("AD9528 not locked, status: " + ret + " at x0508.")
    if ret[0] == "f":
        print("Warning: no external reference detected by AD9528.")
    else:
        print("Info: external reference detected by AD9528.")
    if ret[1] == "2" or ret[1] == "6":
        print("Warning: PLL1 not locked.")
    else:
        print("Info: PLL1 locked.")

def init_AD9627(spi, port, chip):
    print("Configuring AD9627 on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("00003C") # Soft Reset
    chip.write("000018") # Set
    chip.write("000503") # Enable
    chip.write("001441") # Output Mode 2's comp
    chip.write("001701") # Output Delay
    chip.write("00FF01") # Transfer

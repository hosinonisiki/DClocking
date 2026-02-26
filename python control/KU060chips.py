import spi as sp
import time

def init_ADS54J60(spi, port, chip):
    print("Configuring ADS54J60 on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000089")
    chip.write("000080")	
    time.sleep(0.5)	
    chip.write("400468")
    chip.write("400300")
    chip.write("604100")
    chip.write("604D00")
    chip.write("607200")
    chip.write("605200")
    chip.write("600001")
    chip.write("600000")
    chip.write("400469")
    chip.write("400300")	
    chip.write("603100")
    chip.write("603200")	
    chip.write("600101")
    chip.write("600580")
    chip.write("601680")	
    chip.write("40046A")
    chip.write("400300")	
    chip.write("601600")	
	
    

def init_ADS54J69(spi, port, chip):
    print("Configuring ADS54J69 on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000089")
    chip.write("000080")	
    time.sleep(0.5)
    chip.write("400468")
    chip.write("400300")
    chip.write("604116")
    chip.write("604D08")
    chip.write("607208")
    chip.write("605280")
    chip.write("600001")
    chip.write("600000")
    chip.write("400469")
    chip.write("400300")	
    chip.write("60310A")
    chip.write("60320A")	
    chip.write("600101")
    chip.write("600580")
      

   
  

def init_AD9144(spi, port, chip):
    print("Configuring AD9144 (no external ref) on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
   
    time.sleep(0.5)
    chip.write("0000BD")
    chip.write("00003C")
    chip.write("001100") # 
    chip.write("008000")
    chip.write("008100")
	
    chip.write("012D8B")
    chip.write("014601")
    chip.write("02A4FF")
    chip.write("0232FF")
    chip.write("033301")
    chip.write("008762") # 
    chip.write("0088C9") # 010723 to enable pll1
    chip.write("00890E")
    chip.write("008A12")
    chip.write("008D7B")
    chip.write("01B000")
    chip.write("01B924")
    chip.write("01BC0D")
    chip.write("01BE02") # 020301 to calib pll2 and 020300 to clear
    chip.write("01BF8E")
    chip.write("01C02A")
    chip.write("01C12A")
    chip.write("01C47E")
    chip.write("008B02")
    chip.write("008C03")
    chip.write("008508")
    chip.write("01B509")
    chip.write("01BB13")
    chip.write("01C506")
    chip.write("008300")
   
    chip.write("011200")
    chip.write("011000")
    chip.write("020000")
    chip.write("020100")
    chip.write("045000")
    chip.write("045100")
    chip.write("045200")
    chip.write("045387")
    chip.write("045400")
    chip.write("04551F")
    chip.write("045603")
    chip.write("04570F")
    chip.write("04582F")
    chip.write("045920")
    chip.write("045A80")
    chip.write("045D00")
    chip.write("046C00")
    chip.write("047601")
    chip.write("047DFF")
	
    chip.write("02AAB7")
    chip.write("02AB87")
    chip.write("02B1B7")
    chip.write("02B287")
    chip.write("02A701")
    chip.write("02AE01")
    chip.write("031401")
    chip.write("023018")
    chip.write("020600") 
    chip.write("020601")
    chip.write("028905")
    chip.write("028462")
    chip.write("0285C9")
    chip.write("02860E")
    chip.write("028712")
    chip.write("028A7B")
    chip.write("028B00") 
    chip.write("029089")
    chip.write("029424")
    chip.write("029603")
    chip.write("02970D")
    chip.write("029902")
    chip.write("029A8E")
    chip.write("029C2A") 
    chip.write("029F78") 
    chip.write("02A006") 
    chip.write("028001") 
    chip.write("026822") # 
    chip.write("030101") # 
    chip.write("030400") # 
    chip.write("030500") # 
    chip.write("030600") # 
    chip.write("030700") # 
    chip.write("003A02") # 
	chip.write("003A82")
    chip.write("003AC2")
	chip.write("030001")	
	
   
		
		
def init_lmk04828(spi, port, chip):
    print("Configuring lmk04828 (no external ref) on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    time.sleep(0.5)
    chip.write("000090")
    chip.write("000010")
    chip.write("000200") # power down
    chip.write("000306")
    chip.write("0004D0")
    chip.write("00055B")
    chip.write("000600")
    chip.write("000C51")
    chip.write("000D04")
    chip.write("01000C") # dclkout0 12div 250MHz
    chip.write("010155") # 
    chip.write("010255")
    chip.write("010300")
    chip.write("010402")
    chip.write("010500")
    chip.write("0106F0")
    chip.write("010711")
    chip.write("010803") # dclkout2 3div 1000MHz
    chip.write("010955")
    chip.write("010A55")
    chip.write("010B00")
    chip.write("010C22")
    chip.write("010D00")
    chip.write("010EF0")
    chip.write("010F11")
    chip.write("01100C") # dclkout4 12div 250MHz
    chip.write("011155")
    chip.write("011255")
    chip.write("011300")
    chip.write("011422")
    chip.write("011500")
    chip.write("0116F0")
    chip.write("011711")
    chip.write("011803") # dclkout6 3div 1000MHz
    chip.write("011955")
    chip.write("011A55")
    chip.write("011B00")
    chip.write("011C22")
    chip.write("011D00")
    chip.write("011EF0")
    chip.write("011F11")
    chip.write("01200C")# dclkout8 12div 250MHz
    chip.write("012155")
    chip.write("012255")
    chip.write("012300")
    chip.write("012402") # channel 9, adc sysref to fpga, 3.90625MHz
    chip.write("012500")
    chip.write("0126F0")
    chip.write("012711")
    chip.write("012803")# dclkout10 3div 1000MHz
    chip.write("012955")
    chip.write("012A55")
    chip.write("012B00")
    chip.write("012C22")
    chip.write("012D00")
    chip.write("012EF0")
    chip.write("012F11") 
    chip.write("01300C")# dclkout12 12div 250MHz
    chip.write("013155")
    chip.write("013255")
    chip.write("013300")
    chip.write("013402")
    chip.write("013500")
    chip.write("0136F0")
    chip.write("013711")
    chip.write("013821")
    chip.write("013903")
    chip.write("013A06") #[4:0] sysref_div[12:8]
    chip.write("013B00") #sysref_div[7:0]
    chip.write("013C00")
    chip.write("013D08")
    chip.write("013E03") # 
    chip.write("013F01") # 
    chip.write("014002") # 
    chip.write("014100") # 
    chip.write("014200") # 
    chip.write("014311") # 
    chip.write("0144FF") # 
    chip.write("01457F") # 
    chip.write("01461B") #  
    chip.write("01470A") #  CLKin_SEL_MODE[6:4]
    chip.write("014882") #  
    chip.write("014902")
    chip.write("014A33")
    chip.write("014B16")
    chip.write("014C00")
    chip.write("014D00")
    chip.write("014EC0") # 
    chip.write("014F7F") # 
    chip.write("015003") # 
    chip.write("015101") # 
    chip.write("015200") # 
    chip.write("015300") # 
    chip.write("015401") # 
    chip.write("015500") # 
    chip.write("015601") #  
    chip.write("015700") #  
    chip.write("015801") #  	
    chip.write("015900")
    chip.write("015A0A")
    chip.write("015BD4")
    chip.write("015C20")
    chip.write("015D00")
    chip.write("015E00") # 
    chip.write("015F0B") # 
    chip.write("016000") # 
    chip.write("016164") # 
    chip.write("016244") # 
    chip.write("016300") # 
    chip.write("016400") # 
    chip.write("01650C") # 
    chip.write("0171AA") #  
    chip.write("017202") #  
    chip.write("017C15") #  	
	chip.write("017D33")
    chip.write("016600") #  
    chip.write("016705") #  
    chip.write("0168DC") #  	
    chip.write("016959")
    chip.write("016A20")
    chip.write("016B00")
    chip.write("016C00")
    chip.write("016D00")
    chip.write("016E13")  
    chip.write("017300")  
    chip.write("018200")  
    chip.write("018300")  
    chip.write("018400")  
    chip.write("018500")  
    chip.write("018800")  
    chip.write("018900") 
    chip.write("018A00") 
    chip.write("018B00")  
    chip.write("1FFD00")  
    chip.write("1FFE00")  
    chip.write("1FFF53") 	

   

def init_lmk04828_ext_ref(spi, port, chip):
    print("Configuring lmk04828 (external ref) on fmc port {}, chip {}".format(port, chip))
    name = "P{}C{}".format(port, chip)
    chip = sp.SpiChip(name, spi)
    chip.write("000090")
    chip.write("000010")
    chip.write("000200") # power down
    chip.write("000306")
    chip.write("0004D0")
    chip.write("00055B")
    chip.write("000600")
    chip.write("000C51")
    chip.write("000D04")
    chip.write("01000C") # dclkout0 12div 250MHz
    chip.write("010155") # 
    chip.write("010255")
    chip.write("010300")
    chip.write("010402")
    chip.write("010500")
    chip.write("0106F0")
    chip.write("010711")
    chip.write("010803") # dclkout2 3div 1000MHz
    chip.write("010955")
    chip.write("010A55")
    chip.write("010B00")
    chip.write("010C22")
    chip.write("010D00")
    chip.write("010EF0")
    chip.write("010F11")
    chip.write("01100C") # dclkout4 12div 250MHz
    chip.write("011155")
    chip.write("011255")
    chip.write("011300")
    chip.write("011422")
    chip.write("011500")
    chip.write("0116F0")
    chip.write("011711")
    chip.write("011803") # dclkout6 3div 1000MHz
    chip.write("011955")
    chip.write("011A55")
    chip.write("011B00")
    chip.write("011C22")
    chip.write("011D00")
    chip.write("011EF0")
    chip.write("011F11")
    chip.write("01200C")# dclkout8 12div 250MHz
    chip.write("012155")
    chip.write("012255")
    chip.write("012300")
    chip.write("012402") # channel 9, adc sysref to fpga, 3.90625MHz
    chip.write("012500")
    chip.write("0126F0")
    chip.write("012711")
    chip.write("012803")# dclkout10 3div 1000MHz
    chip.write("012955")
    chip.write("012A55")
    chip.write("012B00")
    chip.write("012C22")
    chip.write("012D00")
    chip.write("012EF0")
    chip.write("012F11") 
    chip.write("01300C")# dclkout12 12div 250MHz
    chip.write("013155")
    chip.write("013255")
    chip.write("013300")
    chip.write("013402")
    chip.write("013500")
    chip.write("0136F0")
    chip.write("013711")
    chip.write("013821")
    chip.write("013903")
    chip.write("013A06") #[4:0] sysref_div[12:8]
    chip.write("013B00") #sysref_div[7:0]
    chip.write("013C00")
    chip.write("013D08")
    chip.write("013E03") # 
    chip.write("013F01") # 
    chip.write("014002") # 
    chip.write("014100") # 
    chip.write("014200") # 
    chip.write("014311") # 
    chip.write("0144FF") # 
    chip.write("01457F") # 
    chip.write("01461B") #  
    chip.write("01471A") #  CLKin_SEL_MODE[6:4] clkin1
    chip.write("014882") #  
    chip.write("014902")
    chip.write("014A33")
    chip.write("014B16")
    chip.write("014C00")
    chip.write("014D00")
    chip.write("014EC0") # 
    chip.write("014F7F") # 
    chip.write("015003") # 
    chip.write("015101") # 
    chip.write("015200") # 
    chip.write("015300") # 
    chip.write("015401") # 
    chip.write("015500") # 
    chip.write("015601") #  
    chip.write("015700") #  
    chip.write("015801") #  	
    chip.write("015900")
    chip.write("015A0A")
    chip.write("015BD4")
    chip.write("015C20")
    chip.write("015D00")
    chip.write("015E00") # 
    chip.write("015F0B") # 
    chip.write("016000") # 
    chip.write("016164") # 
    chip.write("016244") # 
    chip.write("016300") # 
    chip.write("016400") # 
    chip.write("01650C") # 
    chip.write("0171AA") #  
    chip.write("017202") #  
    chip.write("017C15") #  	
	chip.write("017D33")
    chip.write("016600") #  
    chip.write("016705") #  
    chip.write("0168DC") #  	
    chip.write("016959")
    chip.write("016A20")
    chip.write("016B00")
    chip.write("016C00")
    chip.write("016D00")
    chip.write("016E13")  
    chip.write("017300")  
    chip.write("018200")  
    chip.write("018300")  
    chip.write("018400")  
    chip.write("018500")  
    chip.write("018800")  
    chip.write("018900") 
    chip.write("018A00") 
    chip.write("018B00")  
    chip.write("1FFD00")  
    chip.write("1FFE00")  
    chip.write("1FFF53") 
 
   



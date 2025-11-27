import uart
import bus
import module
import module_signal_router
import spi
from boards import *
from chips import *
from port_numbers import *
import numpy as np
import time

import code

ser = uart.MySerial("COM7", baudrate = 115200, parity = "E", timeout = 0.5)
bus_inst = bus.Bus(ser)
router = module_signal_router.ModuleSignalRouter(bus_inst)
tri = module.ModuleBase(bus_inst, "TRIG")
acc = module.ModuleAccumulator(bus_inst, "ACCM")
sclr = module.ModuleScaler(bus_inst, "SCLR")
sclr2 = module.ModuleScaler(bus_inst, "SCL2")
sclr3 = module.ModuleScaler(bus_inst, "SCL3")
sclr4 = module.ModuleScaler(bus_inst, "SCL4")
pid = module.ModulePID(bus_inst, "PIDC")
fir = module.ModuleFIRFilter(bus_inst, "FIRF")
fir2 = module.ModuleFIRFilter(bus_inst, "FIR2")
mixer = module.ModuleBase(bus_inst, "MIXR")
tri2 = module.ModuleBase(bus_inst, "TRI2")
acc2 = module.ModuleAccumulator(bus_inst, "ACC2")
pid2 = module.ModulePID(bus_inst, "PID2")
ltrn = module.ModuleLinearTransformer(bus_inst, "LTRN")
ltrn2 = module.ModuleLinearTransformer(bus_inst, "LTR2")
mixer3 = module.ModuleBase(bus_inst, "MIX3")
mixer4 = module.ModuleBase(bus_inst, "MIX4")
fir3 = module.ModuleFIRFilter(bus_inst, "FIR3")
fir4 = module.ModuleFIRFilter(bus_inst, "FIR4")
pdhfsm = module.ModulePDHFSM(bus_inst, "PDHS")
spi_inst = spi.Spi(ser)

def init():
    try:
        print("Reset modules")
        router.reset()
        tri.reset()
        acc.reset()
        sclr.reset()
        sclr2.reset()
        sclr3.reset()
        sclr4.reset()
        fir.reset()
        mixer.reset()
        pid.reset()
        fir2.reset()
        tri2.reset()
        acc2.reset()
        pid2.reset()
        ltrn.reset()
        ltrn2.reset()
        mixer3.reset()
        mixer4.reset()
        fir3.reset()
        fir4.reset()
        pdhfsm.reset()

        print("Configure converters")
        init_FL9627(spi_inst, 1)
        init_FH8052_ext_ref(spi_inst, 3)
    except Exception as e:
        print("Error during initialization:", e)
    return

def init_no_ref():
    try:
        print("Reset modules")
        router.reset()
        tri.reset()
        acc.reset()
        sclr.reset()
        sclr2.reset()
        sclr3.reset()
        sclr4.reset()
        fir.reset()
        mixer.reset()
        pid.reset()
        fir2.reset()
        tri2.reset()
        acc2.reset()
        pid2.reset()
        ltrn.reset()
        ltrn2.reset()
        mixer3.reset()
        mixer4.reset()
        fir3.reset()
        fir4.reset()
        pdhfsm.reset()

        print("Configure converters")
        init_FL9627(spi_inst, 1)
        init_FH8052(spi_inst, 3)
    except Exception as e:
        print("Error during initialization:", e)
    return

def setup_pll():
    print("Setup PLL")
    router.set_routing(TRI_IN,ACC_OUT)
    router.set_routing(MIXER_IN_A, INPUT_F)
    router.set_routing(MIXER_IN_B, TRI_SIN)
    router.set_routing(MIXER2_IN_A, INPUT_F)
    router.set_routing(MIXER2_IN_B, TRI_COS)
    router.set_routing(FIR_IN, MIXER_OUT)
    router.set_routing(FIR2_IN, MIXER2_OUT)
    router.set_routing(ATAN_IN_SIN, FIR_OUT)
    router.set_routing(ATAN_IN_COS, FIR2_OUT)
    router.set_routing(UNWRAPPER_IN, ATAN_OUT)
    router.set_routing(PID_IN, UNWRAPPER_OUT)
    router.set_routing(SCALER_IN, PID_OUT)
    router.set_routing(OUTPUT_A, SCALER_OUT)
    router.set_routing(OUTPUT_B, FIR_OUT) # For monitoring
    router.set_routing(OUTPUT_C, ATAN_OUT)
    router.upload()

    print("Write parameters")
    sclr.write("scale", "00010000") # Gain = 1
    pid.write("p", 65536)

def setup_duallock():
    print("Setup dual locking")
    router.set_routing(TRI_IN, ACC_OUT)
    router.set_routing(MIXER_IN_A, INPUT_F)
    router.set_routing(MIXER_IN_B, TRI_SIN)
    router.set_routing(FIR_IN, MIXER_OUT)
    router.set_routing(PID_IN, FIR_OUT)
    router.set_routing(SCALER_IN, PID_OUT)
    router.set_routing(OUTPUT_A, SCALER_OUT)
    router.set_routing(TRI2_IN, ACC2_OUT)
    router.set_routing(MIXER2_IN_A, INPUT_F)
    router.set_routing(MIXER2_IN_B, TRI2_SIN)
    router.set_routing(FIR2_IN, MIXER2_OUT)
    router.set_routing(PID2_IN, FIR2_OUT)
    router.set_routing(SCALER2_IN, PID2_OUT)
    router.set_routing(OUTPUT_B, SCALER2_OUT)
    router.upload()

    print("Write parameters")
    sclr.write("scale", 0) # Disable output until limits are set
    sclr2.write("scale", 0)
    pid.write("p", 65536)
    pid2.write("p", 65536)

def setup_pdh():
    router.set_routing(TRI_IN, ACC_OUT)
    router.set_routing(MIXER_IN_A, TRI_SIN)
    router.set_routing(MIXER_IN_B, INPUT_C)
    router.set_routing(FIR_IN, MIXER_OUT)
    router.set_routing(PID_IN, FIR_OUT)
    router.set_routing(LN_TRANSFORMER_IN_A, PID_OUT)
    router.set_routing(LN_TRANSFORMER_IN_B, ACC2_OUT)
    router.set_routing(SCALER_IN, LN_TRANSFORMER_OUT_A)
    router.set_routing(OUTPUT_B, SCALER_OUT)
    router.set_routing(OUTPUT_C, TRI_SIN)
    router.set_routing(FIR2_IN, INPUT_C)
    router.set_routing(PDHFSM_IN, FIR2_OUT)
    router.set_routing(PID_RESET, PDHFSM_PID_RESET_CTRL)
    router.set_routing(ACC2_PAUSE, PDHFSM_SCAN_RESET_CTRL)
    router.upload()

    print("Write parameters")
    sclr.write("scale", 0) # Disable output until limits are set
    sclr.write("bias", 15000)
    pid.write("auto_reset", 1)
    acc2.write("auto_reset", 1)# 1 by fsm；0 by hand
    ltrn.write("matrix", np.array([[0.5, 0.5], [1, 0]]))
    pdhfsm.write("thre_sig_lock", 7800)
    pdhfsm.write("thre_sig_scan", 32767)
    pdhfsm.write("time_lock", 1000000)
    pdhfsm.write("time_scan", 2**29)

def load_fir():
    print("Load FIR coefficients")
    filename = "fir_coef.txt"
    with open(filename, 'r') as f:
        lines = f.readlines()
    coef = [float(line.strip()) for line in lines]
    coef = np.array(coef)
    coef /= np.max(np.abs(coef)) # Normalize
    coef *= 0.98
    print("Normalized coefficients:", coef)
    l1_norm = sum(np.abs(coef))
    norm = 32 / l1_norm * 0.98
    print("L1 norm:", l1_norm)
    print("Normalization factor:", norm)
    fir.load_coef(coef, norm)
    fir2.load_coef(coef, norm)

if __name__ == "__main__":
    code.interact(local=locals())
import qt_bus
import module
import module_signal_router
import spi
from boards import *
from chips import *
from port_numbers import *
import qt_uart
import numpy as np
import time

import code

class HardwareController:
    def __init__(self, serial_instance=None):
        """
        初始化硬件控制器
        
        Args:
            serial_instance: QtSerial 实例，可选。如果不提供，需要后续调用 set_serial()
        """
        self.ser = None
        self.bus_inst = None
        self.router = None
        self.tri = None
        self.acc = None
        self.sclr = None
        self.sclr2 = None
        self.sclr3 = None
        self.sclr4 = None
        self.pid = None
        self.fir = None
        self.fir2 = None
        self.mixer = None
        self.tri2 = None
        self.acc2 = None
        self.pid2 = None
        self.ltrn = None
        self. ltrn2 = None
        self.mixer3 = None
        self.mixer4 = None
        self. fir3 = None
        self.fir4 = None
        self.pdhfsm = None
        self.spi_inst = None
        self.pdhfsm = None
        self.sclofsm = None
        self.sclofsm2 = None
        self.iir = None
        self.iir2 = None
        self.iir3 = None
        self.iir4 = None
        
        
        if serial_instance is not None:
            self.set_serial(serial_instance)
    
    def set_serial(self, serial_instance):
        """
        设置串口实例并初始化所有模块
        
        Args: 
            serial_instance: QtSerial 实例
        """
        self.ser = serial_instance
        self.bus_inst = qt_bus.Bus(self.ser)
        self.router = module_signal_router.ModuleSignalRouter(self.bus_inst)
        self.tri = module.ModuleBase(self.bus_inst, "TRIG")
        self.acc = module.ModuleAccumulator(self.bus_inst, "ACCM")
        self.sclr = module.ModuleScaler(self.bus_inst, "SCLR")
        self.sclr2 = module.ModuleScaler(self.bus_inst, "SCL2")
        self.sclr3 = module.ModuleScaler(self.bus_inst, "SCL3")
        self.sclr4 = module.ModuleScaler(self.bus_inst, "SCL4")
        self.pid = module.ModulePID(self.bus_inst, "PIDC")
        self.fir = module.ModuleFIRFilter(self.bus_inst, "FIRF")
        self.fir2 = module.ModuleFIRFilter(self.bus_inst, "FIR2")
        self.mixer = module.ModuleBase(self.bus_inst, "MIXR")
        self.tri2 = module.ModuleBase(self.bus_inst, "TRI2")
        self.acc2 = module.ModuleAccumulator(self.bus_inst, "ACC2")
        self.pid2 = module.ModulePID(self.bus_inst, "PID2")
        self.ltrn = module.ModuleLinearTransformer(self.bus_inst, "LTRN")
        self.ltrn2 = module.ModuleLinearTransformer(self.bus_inst, "LTR2")
        self.mixer3 = module.ModuleBase(self.bus_inst, "MIX3")
        self.mixer4 = module.ModuleBase(self.bus_inst, "MIX4")
        self.fir3 = module.ModuleFIRFilter(self.bus_inst, "FIR3")
        self.fir4 = module.ModuleFIRFilter(self.bus_inst, "FIR4")
        self.pdhfsm = module.ModulePDHFSM(self.bus_inst, "PDHS")
        self.sclofsm = module.ModuleSCLOFSM(self.bus_inst, "SCLO")
        self.sclofsm2 = module.ModuleSCLOFSM(self.bus_inst, "SLO2")
        self.iir = module.ModuleIIRFilter(self.bus_inst, "IIRF")
        self.iir2 = module.ModuleIIRFilter(self.bus_inst, "IIR2")
        self.iir3 = module.ModuleIIRFilter(self.bus_inst, "IIR3")
        self.iir4 = module.ModuleIIRFilter(self.bus_inst, "IIR4")
        self.spi_inst = spi.Spi(self.ser)
        

    
    def _check_serial(self):
        """检查串口是否已初始化"""
        if self. ser is None:
            raise Exception("Serial port not initialized.  Call set_serial() first.")
    
    def init(self):
        """初始化所有模块（使用外部参考）"""
        self._check_serial()
        
        try:
            print("Reset modules")
            self.router.reset()
            self.tri.reset()
            self.acc.reset()
            self.sclr.reset()
            self.sclr2.reset()
            self.sclr3.reset()
            self.sclr4.reset()
            self.fir.reset()
            self.mixer.reset()
            self.pid.reset()
            self.fir2.reset()
            self.tri2.reset()
            self.acc2.reset()
            self.pid2.reset()
            self.ltrn.reset()
            self.ltrn2.reset()
            self.mixer3.reset()
            self.mixer4.reset()
            self.fir3.reset()
            self.fir4.reset()
            self.pdhfsm.reset()

            print("Configure converters")
            init_FL9627(self.spi_inst, 1)
            init_FH8052_ext_ref(self.spi_inst, 3)
        except Exception as e:
            print("Error during initialization:", e)
            raise
    
    def init_no_ref(self):
        """初始化所有模块（不使用外部参考）"""
        self._check_serial()
        
        try:
            print("Reset modules")
            self.router. reset()
            self.tri. reset()
            self.acc. reset()
            self.sclr.reset()
            self.sclr2.reset()
            self.sclr3.reset()
            self.sclr4.reset()
            self.fir.reset()
            self.mixer.reset()
            self.pid.reset()
            self.fir2.reset()
            self.tri2.reset()
            self.acc2.reset()
            self.pid2.reset()
            self.ltrn.reset()
            self.ltrn2.reset()
            self.mixer3.reset()
            self.mixer4.reset()
            self.fir3.reset()
            self.fir4.reset()
            self.pdhfsm.reset()

            print("Configure converters")
            init_FL9627(self.spi_inst, 1)
            init_FH8052(self.spi_inst, 3)
        except Exception as e:
            print("Error during initialization:", e)
            raise
    
    def setup_pll(self):
        """配置 PLL"""
        self._check_serial()
        
        print("Setup PLL")
        self.router.set_routing(TRI_IN, ACC_SLOW_OUT)
        self.router. set_routing(MIXER_IN_A, INPUT_F)
        self.router.set_routing(MIXER_IN_B, TRI_SIN)
        self.router. set_routing(MIXER2_IN_A, INPUT_F)
        self.router.set_routing(MIXER2_IN_B, TRI_COS)
        self.router. set_routing(FIR_IN, MIXER_OUT)
        self.router.set_routing(FIR2_IN, MIXER2_OUT)
        self.router.set_routing(ATAN_IN_SIN, FIR_OUT)
        self.router.set_routing(ATAN_IN_COS, FIR2_OUT)
        self.router.set_routing(UNWRAPPER_IN, ATAN_OUT)
        self.router.set_routing(PID_IN, UNWRAPPER_OUT)
        self.router.set_routing(SCALER_IN, PID_OUT)
        self.router.set_routing(OUTPUT_A, SCALER_OUT)
        self.router.set_routing(OUTPUT_B, FIR_OUT)  # For monitoring
        self.router.set_routing(OUTPUT_C, ATAN_OUT)
        self.router.upload()

        print("Write parameters")
        self.sclr.write("scale", "00010000")  # Gain = 1
        self.pid.write("p", 65536)
    
    def setup_duallock(self):
        """配置双锁定"""
        self._check_serial()
        
        print("Setup dual locking")
        self.router. set_routing(TRI_IN, ACC_SLOW_OUT)
        self.router.set_routing(MIXER_IN_A, INPUT_F)
        self.router.set_routing(MIXER_IN_B, TRI_SIN)
        self.router.set_routing(FIR_IN, MIXER_OUT)
        self.router. set_routing(PID_IN, FIR_OUT)
        self.router. set_routing(SCALER_IN, PID_OUT)
        self.router. set_routing(OUTPUT_A, SCALER_OUT)
        self.router.set_routing(TRI2_IN, ACC2_SLOW_OUT)
        self.router.set_routing(MIXER2_IN_A, INPUT_F)
        self.router.set_routing(MIXER2_IN_B, TRI2_SIN)
        self.router. set_routing(FIR2_IN, MIXER2_OUT)
        self.router.set_routing(PID2_IN, FIR2_OUT)
        self.router.set_routing(SCALER2_IN, PID2_OUT)
        self.router.set_routing(OUTPUT_B, SCALER2_OUT)
        self.router.upload()

        print("Write parameters")
        self.sclr. write("scale", 0)  # Disable output until limits are set
        self.sclr2.write("scale", 0)
        self.pid.write("p", 65536)
        self.pid2.write("p", 65536)
    
    def setup_pdh(self):
        """配置 PDH"""
        self._check_serial()
        
        self.router.set_routing(TRI_IN, ACC_SLOW_OUT)
        self.router.set_routing(MIXER_IN_A, TRI_SIN)
        self.router.set_routing(MIXER_IN_B, INPUT_C)
        self.router.set_routing(FIR_IN, MIXER_OUT)
        self.router.set_routing(PID_IN, FIR_OUT)
        self.router.set_routing(LN_TRANSFORMER_IN_A, PID_OUT)
        self.router.set_routing(LN_TRANSFORMER_IN_B, ACC2_SLOW_OUT)
        self.router.set_routing(SCALER_IN, LN_TRANSFORMER_OUT_A)
        self.router.set_routing(OUTPUT_B, SCALER_OUT)
        self.router.set_routing(OUTPUT_C, TRI_SIN)
        self.router.set_routing(FIR2_IN, INPUT_C)
        self.router.set_routing(PDHFSM_IN_POWER, FIR2_OUT)
        self.router.set_routing(PDHFSM_IN_SCAN, ACC2_SLOW_OUT)
        self.router.set_routing(PID_RESET, PDHFSM_PID_RESET_CTRL)
        self.router.set_routing(ACC2_PAUSE, PDHFSM_SCAN_RESET_CTRL)
        self.router.upload()

        print("Write parameters")
        self.sclr.write("scale", 0)  # Disable output until limits are set
        self.sclr. write("bias", 15000)
        self.pid.write("auto_reset", 1)
        self.acc2.write("auto_reset", 1)  # 1 by fsm；0 by hand
        self. ltrn.write("matrix", np.array([[0.5, 0.5], [1, 0]]))
        self.pdhfsm.write("thre_sig_lock", 7800)
        self.pdhfsm.write("thre_sig_scan", 32767)
        self.pdhfsm.write("time_lock", 1000000)
        self.pdhfsm.write("time_scan", 2**29)
    
    def setup_sclo(self):
        self.router.set_routing(MIXER_IN_A, INPUT_F)
        self.router.set_routing(MIXER_IN_B, TRI_SIN)
        self.router.set_routing(MIXER2_IN_A, INPUT_F)
        self.router.set_routing(MIXER2_IN_B, TRI_COS)
        self.router.set_routing(FIR_IN, MIXER_OUT)
        self.router.set_routing(FIR2_IN, MIXER2_OUT)
        self.router.set_routing(ATAN_IN_SIN, FIR_OUT)
        self.router.set_routing(ATAN_IN_COS, FIR2_OUT)
        self.router.set_routing(SCLOFSM_PHASE_IN, ATAN_OUT)
        self.router.set_routing(ACC_BIAS_IN, SCLOFSM_BIAS_OUT)
        self.router.set_routing(TRI_IN, ACC_FAST_OUT)
        self.router.set_routing(PID_IN, FIR_OUT)
        self.router.set_routing(PID_RESET, SCLOFSM_PID_RESET_CTRL)
        self.router.set_routing(SCALER_IN, PID_OUT)
        self.router.set_routing(OUTPUT_A, SCALER_OUT)
        self.router.upload()
        self.sclofsm.flip_on("clear")
    
    def load_fir(self, filename="fir_coef.txt"):
        """
        加载 FIR 滤波器系数
        
        Args:
            filename: 系数文件路径，默认为 "fir_coef.txt"
        """
        self._check_serial()
        
        print("Load FIR coefficients")
        with open(filename, 'r') as f:
            lines = f.readlines()
        coef = [float(line.strip()) for line in lines]
        coef = np.array(coef)
        coef /= np.max(np.abs(coef))  # Normalize
        coef *= 0.98
        print("Normalized coefficients:", coef)
        l1_norm = sum(np. abs(coef))
        norm = 32 / l1_norm * 0.98
        print("L1 norm:", l1_norm)
        print("Normalization factor:", norm)
        self.fir.load_coef(coef, norm)
        self.fir2.load_coef(coef, norm)
    
    def is_initialized(self):
        """检查是否已初始化串口"""
        return self.ser is not None




if __name__ == "__main__": 
    # 交互式模式
    controller = HardwareController()
    code.interact(local=locals())
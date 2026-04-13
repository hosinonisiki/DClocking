from qt_Port import Port
import port_numbers as pn


def ensure_port_methods():
    if hasattr(Port, "write_bus"):
        return

    def is_open(self):
        return self.serial_port.isOpen()

    def write_bus(self, module, address, data, hold=False):
        if not self.serial_port or not self.serial_port.isOpen():
            raise RuntimeError("Serial port is not open")
        module = module.upper()
        if isinstance(address, int):
            address = address.to_bytes(4, "big")
        elif isinstance(address, str):
            address = bytes.fromhex(address).rjust(4, b"\x00")
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        elif isinstance(data, str):
            data = bytes.fromhex(data).rjust(4, b"\x00")
        message = b":BUS_." + module.encode() + b".WRTE.ADDR." + address + b".DATA." + data
        if hold:
            message += b".HOLD!"
        else:
            message += b"!"
        self.serial_port.write(message)

    Port.is_open = is_open
    Port.write_bus = write_bus


def border_port_index(name, prefix):
    if not name.startswith(prefix):
        return None
    try:
        return int(name[len(prefix):])
    except ValueError:
        return None


def resolve_port_number(node_name, port_index, role):
    if node_name.startswith("HIGH"):
        outputs = [pn.HIGH]
        return outputs[port_index] if role == "out" and 0 <= port_index < len(outputs) else None
    if node_name.startswith("LOW"):
        outputs = [pn.LOW]
        return outputs[port_index] if role == "out" and 0 <= port_index < len(outputs) else None

    if node_name == "Border_out_HIGH":
        return pn.HIGH if role == "out" else None
    if node_name == "Border_out_LOW":
        return pn.LOW if role == "out" else None

    border_out_idx = border_port_index(node_name, "Border_out_")
    if border_out_idx is not None:
        inputs = [pn.INPUT_A, pn.INPUT_B, pn.INPUT_C, pn.INPUT_D, pn.INPUT_E, pn.INPUT_F, pn.INPUT_G, pn.INPUT_H]
        return inputs[border_out_idx] if 0 <= border_out_idx < len(inputs) and role == "out" else None

    border_in_idx = border_port_index(node_name, "Border_in_")
    if border_in_idx is not None:
        outputs = [pn.OUTPUT_A, pn.OUTPUT_B, pn.OUTPUT_C, pn.OUTPUT_D, pn.OUTPUT_E, pn.OUTPUT_F, pn.OUTPUT_G, pn.OUTPUT_H]
        return outputs[border_in_idx] if 0 <= border_in_idx < len(outputs) and role == "in" else None

    match node_name:
        case "PIDC" | "PID":
            inputs = [pn.PID_RESET, pn.PID_IN]
            outputs = [pn.PID_OUT]
        case "PID2":
            inputs = [pn.PID2_RESET, pn.PID2_IN]
            outputs = [pn.PID2_OUT]
        case "ACCM":
            inputs = {0: pn.ACC_ERROR_IN, 1: pn.ACC_BIAS_IN, 2: pn.ACC_RESET, 3: pn.ACC_PAUSE, 4: pn.ACC_LF_RESET}
            outputs = {0: pn.ACC_SLOW_OUT, 1: pn.ACC_FAST_OUT}
        case "ACC2":
            inputs = {0: pn.ACC2_ERROR_IN, 1: pn.ACC2_BIAS_IN, 2: pn.ACC2_RESET, 3: pn.ACC2_PAUSE, 4: pn.ACC2_LF_RESET}
            outputs = {0: pn.ACC2_SLOW_OUT, 1: pn.ACC2_FAST_OUT}
        case "SCLR":
            inputs = [pn.SCALER_IN]
            outputs = [pn.SCALER_OUT]
        case "SCL2":
            inputs = [pn.SCALER2_IN]
            outputs = [pn.SCALER2_OUT]
        case "SCL3":
            inputs = [pn.SCALER3_IN]
            outputs = [pn.SCALER3_OUT]
        case "SCL4":
            inputs = [pn.SCALER4_IN]
            outputs = [pn.SCALER4_OUT]
        case "FIRF":
            inputs = [pn.FIR_IN]
            outputs = [pn.FIR_OUT]
        case "FIR2":
            inputs = [pn.FIR2_IN]
            outputs = [pn.FIR2_OUT]
        case "FIR3":
            inputs = [pn.FIR3_IN]
            outputs = [pn.FIR3_OUT]
        case "FIR4":
            inputs = [pn.FIR4_IN]
            outputs = [pn.FIR4_OUT]
        case "IIRF":
            inputs = [pn.IIR_IN]
            outputs = [pn.IIR_OUT]
        case "IIR2":
            inputs = [pn.IIR2_IN]
            outputs = [pn.IIR2_OUT]
        case "IIR3":
            inputs = [pn.IIR3_IN]
            outputs = [pn.IIR3_OUT]
        case "IIR4":
            inputs = [pn.IIR4_IN]
            outputs = [pn.IIR4_OUT]
        case "MIXR":
            inputs = [pn.MIXER_IN_A, pn.MIXER_IN_B]
            outputs = [pn.MIXER_OUT]
        case "MIX2":
            inputs = [pn.MIXER2_IN_A, pn.MIXER2_IN_B]
            outputs = [pn.MIXER2_OUT]
        case "MIX3":
            inputs = [pn.MIXER3_IN_A, pn.MIXER3_IN_B]
            outputs = [pn.MIXER3_OUT]
        case "MIX4":
            inputs = [pn.MIXER4_IN_A, pn.MIXER4_IN_B]
            outputs = [pn.MIXER4_OUT]
        case "TRIG":
            inputs = [pn.TRI_IN]
            outputs = [pn.TRI_SIN, pn.TRI_COS]
        case "TRI2":
            inputs = [pn.TRI2_IN]
            outputs = [pn.TRI2_SIN, pn.TRI2_COS]
        case "TRI3":
            inputs = [pn.TRI3_IN]
            outputs = [pn.TRI3_SIN, pn.TRI3_COS]
        case "TRI4":
            inputs = [pn.TRI4_IN]
            outputs = [pn.TRI4_SIN, pn.TRI4_COS]
        case "ATAN":
            inputs = [pn.ATAN_IN_SIN, pn.ATAN_IN_COS]
            outputs = [pn.ATAN_OUT]
        case "ATA2":
            inputs = [pn.ATAN2_IN_SIN, pn.ATAN2_IN_COS]
            outputs = [pn.ATAN2_OUT]
        case "UNWR":
            inputs = [pn.UNWRAPPER_IN]
            outputs = [pn.UNWRAPPER_OUT]
        case "LTRN":
            inputs = [pn.LN_TRANSFORMER_IN_A, pn.LN_TRANSFORMER_IN_B]
            outputs = [pn.LN_TRANSFORMER_OUT_A, pn.LN_TRANSFORMER_OUT_B]
        case "LTR2":
            inputs = [pn.LN_TRANSFORMER2_IN_A, pn.LN_TRANSFORMER2_IN_B]
            outputs = [pn.LN_TRANSFORMER2_OUT_A, pn.LN_TRANSFORMER2_OUT_B]
        case "PDHS":
            inputs = [pn.PDHFSM_IN_POWER, pn.PDHFSM_IN_SCAN]
            outputs = [pn.PDHFSM_PID_RESET_CTRL, pn.PDHFSM_MIXER_RESET_CTRL, pn.PDHFSM_SCAN_RESET_CTRL]
        case "SCLO":
            inputs = [pn.SCLOFSM_PHASE_IN]
            outputs = [pn.SCLOFSM_BIAS_OUT, pn.SCLOFSM_PID_RESET_CTRL]
        case "SLO2":
            inputs = [pn.SCLOFSM2_PHASE_IN]
            outputs = [pn.SCLOFSM2_BIAS_OUT, pn.SCLOFSM2_PID_RESET_CTRL]
        case _:
            return None

    if isinstance(inputs, dict):
        return inputs.get(port_index) if role == "in" else outputs.get(port_index)
    if role == "in":
        return inputs[port_index] if 0 <= port_index < len(inputs) else None
    return outputs[port_index] if 0 <= port_index < len(outputs) else None


def candidate_node_names():
    names = []
    names.extend(["HIGH1", "LOW1"])
    names.extend([f"Border_out_{i}" for i in range(8)])
    names.extend([f"Border_in_{i}" for i in range(8)])
    names.extend(["Border_out_HIGH", "Border_out_LOW"])
    names.extend(["PIDC", "PID2", "ACCM", "ACC2", "SCLR", "SCL2", "SCL3", "SCL4"])
    names.extend(["FIRF", "FIR2", "FIR3", "FIR4", "IIRF", "IIR2", "IIR3", "IIR4"])
    names.extend(["TRIG", "TRI2", "TRI3", "TRI4", "ATAN", "ATA2"])
    names.extend(["MIXR", "MIX2", "MIX3", "MIX4", "UNWR", "LTRN", "LTR2", "PDHS", "SCLO", "SLO2"])
    return names


def resolve_node_port_from_number(port_num, role):
    for node_name in candidate_node_names():
        for idx in range(8):
            try:
                mapped = resolve_port_number(node_name, idx, role)
            except Exception:
                mapped = None
            if mapped == port_num:
                return node_name, idx
    return None, None


def node_name_to_component(node_name):
    if node_name.startswith("HIGH"):
        suffix = node_name[4:]
        if suffix.isdigit():
            return "布尔值：是", int(suffix) - 1
        return "布尔值：是", 0
    if node_name.startswith("LOW"):
        suffix = node_name[3:]
        if suffix.isdigit():
            return "布尔值：否", int(suffix) - 1
        return "布尔值：否", 0

    if node_name in ("PIDC", "PID"):
        return "PID控制器", 0
    if node_name.startswith("PID") and node_name[3:].isdigit():
        return "PID控制器", int(node_name[3:]) - 1
    if node_name == "ACCM":
        return "累加器", 0
    if node_name.startswith("ACC") and node_name[3:].isdigit():
        return "累加器", int(node_name[3:]) - 1
    if node_name == "SCLR":
        return "线性缩放器", 0
    if node_name.startswith("SCL") and node_name[3:].isdigit():
        return "线性缩放器", int(node_name[3:]) - 1
    if node_name == "FIRF":
        return "FIR滤波器", 0
    if node_name.startswith("FIR") and node_name[3:].isdigit():
        return "FIR滤波器", int(node_name[3:]) - 1
    if node_name == "IIRF":
        return "IIR滤波器", 0
    if node_name.startswith("IIR") and node_name[3:].isdigit():
        return "IIR滤波器", int(node_name[3:]) - 1
    if node_name == "TRIG":
        return "三角函数运算器", 0
    if node_name.startswith("TRI") and node_name[3:].isdigit():
        return "三角函数运算器", int(node_name[3:]) - 1
    if node_name == "ATAN":
        return "反三角函数运算器", 0
    if node_name.startswith("ATA") and node_name[3:].isdigit():
        return "反三角函数运算器", int(node_name[3:]) - 1
    if node_name == "MIXR":
        return "混频器", 0
    if node_name.startswith("MIX") and node_name[3:].isdigit():
        return "混频器", int(node_name[3:]) - 1
    if node_name == "UNWR":
        return "解卷绕器", 0
    if node_name == "LTRN":
        return "线性变换器", 0
    if node_name == "LTR2":
        return "线性变换器", 1
    if node_name == "PDHS":
        return "PDH状态机", 0
    if node_name == "SCLO":
        return "LO自动校准状态机", 0
    if node_name == "SLO2":
        return "LO自动校准状态机", 1
    return None, None

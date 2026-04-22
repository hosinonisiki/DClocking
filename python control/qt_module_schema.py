PID_SCHEMA = [
    # 直接参数
    {"key" : "gain_p", "label" : "P通道增益系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : True, "note" : "线性增益系数。取对数后才可转换为分贝值。可通过间接参数直接设定分贝值"},
    {"key" : "gain_i", "label" : "I通道增益系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : True, "note" : "线性增益系数。取对数后才可转换为分贝值。可通过间接参数直接设定分贝值"},
    {"key" : "gain_d", "label" : "D通道增益系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : True, "note" : "线性增益系数。取对数后才可转换为分贝值。可通过间接参数直接设定分贝值"},
    {"key" : "setpoint", "label" : "设定值", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "limit_integral", "label" : "积分限幅值", "type" : "int", "min" : 0, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "limit_sum", "label" : "输出限幅值", "type" : "int", "min" : 0, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "leak_digit", "label" : "积分泄露控制参数", "type" : "int", "min" : 0, "max" : 2**23, "mode" : "direct", "free" : False, "note" : "仅推荐通过间接参数修改"},
    {"key" : "enable_auto_reset", "label" : "自动控制使能", "type" : "bool", "mode" : "direct", "free" : True, "note" : "设为1时，模块接受其它状态机模块的开关指令。设为0时，开关指令被忽略"},

    # 间接参数
    {"key" : "overall_gain", "label" : "整体增益", "type" : "float", "min" : -1e6, "max" : 1e6, "unit" : "dB", "mode" : "indirect", "free" : True, "note" : "调节P通道增益，并等比例缩放I、D通道增益。若缩放后任一通道增益超出范围则报错。若初始P通道增益为0（缩放比例为无穷大），则仅调节P通道增益"},
    {"key" : "pi_corner", "label" : "PI交点频率", "type" : "float", "min" : 0.0, "max" : 1e9, "unit" : "Hz", "mode" : "indirect", "free" : True, "note" : "调节I通道增益。使得PI增益曲线交点位于指定频率。若调节后I通道增益超出范围则报错"},
    {"key" : "pd_corner", "label" : "PD交点频率", "type" : "float", "min" : 0.0, "max" : 1e9, "unit" : "Hz", "mode" : "indirect", "free" : True, "note" : "调节D通道增益。使得PD增益曲线交点位于指定频率。若调节后D通道增益超出范围则报错"},
    {"key" : "saturation_gain", "label" : "饱和增益", "type" : "float", "min" : -1e6, "max" : 1e6, "unit" : "dB", "mode" : "indirect", "free" : True, "note" : "调节泄漏系数，使得积分通道在设定增益处饱和。若饱和增益过大，则设定为无饱和。若饱和增益过小，则设定为最大泄漏。若I通道增益为0，则报错"},
    {"key" : "saturation_turning_frequency", "label" : "饱和拐点频率", "type" : "float", "min" : 0, "max" : 1e9, "unit" : "Hz", "mode" : "indirect", "free" : True, "note" : "调节泄漏系数，使得积分通道在设定频率处饱和。若饱和频率过小或为0，则设定为无饱和。若饱和频率过大，则设定为最大泄漏"},
]

ACCM_SCHEMA = [
    # 直接参数
    {"key" : "low", "label" : "每周期慢变累加值低32位", "mode" : "direct", "free" : False, "note" : "与high组成64位累加值"},
    {"key" : "high", "label" : "每周期慢变累加值高32位", "mode" : "direct", "free" : False, "note" : "仅推荐通过间接参数修改"},
    {"key" : "divisor", "label" : "快变累加值与慢变累加值的频率之比", "mode" : "direct", "free" : False, "note" : "仅接受2的幂次，从高位起依次检测每位是否为1。仅推荐通过间接参数修改"},
    {"key" : "lf_kp", "label" : "环路滤波器P通道增益系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "线性增益系数。取对数后才可转换为分贝值。涉及锁相环性能，不推荐修改"},
    {"key" : "lf_ki", "label" : "环路滤波器I通道增益系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "线性增益系数。取对数后才可转换为分贝值。涉及锁相环性能，不推荐修改"},
    {"key" : "enable_auto_reset", "label" : "自动控制使能", "type" : "bool", "mode" : "direct", "free" : False, "note" : "设为1时，模块接受其它状态机模块的开关指令。设为0时，开关指令被忽略"},

    # 间接参数
    {"key" : "freq", "label" : "频率", "type" : "float", "min" : 0, "max" : 1e9, "unit" : "Hz", "mode" : "indirect", "free" : True, "note" : "调节慢变累加器的频率，使得快变累加器输出指定频率的锯齿波"},
    {"key" : "ratio", "label" : "频率比", "type" : "int", "min" : 2**0, "max" : 2**15, "mode" : "indirect", "free" : True, "note" : "同时调节慢变累加器的频率和divisor，使得在快变累加器频率不变的前提下达到指定频率比"},
]

SCLR_SCHEMA = [
    # 直接参数
    {"key" : "scale", "label" : "缩放系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : True, "note" : "线性增益系数。取对数后才可转换为分贝值。可通过间接参数直接设定分贝值"},
    {"key" : "bias", "label" : "偏置量", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "upper_limit", "label" : "输出上限", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "lower_limit", "label" : "输出下限", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号"},
    {"key" : "enable_wrapping", "label" : "环绕使能", "type" : "bool", "mode" : "direct", "free" : True, "note" : "设为1时，输出信号无视上下限，并在达到16位物理信号最大表示范围时环绕。设为0时，输出信号受上下限限制"},

    # 间接参数
    {"key" : "gain", "label" : "增益", "type" : "float", "min" : -1e6, "max" : 1e6, "unit" : "dB", "mode" : "indirect", "free" : True, "note" : "调节缩放系数。若所要求系数超出范围则报错"},
]

FIRF_SCHEMA = [
    # 直接参数
    {"key" : "coef_0", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_1", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_2", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_3", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_4", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_5", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_6", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_7", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_8", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_9", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_10", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_11", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_12", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_13", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_14", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_15", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_16", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_17", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_18", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_19", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_20", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_21", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_22", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_23", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_24", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_25", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_26", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_27", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_28", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_29", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_30", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_31", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_32", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_33", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_34", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_35", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_36", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_37", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_38", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_39", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_40", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_41", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_42", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_43", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_44", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_45", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_46", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_47", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_48", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_49", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_50", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_51", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_52", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_53", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_54", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_55", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_56", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_57", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_58", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_59", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_60", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_61", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_62", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "coef_63", "label" : "滤波器系数", "type" : "int", "min" : -(2**23), "max" : 2**23 - 1, "mode" : "direct", "free" : False, "note" : "滤波器的冲激响应，共64个抽头，仅推荐通过专用方法修改"},
    {"key" : "norm_64", "label" : "归一化系数", "type" : "int", "min" : 0, "max" : 262143, "mode" : "direct", "free" : False, "note" : "用于归一化滤波器输出，仅推荐通过专用方法修改"},
    {"key" : "norm_32", "label" : "归一化系数", "type" : "int", "min" : 0, "max" : 262143, "mode" : "direct", "free" : False, "note" : "用于归一化滤波器输出，仅推荐通过专用方法修改"},
    {"key" : "norm_16", "label" : "归一化系数", "type" : "int", "min" : 0, "max" : 262143, "mode" : "direct", "free" : False, "note" : "用于归一化滤波器输出，仅推荐通过专用方法修改"},
    {"key" : "taps", "label" : "滤波器抽头数", "type" : "int", "mode" : "direct", "free" : False, "note" : "15表示16抽头，31表示32抽头，63表示64抽头，仅推荐通过专用方法修改"}
]

LTRN_SCHEMA = [
    # 直接参数
    {"key" : "coef_aa", "label" : "变换矩阵元素AA", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : False, "note" : "输出A对输入A的线性变换系数，仅推荐通过间接参数修改"},
    {"key" : "coef_ab", "label" : "变换矩阵元素AA", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : False, "note" : "输出A对输入B的线性变换系数，仅推荐通过间接参数修改"},
    {"key" : "coef_ba", "label" : "变换矩阵元素AA", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : False, "note" : "输出B对输入A的线性变换系数，仅推荐通过间接参数修改"},
    {"key" : "coef_bb", "label" : "变换矩阵元素AA", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : False, "note" : "输出B对输入B的线性变换系数，仅推荐通过间接参数修改"},

    # 间接参数
    {"key" : "a00", "label" : "变换矩阵元素00", "type" : "float", "min" : -1.0, "max" : 1.0, "mode" : "indirect", "free" : True, "note" : "若线性变换后结果超出16位物理信号范围则自动饱和"},
    {"key" : "a01", "label" : "变换矩阵元素01", "type" : "float", "min" : -1.0, "max" : 1.0, "mode" : "indirect", "free" : True, "note" : ""},
    {"key" : "a10", "label" : "变换矩阵元素10", "type" : "float", "min" : -1.0, "max" : 1.0, "mode" : "indirect", "free" : True, "note" : ""},
    {"key" : "a11", "label" : "变换矩阵元素11", "type" : "float", "min" : -1.0, "max" : 1.0, "mode" : "indirect", "free" : True, "note" : ""},
    {"key" : "matrix", "label" : "变换矩阵"}
]

PDH_SCHEMA = [
    # 直接参数
    {"key" : "pc_cmd", "label" : "工作模式指令", "type" : "int", "min" : 0, "max" : 3, "mode" : "direct", "free" : True, "note" : "00:空闲/复位, 01:手动扫描, 10:自动校准, 11:自动锁定退出"},
    {"key" : "threshold_signal_lock", "label" : "手动锁定阈值", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号。退出锁定状态的振幅阈值"},
    {"key" : "threshold_signal_scan", "label" : "手动扫描阈值", "type" : "int", "min" : -32768, "max" : 32767, "display_voltage" : True, "mode" : "direct", "free" : True, "note" : "物理信号。从扫描状态切换为锁定状态的振幅阈值"},
    {"key" : "time_scan", "label" : "手动扫描确认时间", "type" : "int", "min" : 0, "max" : 2**31 - 1, "unit" : "clk", "prefix" : False, "mode" : "direct", "free" : True, "note" : "单位为时钟周期。从扫描状态切换为锁定状态的时间阈值"},
    {"key" : "time_lock", "label" : "手动锁定超时时间", "type" : "int", "min" : 0, "max" : 2**31 - 1, "unit" : "clk", "prefix" : False, "mode" : "direct", "free" : True, "note" : "单位为时钟周期。退出锁定状态的时间阈值"},
    {"key" : "coef_scan", "label" : "自动扫描系数", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : True, "note" : "	Q1.15格式定点数。用于自动计算扫描阈值比例，32767为1.0，16384为0.5"},
    {"key" : "coef_lock", "label" : "自动锁定系数", "type" : "int", "min" : -32768, "max" : 32767, "mode" : "direct", "free" : True, "note" : "	Q1.15格式定点数。用于自动计算锁定阈值比例，同上"}    
]

SCLO_SCHEMA = [
    # 直接参数
    {"key" : "lock", "label" : "锁定指令", "type" : "bool", "mode" : "direct", "free" : True, "ui_control" : "flip_toggle", "flip_on" : "lock", "flip_off" : "lock", "note" : "粘滞按键。按下触发flip_on，弹起触发flip_off。上升沿时更新校准值并打开PID；下降沿时关闭PID"},
    {"key" : "clear", "label" : "清除指令", "type" : "bool", "mode" : "direct", "free" : True, "ui_control" : "flip_pulse", "flip_on" : "clear", "note" : "瞬时按键。每次点击仅触发一次flip_on，上升沿时清除校准值为0"}
]

# 在文件末尾添加
IIR_SCHEMA = [
    # 直接参数
    {"key": "coef_bq1_b0", "label": "第一二阶节b0系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b1", "label": "第一二阶节b1系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b2", "label": "第一二阶节b2系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b3", "label": "第一二阶节b3系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b4", "label": "第一二阶节b4系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b5", "label": "第一二阶节b5系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b6", "label": "第一二阶节b6系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b7", "label": "第一二阶节b7系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_b8", "label": "第一二阶节b8系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_a4", "label": "第一二阶节a4系数", "type": "int", "min": -(2**25), "max": 2**25 - 1, "mode": "direct", "free": False, "note": "Q2.25格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq1_a8", "label": "第一二阶节a8系数", "type": "int", "min": -(2**25), "max": 2**25 - 1, "mode": "direct", "free": False, "note": "Q2.25格式，仅推荐通过专用方法修改"},
    
    {"key": "coef_bq2_b0", "label": "第二二阶节b0系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b1", "label": "第二二阶节b1系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b2", "label": "第二二阶节b2系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b3", "label": "第二二阶节b3系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b4", "label": "第二二阶节b4系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b5", "label": "第二二阶节b5系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b6", "label": "第二二阶节b6系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b7", "label": "第二二阶节b7系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_b8", "label": "第二二阶节b8系数", "type": "int", "min": -(2**26), "max": 2**26 - 1, "mode": "direct", "free": False, "note": "Q3.24格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_a4", "label": "第二二阶节a4系数", "type": "int", "min": -(2**25), "max": 2**25 - 1, "mode": "direct", "free": False, "note": "Q2.25格式，仅推荐通过专用方法修改"},
    {"key": "coef_bq2_a8", "label": "第二二阶节a8系数", "type": "int", "min": -(2**25), "max": 2**25 - 1, "mode": "direct", "free": False, "note": "Q2.25格式，仅推荐通过专用方法修改"},
]

# -*- coding: utf-8 -*-
import time

from PySide6.QtCore import  QTimer, Qt, QPoint,QEvent,QObject 
import PySide6.QtWidgets as qw
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from qt_uart import QtSerial
from qt_env import HardwareController
class Port(QObject):
    def __init__(self, parent, serial_port):
        super().__init__(parent)	#必须调用父类构造函数,QObject 的子类必须显式调用父类的 __init__，否则会导致对象初始化不完整。
        self.parent = parent
        self.serial_port = serial_port
        self.qt_serial=None
        self.hw_controller = HardwareController()
        # 创建自适应高度的列表窗口
        self.parent.port_list_widget = qw.QListWidget()
        self.parent.port_list_widget.setWindowFlags(Qt.Popup)
        self.parent.port_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.parent.port_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.parent.port_list_widget.itemClicked.connect(self.on_port_selected)
        
        # 安装事件过滤器
        self.parent.port_list_widget.installEventFilter(self)
                # 安装主窗口事件过滤器
        self.parent.installEventFilter(self)
        # 设置ComboBox事件
        self.parent.comboBox.mousePressEvent = self.on_combo_clicked

        self.parent.connect_btn.clicked.connect(self.open_port)	#绑定打开串口
        if hasattr(self.parent, "init_btn"):
            self.parent.init_btn.clicked.connect(self.initialize_hardware)

        if hasattr(self.parent, "init_btn"):
            self.parent.init_btn.setEnabled(False)

       

    
    def scan_ports(self, force_update=False):
        """扫描可用串口"""
        ports = QSerialPortInfo.availablePorts()
        
        if force_update or self.parent.comboBox.count() == 0:
            self.parent.comboBox.clear()
            for port in ports:
                self.parent.comboBox.addItem(port.portName(),
                                             port.portName())

    def eventFilter(self, obj, event):
        """处理全局点击事件以隐藏下拉框"""
        if event.type() == QEvent.MouseButtonPress:
            # 获取点击的全局坐标
            global_pos = event.globalPosition().toPoint()
            
            # 判断点击是否在comboBox或下拉框范围内
            combo_rect = self.parent.comboBox.rect()
            combo_global_rect = self.parent.comboBox.rect().translated(self.parent.comboBox.mapToGlobal(QPoint(0, 0)))
            list_visible = self.parent.port_list_widget.isVisible()
            list_rect = self.parent.port_list_widget.rect()
            list_global_rect = self.parent.port_list_widget.rect().translated(self.parent.port_list_widget.mapToGlobal(QPoint(0, 0)))
            
            # 如果点击不在comboBox或下拉框范围内，且下拉框可见，则隐藏
            if (list_visible and 
                not combo_global_rect.contains(global_pos) and
                not list_global_rect.contains(global_pos)):
                self.parent.port_list_widget.hide()
                
        return super().eventFilter(obj, event)

    
    def on_combo_clicked(self, event):
        """处理ComboBox点击事件"""
        if self.parent.port_list_widget.isVisible():
            self.parent.port_list_widget.hide()
            return
        
        # 更新端口列表
        self.scan_ports(force_update=True)
        ports = QSerialPortInfo.availablePorts()
        
        # 计算最大文本宽度
        font_metrics = self.parent.port_list_widget.fontMetrics()
        max_width = 0
        items = []
        # 新增：维护描述计数字典
        desc_counter = {}
        for port in ports:
            base_desc = port.description()
            
            # 处理重复描述
            if base_desc in desc_counter:
                desc_counter[base_desc] += 1
                display_desc = f"{base_desc} ({desc_counter[base_desc]-1})"
            else:
                desc_counter[base_desc] = 1
                display_desc = base_desc
            
            text = f"{port.portName()} - {display_desc}"
            width = font_metrics.horizontalAdvance(text) + 20
            max_width = max(max_width, width)
            items.append((text, port.portName()))
        # 填充列表
        self.parent.port_list_widget.clear()
        for text, port_name in items:
            item = qw.QListWidgetItem(text)
            item.setData(Qt.UserRole, port_name)
            self.parent.port_list_widget.addItem(item)
        
        # 动态调整大小
        row_height     = self.parent.port_list_widget.sizeHintForRow(0)
        content_height = row_height * len(items) + 2 * self.parent.port_list_widget.frameWidth()
        self.parent.port_list_widget.setFixedSize(min(max_width, 500),	#限制最大宽度500px
                                                  min(content_height, 300))	#限制最大高度300px
        
        # 显示在ComboBox下方
        pos = self.parent.comboBox.mapToGlobal(self.parent.comboBox.rect().bottomLeft())
        self.parent.port_list_widget.move(pos)
        self.parent.port_list_widget.show()

    def on_port_selected(self, item):
        """处理端口选择"""
        port_name = item.data(Qt.UserRole)
        index     = self.parent.comboBox.findData(port_name)
        if index >= 0:
            self.parent.comboBox.setCurrentIndex(index)
        self.parent.port_list_widget.hide()

    def setport(self):	#初始化串口
        #设置串口名
        #self.parent.scan_ports()
        port = self.parent.comboBox.currentData()	#获取当前选中的串口
        
        self.serial_port.setPortName(port)
        #设置波特率
        # 与 env.py 中已验证可用的链路参数保持一致
        self.serial_port.setBaudRate(115200)
        #设置数据位 8位数据位
        self.serial_port.setDataBits(QSerialPort.Data8)
        # FPGA UART 使用偶校验
        self.serial_port.setParity(QSerialPort.EvenParity)
        #设置停止位
        self.serial_port.setStopBits(QSerialPort.OneStop)
    
    def open_port(self):	#打开串口
        if self.serial_port.isOpen():
            self.parent.connect_btn.setText(self.tr("连接"))
            self.serial_port.close()
            self.qt_serial = None
            if hasattr(self.parent, "router"):
                self.parent.router = None
            if hasattr(self.parent, "init_btn"):
                self.parent.init_btn.setEnabled(False)
        else:
            self.setport()	#设置串口
            
            if self.serial_port.open(QSerialPort.ReadWrite):
                self.parent.connect_btn.setText(self.tr("断开"))               
                # 配置串口读取回调
                  # ✅ 清空缓冲区
                self.serial_port.clear()
                try:
                    self.qt_serial = QtSerial(
                        serial_instance=self.serial_port,
                        timeout=1
                    )
                    self.hw_controller.set_serial(self.qt_serial)
                    if hasattr(self.parent, "router"):
                        self.parent.router = None
                    if hasattr(self.parent, "init_btn"):
                        self.parent.init_btn.setEnabled(True)
                    if hasattr(self.parent, "sync_from_device"):
                        try:
                            self.parent.sync_from_device()
                        except Exception as sync_exc:
                            qw.QMessageBox.warning(
                                self.parent,
                                self.tr("同步失败"),
                                self.tr(f"已连接串口，但同步下位机状态失败:\n{sync_exc}")
                            )
                except Exception as e:
                    # 建立 QtSerial 失败时回滚连接状态
                    self.serial_port.close()
                    self.qt_serial = None
                    self.parent.connect_btn.setText(self.tr("连接"))
                    if hasattr(self.parent, "init_btn"):
                        self.parent.init_btn.setEnabled(False)
                    qw.QMessageBox.critical(
                        self.parent,
                        self.tr("连接失败"),
                        self.tr(f"串口连接失败:\n{e}")
                    )
                    return

            else:
                qw.QMessageBox.critical(self.parent,
                                        self.tr("错误"),
                                        self.tr("无法打开串口！"))

    def initialize_hardware(self):
        if not self.serial_port.isOpen() or self.qt_serial is None:
            qw.QMessageBox.warning(self.parent,
                                   self.tr("未连接"),
                                   self.tr("请先点击“连接”打开串口。"))
            return

        try:
            self.hw_controller.init()
            qw.QMessageBox.information(self.parent,
                                       self.tr("初始化完成"),
                                       self.tr("硬件初始化成功。"))
        except Exception as e:
            qw.QMessageBox.critical(self.parent,
                                    self.tr("初始化失败"),
                                    self.tr(f"硬件初始化失败:\n{e}"))

    def _resolve_hw_module(self, module_type, module_index):
        if not self.hw_controller or not self.hw_controller.is_initialized():
            return None
        if module_type == "PID":
            return self.hw_controller.pid if module_index == 0 else self.hw_controller.pid2
        if module_type == "ACC":
            return self.hw_controller.acc if module_index == 0 else self.hw_controller.acc2
        if module_type == "SCLR":
            if module_index == 0:
                return self.hw_controller.sclr
            if module_index == 1:
                return self.hw_controller.sclr2
            if module_index == 2:
                return self.hw_controller.sclr3
            if module_index == 3:
                return self.hw_controller.sclr4
        if module_type == "FIR":
            if module_index == 0:
                return self.hw_controller.fir
            if module_index == 1:
                return self.hw_controller.fir2
            if module_index == 2:
                return self.hw_controller.fir3
            if module_index == 3:
                return self.hw_controller.fir4
        if module_type == "IIR":  # 新增 IIR 支持
            if module_index == 0:
                return self.hw_controller.iir
            if module_index == 1:
                return self.hw_controller.iir2
            if module_index == 2:
                return self.hw_controller.iir3
            if module_index == 3:
                return self.hw_controller.iir4
        if module_type == "LTRN":
            return self.hw_controller.ltrn if module_index == 0 else self.hw_controller.ltrn2
        if module_type == "PDHS":
            return self.hw_controller.pdhfsm
        if module_type == "SCLO":
            return self.hw_controller.sclofsm if module_index == 0 else self.hw_controller.sclofsm2
        return None

    def get_hw_module(self, module_type, module_index):
        return self._resolve_hw_module(module_type, module_index)

    def send_param(self, module_type, module_index, params):
        hw_module = self._resolve_hw_module(module_type, module_index)
        if hw_module is None:
            raise RuntimeError("Hardware controller not initialized")
        for key, value in params.items():
            if isinstance(value, bool):
                value = int(value)
            hw_module.write(key, value)

    def send_special_method(self, module_type, module_index, method_name, method_args=None):
        hw_module = self._resolve_hw_module(module_type, module_index)
        if hw_module is None:
            raise RuntimeError("Hardware controller not initialized")
        if not method_name:
            raise ValueError("method_name is required")
        method = getattr(hw_module, method_name, None)
        if not callable(method):
            raise AttributeError(f"{module_type}[{module_index}] does not support method '{method_name}'")

        if method_args is None:
            method_args = {}
        if not isinstance(method_args, dict):
            raise TypeError("method_args must be a dict")

        method(**method_args)

    def send_flip_toggle(self, module_type, module_index, flip_on_key, flip_off_key, checked):
        hw_module = self._resolve_hw_module(module_type, module_index)
        if hw_module is None:
            raise RuntimeError("Hardware controller not initialized")
        if checked:
            hw_module.flip_on(flip_on_key)
        else:
            hw_module.flip_off(flip_off_key)

    def send_flip_pulse(self, module_type, module_index, flip_on_key):
        hw_module = self._resolve_hw_module(module_type, module_index)
        if hw_module is None:
            raise RuntimeError("Hardware controller not initialized")
        hw_module.flip_on(flip_on_key)

    def query_router_routes(self):
        if not self.hw_controller or not self.hw_controller.is_initialized():
            raise RuntimeError("Hardware controller not initialized")

        def _read_router_word(addr, retries=4):
            last_exc = None
            for _ in range(max(1, retries)):
                try:
                    raw = self.hw_controller.bus_inst.read("ROUT", addr)
                    if isinstance(raw, (bytes, bytearray)) and len(raw) == 4:
                        return int.from_bytes(raw, "big", signed=False)
                except Exception as exc:
                    last_exc = exc
                time.sleep(0.01)

            if last_exc is not None:
                raise RuntimeError(f"Failed to read ROUT[{addr}]: {last_exc}")
            raise RuntimeError(f"Failed to read ROUT[{addr}]: invalid response")

        def _read_snapshot():
            return [_read_router_word(addr) for addr in range(32)]

        # ROUT has 32 x 32-bit words. Address 31 is bits[0:32], address 0 is bits[992:1024].
        snapshots = []
        words = None
        for _ in range(3):
            snap = _read_snapshot()
            snapshots.append(snap)
            if len(snapshots) >= 2 and snapshots[-1] == snapshots[-2]:
                words = snapshots[-1]
                break
        if words is None:
            # Fall back to the most informative snapshot when back-to-back reads are unstable.
            words = max(snapshots, key=lambda s: sum(1 for w in s if w != 0))
            print("[sync] warning: ROUT snapshots unstable, using best-effort decode")

        bit_chunks = [format(words[31 - i], "032b") for i in range(32)]
        bits = "".join(bit_chunks)

        routes = []
        # Full-connection encoding: each port entry is 8 bits [reserved(1), enable(1), source(6)]
        for port in range(128):
            start = len(bits) - (port + 1) * 8
            end = len(bits) - port * 8
            if start < 0:
                continue
            entry = bits[start:end]
            if len(entry) != 8:
                continue

            enable = int(entry[1], 2)
            source = int(entry[2:], 2)
            if enable != 1:
                continue

            if port < 64:
                dst_port = port
                src_port = source
            else:
                dst_port = port
                src_port = source + 64

            routes.append({
                "dst_port": dst_port,
                "src_port": src_port,
            })
        return routes

    def query_module_params(self, module_type, module_index, schema_fields):
        hw_module = self._resolve_hw_module(module_type, module_index)
        if hw_module is None:
            raise RuntimeError("Hardware controller not initialized")

        result = {}
        for field in schema_fields:
            key = field.get("key")
            if not key:
                continue
            try:
                value = hw_module.read(key)
            except Exception:
                continue

            if isinstance(value, (bytes, bytearray)):
                address = hw_module.process_designator(key)
                if isinstance(address, int):
                    width = hw_module.parameter_list.get(address, {"width": 32}).get("width", 32)
                else:
                    width = 32
                intval = int.from_bytes(value, "big", signed=False)
                if field.get("type") == "bool" or width == 1:
                    result[key] = bool(intval & 0x1)
                else:
                    if width < 32 and intval >= (1 << (width - 1)):
                        intval -= (1 << width)
                    elif width == 32 and intval >= (1 << 31):
                        intval -= (1 << 32)
                    result[key] = intval
            else:
                result[key] = value

        return result

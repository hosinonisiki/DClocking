import json
from collections import deque
from datetime import datetime

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtSerialPort import QSerialPort

from qt_moudle import (
    NodeItem,
    MoudlePID,
    MoudleAccumulator,
    MoudleScaler,
    ModuleFIRFilter,
    ModuleIIRFilter,
    MoudleSCLOFSM,
    MoudlePDHFSM,
    MoudleLinerTransformer,
    set_param_apply_handler,
)
from qt_Port import Port
from qt_ui_graph import NodeSignals, BorderPort, EdgeItem, DiagramScene, DiagramView, ComponentPalette
from qt_ui_utils import (
    ensure_port_methods,
    border_port_index,
    resolve_port_number,
    resolve_node_port_from_number,
    node_name_to_component,
)
import port_numbers as pn


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 节点流编辑器 - 支持复杂绕行规则")
        self.resize(1600, 900)

        self._route_queue = deque()
        self._route_sending = False
        self.route_send_delay_ms = 80

        self.comboBox = QComboBox()
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(120)
        self.mode_combo.addItems(["Free Mode", "Developer Mode"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.comboBox.setFixedWidth(180)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedWidth(80)
        self.init_btn = QPushButton("初始化")
        self.init_btn.setFixedWidth(80)
        self.save_cfg_btn = QPushButton("保存配置")
        self.save_cfg_btn.setFixedWidth(90)
        self.load_cfg_btn = QPushButton("加载配置")
        self.load_cfg_btn.setFixedWidth(90)

        serial_bar = QWidget()
        serial_bar.setFixedHeight(40)
        serial_layout = QHBoxLayout(serial_bar)
        serial_layout.setContentsMargins(8, 4, 8, 4)
        serial_layout.addStretch()
        serial_layout.addWidget(self.comboBox)
        serial_layout.addWidget(self.mode_combo)
        serial_layout.addWidget(self.connect_btn)
        serial_layout.addWidget(self.init_btn)
        serial_layout.addWidget(self.save_cfg_btn)
        serial_layout.addWidget(self.load_cfg_btn)
        serial_layout.addStretch()

        self.serial_port = QSerialPort(self)
        self.port_ctrl = Port(self, self.serial_port)
        self.port_ctrl.scan_ports(force_update=True)
        ensure_port_methods()
        self.router = None

        self.signals = NodeSignals()
        self.signals.connection_created.connect(self.run_business_logic)
        self.signals.connection_removed.connect(self.handle_connection_removed)

        self.scene = DiagramScene(self.signals)
        self.view = DiagramView(self.scene)
        self.palette = ComponentPalette()
        self._on_mode_changed(self.mode_combo.currentText())

        self.save_cfg_btn.clicked.connect(self.save_configuration)
        self.load_cfg_btn.clicked.connect(self.load_configuration)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.palette)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(serial_bar)
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)

        set_param_apply_handler(self._apply_param_to_hardware)

    def _on_mode_changed(self, text):
        developer_mode = text == "Developer Mode"
        self.scene.set_developer_mode(developer_mode)
        for item in self.scene.items():
            if isinstance(item, NodeItem) and hasattr(item, "free_mode"):
                item.free_mode = not developer_mode

    def _port_ref_for_name_index(self, node_name, port_idx, role, node_map):
        if node_name.startswith("Border_out_") and node_name not in ("Border_out_HIGH", "Border_out_LOW"):
            idx = border_port_index(node_name, "Border_out_")
            if idx is not None and role == "out":
                return self.scene.left_ports[idx]
        if node_name.startswith("Border_in_"):
            idx = border_port_index(node_name, "Border_in_")
            if idx is not None and role == "in":
                return self.scene.right_ports[idx]
        if node_name == "Border_out_HIGH" and role == "out":
            return self.scene.constant_out_ports[0]
        if node_name == "Border_out_LOW" and role == "out":
            return self.scene.constant_out_ports[1]

        node = node_map.get(node_name)
        if node is None:
            return None
        if role == "out" and 0 <= port_idx < len(node.out_ports):
            return node.out_ports[port_idx]
        if role == "in" and 0 <= port_idx < len(node.in_ports):
            return node.in_ports[port_idx]
        return None

    def sync_from_device(self):
        if not self.port_ctrl.is_open():
            return

        routes = self.port_ctrl.query_router_routes()
        self._prime_router_cache_from_device_routes(routes)

        device_edges = []
        required_nodes = set()
        unresolved_route_count = 0
        unknown_node_count = 0
        missing_port_ref_count = 0
        param_fail_count = 0

        for route in routes:
            src_name, src_idx = resolve_node_port_from_number(route["src_port"], "out")
            dst_name, dst_idx = resolve_node_port_from_number(route["dst_port"], "in")
            if src_name is None or dst_name is None:
                unresolved_route_count += 1
                continue
            device_edges.append((src_name, src_idx, dst_name, dst_idx))
            if not src_name.startswith("Border_"):
                required_nodes.add(src_name)
            if not dst_name.startswith("Border_"):
                required_nodes.add(dst_name)

        self._clear_canvas()
        ordered_names = sorted(required_nodes)

        internal_edges = []
        for src_name, _src_idx, dst_name, _dst_idx in device_edges:
            if src_name in required_nodes and dst_name in required_nodes:
                internal_edges.append((src_name, dst_name))

        adjacency = {name: set() for name in required_nodes}
        indegree = {name: 0 for name in required_nodes}
        for src_name, dst_name in internal_edges:
            if dst_name not in adjacency[src_name]:
                adjacency[src_name].add(dst_name)
                indegree[dst_name] += 1

        layer = {name: 0 for name in required_nodes}
        queue = deque(sorted([name for name in required_nodes if indegree[name] == 0]))
        visited = 0
        while queue:
            node_name = queue.popleft()
            visited += 1
            for nxt in adjacency[node_name]:
                layer[nxt] = max(layer[nxt], layer[node_name] + 1)
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if visited < len(required_nodes):
            max_layer = max(layer.values()) if layer else 0
            for name in sorted(required_nodes):
                if indegree[name] > 0:
                    max_layer += 1
                    layer[name] = max_layer

        layers = {}
        for name in ordered_names:
            lv = layer.get(name, 0)
            layers.setdefault(lv, []).append(name)

        node_map = {}
        x0, y0 = 280.0, 170.0
        dx, dy = 280.0, 190.0
        for lv in sorted(layers.keys()):
            names_in_layer = sorted(layers[lv])
            for row, name in enumerate(names_in_layer):
                component_name, index = node_name_to_component(name)
                if component_name is None:
                    unknown_node_count += 1
                    continue
                cls = self.view.moudle_factory.get(component_name)
                if cls is None:
                    unknown_node_count += 1
                    continue

                pos = QPointF(x0 + lv * dx, y0 + row * dy)
                node = cls(component_name, index, pos)
                self.view._used_indices.setdefault(component_name, set()).add(index)
                self.view._apply_mode_to_node(node)
                self.scene.addItem(node)
                node_map[name] = node

        for src_name, src_idx, dst_name, dst_idx in device_edges:
            src_port = self._port_ref_for_name_index(src_name, src_idx, "out", node_map)
            dst_port = self._port_ref_for_name_index(dst_name, dst_idx, "in", node_map)
            if src_port is None or dst_port is None:
                missing_port_ref_count += 1
                continue
            if dst_port.has_connection():
                continue

            edge = EdgeItem(src_port, dst_port)
            self.scene.addItem(edge)
            edge.refresh_style()

            start_node = src_port.parent_node if hasattr(src_port, "parent_node") else None
            end_node = dst_port.parent_node if hasattr(dst_port, "parent_node") else None
            if start_node:
                start_node.edges.append(edge)
            if end_node:
                end_node.edges.append(edge)

        for node in node_map.values():
            module_type, module_index = self._resolve_module_identity(node)
            if module_type is None:
                continue
            try:
                schema = node.param_schema() if hasattr(node, "param_schema") else []
                params = self.port_ctrl.query_module_params(module_type, module_index, schema)
                if hasattr(node, "_params") and isinstance(node._params, dict):
                    node._params.update(params)
            except Exception as exc:
                param_fail_count += 1
                print(f"[sync] param query failed for {node.name}: {exc}")

        self.view.auto_fit_nodes()
        print(f"[sync] loaded {len(node_map)} nodes and {len(device_edges)} routes from device")

        report = (
            f"同步完成\n"
            f"已识别连线: {len(device_edges)}\n"
            f"已生成节点: {len(node_map)}\n"
            f"未识别端口连线: {unresolved_route_count}\n"
            f"端口映射失败连线: {missing_port_ref_count}\n"
            f"未知模块节点: {unknown_node_count}\n"
            f"参数读取失败模块: {param_fail_count}"
        )
        QMessageBox.information(self, "同步报告", report)

    def run_business_logic(self, src, src_port, dst, dst_port):
        print(f"🔄 >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")
        src_port_num = resolve_port_number(src, src_port, "out")
        dst_port_num = resolve_port_number(dst, dst_port, "in")
        if src_port_num is None or dst_port_num is None:
            print(f"[route] skip: unresolved port mapping src={src}:{src_port} dst={dst}:{dst_port}")
            return
        self._apply_routing(dst_port_num, src_port_num, f"{src}:Out{src_port+1} -> {dst}:In{dst_port+1}")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        print(f"🧹 >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")
        dst_port_num = resolve_port_number(dst, dst_port, "in")
        if dst_port_num is None:
            print(f"[route] skip: unresolved port mapping dst={dst}:{dst_port}")
            return
        src_port_num = pn.VOID_BOOL if dst_port_num >= 64 else pn.VOID
        self._apply_routing(dst_port_num, src_port_num, f"{dst}:In{dst_port+1} cleared")

    def _ensure_router(self):
        if not self.port_ctrl.is_open():
            print("[route] serial port not open, routing not sent")
            return None
        hw_router = getattr(self.port_ctrl.hw_controller, "router", None)
        if hw_router is None:
            print("[route] router is not ready")
            return None
        self.router = hw_router
        return self.router

    def _prime_router_cache_from_device_routes(self, routes):
        router = self._ensure_router()
        if router is None:
            return

        router.port_config = [0] * 128
        if not getattr(router, "port_enable", None) or len(router.port_enable) != 128:
            router.port_enable = [1] * 128

        for route in routes:
            dst_port = route.get("dst_port")
            src_port = route.get("src_port")
            if dst_port is None or src_port is None:
                continue
            try:
                router.set_routing(int(dst_port), int(src_port))
            except Exception as exc:
                print(f"[sync] skip cache prime route {src_port}->{dst_port}: {exc}")

    def _apply_routing(self, dst_port_num, src_port_num, label):
        router = self._ensure_router()
        if router is None:
            return
        try:
            router.set_routing(dst_port_num, src_port_num)
            router.upload()
            print(f"[route] sent: {label} ({src_port_num} -> {dst_port_num})")
        except Exception as exc:
            print(f"[route] failed: {label}: {exc}")

    def _resolve_module_identity(self, node):
        if isinstance(node, MoudlePID):
            return "PID", node.index
        if isinstance(node, MoudleAccumulator):
            return "ACC", node.index
        if isinstance(node, MoudleScaler):
            return "SCLR", node.index
        if isinstance(node, ModuleFIRFilter):
            return "FIR", node.index
        if isinstance(node, ModuleIIRFilter):
            return "IIR", node.index
        if isinstance(node, MoudleLinerTransformer):
            return "LTRN", node.index
        if isinstance(node, MoudlePDHFSM):
            return "PDH", node.index
        if isinstance(node, MoudleSCLOFSM):
            return "SCLO", node.index
        return None, None

    def _apply_param_to_hardware(self, node, params):
        module_type, module_index = self._resolve_module_identity(node)
        if module_type is None:
            return
        try:
            if isinstance(params, dict) and "__special_method__" in params:
                method_name = params.get("__special_method__")
                method_args = params.get("args", {})
                self.port_ctrl.send_special_method(module_type, module_index, method_name, method_args)
                print(f"[method] sent {node.name}.{method_name}({method_args})")
                return

            schema_fields = node.param_schema() if hasattr(node, "param_schema") else []
            schema_map = {field.get("key"): field for field in schema_fields if isinstance(field, dict) and field.get("key")}

            regular_params = {}
            for key, value in params.items():
                field = schema_map.get(key, {})
                control_mode = field.get("ui_control")

                if control_mode == "flip_toggle":
                    flip_on_key = field.get("flip_on", key)
                    flip_off_key = field.get("flip_off", key)
                    checked = bool(value)
                    self.port_ctrl.send_flip_toggle(module_type, module_index, flip_on_key, flip_off_key, checked)
                    print(f"[param] flip_toggle {node.name}.{key} -> {'on' if checked else 'off'}")
                    continue

                if control_mode == "flip_pulse":
                    flip_on_key = field.get("flip_on", key)
                    self.port_ctrl.send_flip_pulse(module_type, module_index, flip_on_key)
                    print(f"[param] flip_pulse {node.name}.{key}")
                    continue

                regular_params[key] = value

            if regular_params:
                self.port_ctrl.send_param(module_type, module_index, regular_params)
                for key, value in regular_params.items():
                    print(f"[param] sent {node.name}.{key} = {value}")
        except Exception as exc:
            print(f"[param] failed {node.name}: {exc}")

    def _port_to_ref(self, port):
        if isinstance(port, BorderPort):
            return {
                "kind": "border",
                "port_type": port.port_type,
                "index": int(port.index),
                "name": port.name,
            }

        parent = getattr(port, "parent_node", None)
        if parent is None:
            return None
        return {
            "kind": "node",
            "node_name": parent.name,
            "port_type": port.port_type,
            "index": int(port.index),
        }

    def _resolve_port_ref(self, ref, node_map):
        if not isinstance(ref, dict):
            return None

        kind = ref.get("kind")
        port_type = ref.get("port_type")
        idx = int(ref.get("index", -1))

        if kind == "border":
            name = ref.get("name")
            if name == "Border_out_HIGH" and hasattr(self.scene, "constant_out_ports") and len(self.scene.constant_out_ports) >= 1:
                return self.scene.constant_out_ports[0]
            if name == "Border_out_LOW" and hasattr(self.scene, "constant_out_ports") and len(self.scene.constant_out_ports) >= 2:
                return self.scene.constant_out_ports[1]

            if idx < 0 or idx >= 8:
                return None
            if port_type == "out":
                return self.scene.left_ports[idx]
            if port_type == "in":
                return self.scene.right_ports[idx]
            return None

        if kind == "node":
            node_name = ref.get("node_name")
            node = node_map.get(node_name)
            if node is None:
                return None
            if port_type == "out" and 0 <= idx < len(node.out_ports):
                return node.out_ports[idx]
            if port_type == "in" and 0 <= idx < len(node.in_ports):
                return node.in_ports[idx]
        return None

    def _clear_canvas(self):
        for item in list(self.scene.items()):
            if isinstance(item, EdgeItem):
                item.remove()

        for item in list(self.scene.items()):
            if isinstance(item, NodeItem):
                if item.scene():
                    item.scene().removeItem(item)

        for key in self.view._used_indices:
            self.view._used_indices[key].clear()

    def _build_config_dict(self):
        nodes = []
        edges = []

        for item in self.scene.items():
            if isinstance(item, NodeItem):
                params = item.get_params() if hasattr(item, "get_params") else {}
                nodes.append(
                    {
                        "name": item.name,
                        "component_name": item.component_name,
                        "index": int(item.index),
                        "pos": {"x": float(item.pos().x()), "y": float(item.pos().y())},
                        "params": params,
                    }
                )

        for item in self.scene.items():
            if isinstance(item, EdgeItem):
                src_ref = self._port_to_ref(item.start_port)
                dst_ref = self._port_to_ref(item.end_port)
                if src_ref and dst_ref:
                    edges.append({"src": src_ref, "dst": dst_ref})

        return {
            "version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "mode": self.mode_combo.currentText(),
            "nodes": nodes,
            "edges": edges,
        }

    def save_configuration(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存配置", "diagram_config.json", "JSON Files (*.json);;All Files (*)")
        if not file_path:
            return

        config = self._build_config_dict()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"[config] saved: {file_path}")
        except Exception as exc:
            print(f"[config] save failed: {exc}")

    def _create_node_from_config(self, node_cfg):
        component_name = node_cfg.get("component_name")
        cls = self.view.moudle_factory.get(component_name)
        if cls is None:
            print(f"[config] skip unknown component: {component_name}")
            return None

        try:
            idx = int(node_cfg.get("index", 0))
            pos_cfg = node_cfg.get("pos", {})
            pos = QPointF(float(pos_cfg.get("x", 0.0)), float(pos_cfg.get("y", 0.0)))
            node = cls(component_name, idx, pos)
        except Exception as exc:
            print(f"[config] create node failed: {node_cfg}: {exc}")
            return None

        self.view._used_indices.setdefault(component_name, set()).add(idx)
        self.view._apply_mode_to_node(node)
        self.scene.addItem(node)

        params = node_cfg.get("params", {})
        if isinstance(params, dict) and params:
            try:
                node.set_params(params)
            except Exception as exc:
                print(f"[config] apply params failed for {node.name}: {exc}")

        return node

    def _restore_edges(self, edges_cfg, node_map):
        for edge_cfg in edges_cfg:
            src_port = self._resolve_port_ref(edge_cfg.get("src"), node_map)
            dst_port = self._resolve_port_ref(edge_cfg.get("dst"), node_map)
            if src_port is None or dst_port is None:
                print(f"[config] skip invalid edge: {edge_cfg}")
                continue

            if dst_port.port_type != "in":
                print(f"[config] skip non-input destination edge: {edge_cfg}")
                continue
            if dst_port.has_connection():
                print(f"[config] skip occupied destination edge: {edge_cfg}")
                continue

            edge = EdgeItem(src_port, dst_port)
            self.scene.addItem(edge)
            edge.refresh_style()

            start_node = src_port.parent_node if hasattr(src_port, "parent_node") else None
            end_node = dst_port.parent_node if hasattr(dst_port, "parent_node") else None
            if start_node:
                start_node.edges.append(edge)
            if end_node:
                end_node.edges.append(edge)

            src_name = start_node.name if start_node else src_port.name
            dst_name = end_node.name if end_node else dst_port.name
            self.signals.connection_created.emit(src_name, src_port.index, dst_name, dst_port.index)

    def load_configuration(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载配置", "", "JSON Files (*.json);;All Files (*)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as exc:
            print(f"[config] load failed: {exc}")
            return

        nodes_cfg = config.get("nodes", [])
        edges_cfg = config.get("edges", [])
        if not isinstance(nodes_cfg, list) or not isinstance(edges_cfg, list):
            print("[config] invalid format: nodes/edges must be list")
            return

        self._clear_canvas()

        mode = config.get("mode")
        if isinstance(mode, str) and mode in ["Free Mode", "Developer Mode"]:
            self.mode_combo.setCurrentText(mode)

        node_map = {}
        for node_cfg in nodes_cfg:
            node = self._create_node_from_config(node_cfg)
            if node is not None:
                node_map[node.name] = node

        self._restore_edges(edges_cfg, node_map)
        self.view.update_border_ports()
        print(f"[config] loaded: {file_path}")

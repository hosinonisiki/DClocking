import json
import sys
from collections import deque
from datetime import datetime
import module as hw_module_defs

from PySide6.QtCore import Qt, QPointF, QObject, Signal
from PySide6.QtGui import QTextCursor
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
    QLabel,
    QScrollArea,
    QFrame,
    QPlainTextEdit,
)
from PySide6.QtSerialPort import QSerialPort

from qt_module import (
    NodeItem,
    ModulePID,
    ModuleAccumulator,
    ModuleScaler,
    ModuleFIRFilter,
    ModuleIIRFilter,
    ModuleSCLOFSM,
    ModulePDHFSM,
    ModuleLinerTransformer,
    ParamDialog,
    PIDParamCanvas,
    SpecialMethodDialog,
    set_param_apply_handler,
    set_param_open_handler,
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


class _StreamProxy(QObject):
    text_written = Signal(str)

    def __init__(self, target_stream):
        super().__init__()
        self._target_stream = target_stream

    def write(self, text):
        if text is None:
            return
        chunk = str(text)
        if not chunk:
            return
        self.text_written.emit(chunk)
        if self._target_stream is not None:
            self._target_stream.write(chunk)

    def flush(self):
        if self._target_stream is not None:
            self._target_stream.flush()


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
        self.clear_btn = QPushButton("清空画布")
        self.clear_btn.setFixedWidth(90)

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
        serial_layout.addWidget(self.clear_btn)
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
        self._param_panels = {}
        self._build_side_panel()
        self._build_log_panel()
        self._setup_log_redirect()
        self._on_mode_changed(self.mode_combo.currentText())

        self.save_cfg_btn.clicked.connect(self.save_configuration)
        self.load_cfg_btn.clicked.connect(self.load_configuration)
        self.clear_btn.clicked.connect(self.confirm_clear_canvas)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.side_panel)
        splitter.setSizes([1200, 400])

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(serial_bar)
        main_layout.addWidget(splitter, stretch=1)
        main_layout.addWidget(self.log_panel, stretch=0)
        self.setCentralWidget(main_widget)

        set_param_apply_handler(self._apply_param_to_hardware)
        set_param_open_handler(self._open_param_panel)

    def _build_log_panel(self):
        self.log_panel = QFrame(self)
        self.log_panel.setFrameShape(QFrame.StyledPanel)
        self.log_panel.setFixedHeight(140)

        layout = QVBoxLayout(self.log_panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        title = QLabel("命令行输出")
        layout.addWidget(title)

        self.log_output = QPlainTextEdit(self.log_panel)
        self.log_output.setReadOnly(True)
        self.log_output.document().setMaximumBlockCount(300)
        layout.addWidget(self.log_output, stretch=1)

    def _setup_log_redirect(self):
        self._stdout_origin = sys.stdout
        self._stderr_origin = sys.stderr

        self._stdout_proxy = _StreamProxy(self._stdout_origin)
        self._stderr_proxy = _StreamProxy(self._stderr_origin)
        self._stdout_proxy.text_written.connect(self._append_log_text)
        self._stderr_proxy.text_written.connect(self._append_log_text)

        sys.stdout = self._stdout_proxy
        sys.stderr = self._stderr_proxy

    def _restore_log_redirect(self):
        if getattr(self, "_stdout_origin", None) is not None and sys.stdout is getattr(self, "_stdout_proxy", None):
            sys.stdout = self._stdout_origin
        if getattr(self, "_stderr_origin", None) is not None and sys.stderr is getattr(self, "_stderr_proxy", None):
            sys.stderr = self._stderr_origin

    def _append_log_text(self, text):
        if not text:
            return
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def closeEvent(self, event):
        self._restore_log_redirect()
        super().closeEvent(event)

    def _build_side_panel(self):
        self.side_panel = QWidget()
        side_layout = QHBoxLayout(self.side_panel)
        side_layout.setContentsMargins(6, 6, 6, 6)
        side_layout.setSpacing(8)

        module_col = QWidget(self.side_panel)
        module_layout = QVBoxLayout(module_col)
        module_layout.setContentsMargins(0, 0, 0, 0)
        module_layout.setSpacing(6)
        palette_title = QLabel("模块列表")
        module_layout.addWidget(palette_title)
        module_layout.addWidget(self.palette, stretch=1)

        param_col = QWidget(self.side_panel)
        param_layout_root = QVBoxLayout(param_col)
        param_layout_root.setContentsMargins(0, 0, 0, 0)
        param_layout_root.setSpacing(6)

        header_row = QHBoxLayout()
        param_title = QLabel("参数窗口")
        clear_btn = QPushButton("清空")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._clear_param_panels)
        header_row.addWidget(param_title)
        header_row.addStretch()
        header_row.addWidget(clear_btn)
        param_layout_root.addLayout(header_row)

        self.param_scroll = QScrollArea()
        self.param_scroll.setWidgetResizable(True)
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        self.param_layout.setSpacing(8)
        self.param_layout.addStretch()
        self.param_scroll.setWidget(self.param_container)
        param_layout_root.addWidget(self.param_scroll, stretch=1)

        side_layout.addWidget(module_col, stretch=1)
        side_layout.addWidget(param_col, stretch=2)

    def _scroll_to_panel(self, panel_widget):
        scrollbar = self.param_scroll.verticalScrollBar()
        target = max(0, panel_widget.y() - 8)
        scrollbar.setValue(target)

    def _close_param_panel(self, panel_key):
        panel = self._param_panels.pop(panel_key, None)
        if panel is None:
            return
        panel.setParent(None)
        panel.deleteLater()

    def _clear_param_panels(self):
        for key in list(self._param_panels.keys()):
            self._close_param_panel(key)

    def _open_param_panel(self, node):
        if node is None:
            return False

        self._refresh_node_params_from_device(
            node,
            update_panel=not isinstance(node, (ModuleFIRFilter, ModuleIIRFilter)),
        )

        schema = node.param_schema() if hasattr(node, "param_schema") else []
        special_methods = node.special_methods_schema() if hasattr(node, "special_methods_schema") else []
        if not schema and not special_methods:
            return False

        panel_key = f"{node.name}@{node.component_name}:{node.index}"
        existing = self._param_panels.get(panel_key)
        if existing is not None:
            if not isinstance(node, (ModuleFIRFilter, ModuleIIRFilter)):
                self._update_panel_from_node(existing, node)
            self._scroll_to_panel(existing)
            return True

        card = QFrame(self.param_container)
        card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel(f"{node.display_name} 参数")
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(60)
        close_btn.clicked.connect(lambda _=False, k=panel_key: self._close_param_panel(k))
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        card_layout.addLayout(title_row)

        if schema:
            companion_widget_factory = None
            if isinstance(node, ModulePID):
                companion_widget_factory = lambda dialog_parent: PIDParamCanvas(dialog_parent)

            param_widget = ParamDialog(
                schema,
                node.get_params(),
                parent=self,
                apply_callback=node.set_params,
                companion_widget_factory=companion_widget_factory,
            )
            param_widget.setWindowFlags(Qt.Widget)
            card_layout.addWidget(param_widget)
            card._param_widget = param_widget

        if special_methods:
            special_widget = SpecialMethodDialog(
                special_methods,
                parent=self,
                apply_callback=node.apply_special_method,
                initial_values=getattr(node, "_special_method_args", {}),
            )
            special_widget.setWindowFlags(Qt.Widget)
            card_layout.addWidget(special_widget)
            card._special_widget = special_widget

        insert_pos = max(0, self.param_layout.count() - 1)
        self.param_layout.insertWidget(insert_pos, card)
        self._param_panels[panel_key] = card
        self._scroll_to_panel(card)
        return True

    def _update_panel_from_node(self, panel_card, node):
        param_widget = getattr(panel_card, "_param_widget", None)
        if param_widget is not None:
            param_widget.set_values(node.get_params())

    def _refresh_node_params_from_device(self, node, update_panel=True):
        if node is None:
            return False

        module_type, module_index = self._resolve_module_identity(node)
        if module_type is None:
            return False

        hw_module = self.port_ctrl.get_hw_module(module_type, module_index)
        if hw_module is None:
            return False

        schema_fields = getattr(node, "schema", None) or []
        field_map = self._schema_field_map(node)
        refreshed = {}
        read_errors = []

        for key, width in self._direct_param_specs(module_type).items():
            try:
                value = hw_module.read(key)
                refreshed[key] = self._decode_direct_value(value, width, field_map.get(key))
            except Exception as exc:
                read_errors.append(f"{key}: {exc}")

        for field in schema_fields:
            if not isinstance(field, dict):
                continue
            key = field.get("key")
            if not key or key in refreshed:
                continue

            try:
                value = hw_module.readv(key)
                if field.get("type") == "bool" or field.get("ui_control") in {"flip_toggle", "flip_pulse"}:
                    value = bool(value)
                refreshed[key] = value
            except Exception as exc:
                read_errors.append(f"{key}: {exc}")

        if not refreshed:
            if read_errors:
                print(f"[param] refresh skipped {node.name}: {read_errors[0]}")
            return False

        if hasattr(node, "_params"):
            node._params.update(refreshed)

        panel_key = f"{node.name}@{node.component_name}:{node.index}"
        panel = self._param_panels.get(panel_key)
        if update_panel and panel is not None:
            self._update_panel_from_node(panel, node)

        if read_errors:
            print(f"[param] partial refresh {node.name}: {len(read_errors)} field(s) skipped")
        return True

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

    def _optimize_grid_layout(self, required_nodes, internal_edges):
        if not required_nodes:
            return {}

        adjacency = {name: set() for name in required_nodes}
        predecessors = {name: set() for name in required_nodes}
        for src_name, dst_name in internal_edges:
            if src_name in required_nodes and dst_name in required_nodes and dst_name not in adjacency[src_name]:
                adjacency[src_name].add(dst_name)
                predecessors[dst_name].add(src_name)

        index = 0
        stack = []
        on_stack = set()
        indices = {}
        lowlink = {}
        components = []

        def strong_connect(node_name):
            nonlocal index
            indices[node_name] = index
            lowlink[node_name] = index
            index += 1
            stack.append(node_name)
            on_stack.add(node_name)

            for nxt in adjacency[node_name]:
                if nxt not in indices:
                    strong_connect(nxt)
                    lowlink[node_name] = min(lowlink[node_name], lowlink[nxt])
                elif nxt in on_stack:
                    lowlink[node_name] = min(lowlink[node_name], indices[nxt])

            if lowlink[node_name] == indices[node_name]:
                comp = []
                while stack:
                    w = stack.pop()
                    on_stack.remove(w)
                    comp.append(w)
                    if w == node_name:
                        break
                components.append(sorted(comp))

        for name in sorted(required_nodes):
            if name not in indices:
                strong_connect(name)

        node_to_comp = {}
        for cid, comp_nodes in enumerate(components):
            for n in comp_nodes:
                node_to_comp[n] = cid

        comp_adj = {cid: set() for cid in range(len(components))}
        comp_in_degree = {cid: 0 for cid in range(len(components))}
        for src_name, dst_name in internal_edges:
            if src_name not in node_to_comp or dst_name not in node_to_comp:
                continue
            c_src = node_to_comp[src_name]
            c_dst = node_to_comp[dst_name]
            if c_src != c_dst and c_dst not in comp_adj[c_src]:
                comp_adj[c_src].add(c_dst)
                comp_in_degree[c_dst] += 1

        comp_layer = {cid: 0 for cid in comp_adj}
        queue = deque(sorted([cid for cid, deg in comp_in_degree.items() if deg == 0]))
        while queue:
            cid = queue.popleft()
            for nxt in sorted(comp_adj[cid]):
                comp_layer[nxt] = max(comp_layer[nxt], comp_layer[cid] + 1)
                comp_in_degree[nxt] -= 1
                if comp_in_degree[nxt] == 0:
                    queue.append(nxt)

        node_layer = {n: comp_layer[node_to_comp[n]] for n in required_nodes}
        layers = {}
        for n in sorted(required_nodes):
            layers.setdefault(node_layer[n], []).append(n)

        ordered_layers = {lv: list(sorted(names)) for lv, names in layers.items()}
        layer_keys = sorted(ordered_layers.keys())

        def _build_rank(order_map):
            rank = {}
            for lv in layer_keys:
                for i, n in enumerate(order_map.get(lv, [])):
                    rank[n] = i
            return rank

        def _barycenter(values):
            if not values:
                return None
            return sum(values) / len(values)

        for _ in range(10):
            changed = False

            rank = _build_rank(ordered_layers)
            for lv in layer_keys[1:]:
                names = ordered_layers.get(lv, [])
                base_pos = {n: i for i, n in enumerate(names)}

                def _key_forward(n):
                    vals = [rank[p] for p in predecessors.get(n, set()) if p in rank]
                    b = _barycenter(vals)
                    if b is None:
                        return (10**9, base_pos.get(n, 10**9), n)
                    return (b, base_pos.get(n, 10**9), n)

                new_names = sorted(names, key=_key_forward)
                if new_names != names:
                    changed = True
                    ordered_layers[lv] = new_names
                rank = _build_rank(ordered_layers)

            rank = _build_rank(ordered_layers)
            for lv in reversed(layer_keys[:-1]):
                names = ordered_layers.get(lv, [])
                base_pos = {n: i for i, n in enumerate(names)}

                def _key_backward(n):
                    vals = [rank[s] for s in adjacency.get(n, set()) if s in rank]
                    b = _barycenter(vals)
                    if b is None:
                        return (10**9, base_pos.get(n, 10**9), n)
                    return (b, base_pos.get(n, 10**9), n)

                new_names = sorted(names, key=_key_backward)
                if new_names != names:
                    changed = True
                    ordered_layers[lv] = new_names
                rank = _build_rank(ordered_layers)

            if not changed:
                break

        def _objective(order_map):
            rank = _build_rank(order_map)
            local_layer = {}
            for lv, names in order_map.items():
                for n in names:
                    local_layer[n] = lv

            crossings = 0
            for idx, lv in enumerate(layer_keys[:-1]):
                nxt = layer_keys[idx + 1]
                pair_edges = []
                for src_name, dst_name in internal_edges:
                    if src_name in rank and dst_name in rank and local_layer.get(src_name) == lv and local_layer.get(dst_name) == nxt:
                        pair_edges.append((rank[src_name], rank[dst_name]))

                for i in range(len(pair_edges)):
                    a1, b1 = pair_edges[i]
                    for j in range(i + 1, len(pair_edges)):
                        a2, b2 = pair_edges[j]
                        if (a1 - a2) * (b1 - b2) < 0:
                            crossings += 1

            span = 0
            vertical = 0
            for src_name, dst_name in internal_edges:
                if src_name not in rank or dst_name not in rank:
                    continue
                span += abs(local_layer[src_name] - local_layer[dst_name])
                vertical += abs(rank[src_name] - rank[dst_name])

            max_rows = max((len(v) for v in order_map.values()), default=1)
            area = max_rows * max(1, len(order_map))
            return crossings * 3000 + span * 90 + vertical * 12 + area

        best_score = _objective(ordered_layers)
        for _ in range(12):
            improved = False
            for lv in layer_keys:
                names = ordered_layers.get(lv, [])
                if len(names) < 2:
                    continue
                i = 0
                while i < len(names) - 1:
                    names[i], names[i + 1] = names[i + 1], names[i]
                    new_score = _objective(ordered_layers)
                    if new_score < best_score:
                        best_score = new_score
                        improved = True
                    else:
                        names[i], names[i + 1] = names[i + 1], names[i]
                    i += 1
            if not improved:
                break

        return ordered_layers

    def _position_synced_nodes(self, ordered_layers, node_map):
        if not ordered_layers or not node_map:
            return

        layer_keys = sorted(ordered_layers.keys())
        max_rows = max((len(ordered_layers.get(lv, [])) for lv in layer_keys), default=1)
        layer_count = max(1, len(layer_keys))

        vertical_gap = max(32.0, 76.0 - 6.0 * max(0, max_rows - 1))
        horizontal_gap = max(120.0, 220.0 - 14.0 * max(0, layer_count - 1))

        layer_widths = {}
        layer_heights = {}
        for lv in layer_keys:
            nodes = [node_map[name] for name in ordered_layers.get(lv, []) if name in node_map]
            if not nodes:
                layer_widths[lv] = 0.0
                layer_heights[lv] = 0.0
                continue

            max_width = max(float(getattr(node, "width", 128.0)) for node in nodes)
            total_height = sum(float(getattr(node, "height", 108.0)) for node in nodes)
            total_height += vertical_gap * max(0, len(nodes) - 1)

            layer_widths[lv] = max_width
            layer_heights[lv] = total_height

        total_width = 0.0
        for idx, lv in enumerate(layer_keys):
            total_width += layer_widths[lv]
            if idx < len(layer_keys) - 1:
                total_width += horizontal_gap

        current_x = -total_width / 2.0
        for lv in layer_keys:
            names_in_layer = [name for name in ordered_layers.get(lv, []) if name in node_map]
            if not names_in_layer:
                continue

            layer_width = layer_widths[lv]
            layer_height = layer_heights[lv]
            layer_center_x = current_x + layer_width / 2.0
            current_y = -layer_height / 2.0

            for name in names_in_layer:
                node = node_map[name]
                node_height = float(getattr(node, "height", 108.0))
                node.setPos(QPointF(layer_center_x, current_y + node_height / 2.0))
                current_y += node_height + vertical_gap

            current_x += layer_width + horizontal_gap

    def sync_from_device(self):
        if not self.port_ctrl.is_open():
            return

        routes = self.port_ctrl.query_router_routes()
        self._prime_router_cache_from_device_routes(routes)

        device_edges = []
        unresolved_route_count = 0
        unresolved_samples = []
        partial_mapped_route_count = 0
        unknown_node_count = 0
        missing_port_ref_count = 0
        param_fail_count = 0

        for route in routes:
            src_name, src_idx = resolve_node_port_from_number(route["src_port"], "out")
            dst_name, dst_idx = resolve_node_port_from_number(route["dst_port"], "in")

            if src_name is None or dst_name is None:
                unresolved_route_count += 1
                if src_name is not None or dst_name is not None:
                    partial_mapped_route_count += 1
                if len(unresolved_samples) < 12:
                    unresolved_samples.append((route.get("src_port"), route.get("dst_port")))
                continue

            device_edges.append((src_name, src_idx, dst_name, dst_idx))

        def _is_physical_border(name):
            if not isinstance(name, str):
                return False
            if name.startswith("Border_out_") and name not in ("Border_out_HIGH", "Border_out_LOW"):
                return True
            return name.startswith("Border_in_")

        adjacency = {}
        for src_name, _src_idx, dst_name, _dst_idx in device_edges:
            adjacency.setdefault(src_name, set()).add(dst_name)
            adjacency.setdefault(dst_name, set()).add(src_name)

        connected_names = set()
        search_queue = deque()
        for name in adjacency.keys():
            if _is_physical_border(name):
                connected_names.add(name)
                search_queue.append(name)

        while search_queue:
            current = search_queue.popleft()
            for nxt in adjacency.get(current, ()):
                if nxt in connected_names:
                    continue
                connected_names.add(nxt)
                search_queue.append(nxt)

        required_nodes = {
            name for name in connected_names
            if not name.startswith("Border_") and not name.startswith("HIGH") and not name.startswith("LOW")
        }
        visible_edges = [
            (src_name, src_idx, dst_name, dst_idx)
            for src_name, src_idx, dst_name, dst_idx in device_edges
            if src_name in connected_names and dst_name in connected_names
        ]

        self._clear_canvas()

        internal_edges = []
        for src_name, _src_idx, dst_name, _dst_idx in visible_edges:
            if src_name in required_nodes and dst_name in required_nodes:
                internal_edges.append((src_name, dst_name))
        ordered_layers = self._optimize_grid_layout(required_nodes, internal_edges)

        node_map = {}
        for lv in sorted(ordered_layers.keys()):
            names_in_layer = ordered_layers[lv]
            for name in names_in_layer:
                component_name, index = node_name_to_component(name)
                if component_name is None:
                    unknown_node_count += 1
                    continue
                cls = self.view.module_factory.get(component_name)
                if cls is None:
                    unknown_node_count += 1
                    continue

                pos = QPointF(0.0, 0.0)
                node = cls(component_name, index, pos)
                self.view._used_indices.setdefault(component_name, set()).add(index)
                self.view._apply_mode_to_node(node)
                self.scene.addItem(node)
                node_map[name] = node

        self._position_synced_nodes(ordered_layers, node_map)

        for src_name, src_idx, dst_name, dst_idx in visible_edges:
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
            try:
                self._refresh_node_params_from_device(node, update_panel=False)
            except Exception as exc:
                param_fail_count += 1
                print(f"[sync] param query failed for {node.name}: {exc}")

        self.view.auto_fit_nodes()
        print(f"[sync] loaded {len(node_map)} nodes and {len(visible_edges)} visible routes from device")

        report = (
            f"同步完成\n"
            f"已识别连线: {len(visible_edges)}\n"
            f"已生成节点: {len(node_map)}\n"
            f"未识别端口连线: {unresolved_route_count}\n"
            f"部分端点可识别但连线缺失: {partial_mapped_route_count}\n"
            f"端口映射失败连线: {missing_port_ref_count}\n"
            f"未知模块节点: {unknown_node_count}\n"
            f"参数读取失败模块: {param_fail_count}"
        )
        if unresolved_samples:
            sample_text = ", ".join([f"{s}->{d}" for s, d in unresolved_samples])
            report += f"\n未识别样例(src->dst): {sample_text}"
        QMessageBox.information(self, "同步报告", report)

    def run_business_logic(self, src, src_port, dst, dst_port):
        src_log = self._runtime_log_name(src, src_port, "out", dst, dst_port, "in")
        dst_log = self._runtime_log_name(dst, dst_port, "in", src, src_port, "out")
        print(f"🔄 >> 执行业务逻辑: 数据从 {src_log}:Out{src_port+1} 传输到 {dst_log}:In{dst_port+1}...")
        src_port_num = resolve_port_number(src, src_port, "out")
        dst_port_num = resolve_port_number(dst, dst_port, "in")
        if src_port_num is None or dst_port_num is None:
            print(f"[route] skip: unresolved port mapping src={src}:{src_port} dst={dst}:{dst_port}")
            return
        self._apply_routing(dst_port_num, src_port_num, f"{src_log}:Out{src_port+1} -> {dst_log}:In{dst_port+1}")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        src_log = self._runtime_log_name(src, src_port, "out", dst, dst_port, "in")
        dst_log = self._runtime_log_name(dst, dst_port, "in", src, src_port, "out")
        print(f"🧹 >> 清理业务逻辑: 断开 {src_log}:Out{src_port+1} 到 {dst_log}:In{dst_port+1} 的数据流...")
        dst_port_num = resolve_port_number(dst, dst_port, "in")
        if dst_port_num is None:
            print(f"[route] skip: unresolved port mapping dst={dst}:{dst_port}")
            return
        src_port_num = pn.VOID_BOOL if dst_port_num >= 64 else pn.VOID
        self._apply_routing(dst_port_num, src_port_num, f"{dst_log}:In{dst_port+1} cleared")

    def _runtime_log_name(self, node_name, port_idx, role, peer_name=None, peer_port_idx=None, peer_role=None):
        if node_name not in ("HIGH", "LOW"):
            return node_name

        candidates = []
        for item in self.scene.items():
            if not isinstance(item, NodeItem):
                continue
            if getattr(item, "name", None) == node_name:
                candidates.append(item)

        if not candidates:
            return f"{node_name}[?]"

        if peer_name is not None and peer_port_idx is not None and peer_role is not None:
            for node in candidates:
                ports = node.out_ports if role == "out" else node.in_ports
                if not (0 <= port_idx < len(ports)):
                    continue
                for edge in ports[port_idx].connections:
                    peer_port = edge.end_port if role == "out" else edge.start_port
                    peer_parent = peer_port.parent_node if hasattr(peer_port, "parent_node") and peer_port.parent_node else None
                    if peer_parent is None:
                        continue
                    if getattr(peer_parent, "name", None) != peer_name:
                        continue
                    if int(peer_port.index) != int(peer_port_idx):
                        continue
                    return f"{node_name}[{int(getattr(node, 'index', 0))}]"

        if len(candidates) == 1:
            return f"{node_name}[{int(getattr(candidates[0], 'index', 0))}]"
        return f"{node_name}[?]"

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
        try:
            router.sync()
        except Exception as exc:
            print(f"[sync] skip cache prime route : {exc}")

    def _apply_routing(self, dst_port_num, src_port_num, label, upload_immediately=True):
        router = self._ensure_router()
        if router is None:
            return
        try:
            router.set_routing(dst_port_num, src_port_num)
            if upload_immediately:
                router.upload()
                print(f"[route] sent: {label} ({src_port_num} -> {dst_port_num})")
            else:
                print(f"[route] staged: {label} ({src_port_num} -> {dst_port_num})")
        except Exception as exc:
            print(f"[route] failed: {label}: {exc}")

    def _clear_all_routes(self):
        hw_controller = getattr(self.port_ctrl, "hw_controller", None)
        router = getattr(hw_controller, "router", None) if hw_controller is not None else None
        if router is None:
            return

        try:
            for dst_port_num in range(128):
                src_port_num = pn.VOID_BOOL if dst_port_num >= 64 else pn.VOID
                router.set_routing(dst_port_num, src_port_num)

            if self.port_ctrl.is_open():
                router.upload()
                print("[route] cleared all routes in hardware")
            else:
                print("[route] cleared all routes in local cache (serial not open)")
        except Exception as exc:
            print(f"[route] failed to clear all routes: {exc}")

    def _disconnect_all_connections(self):
        # 仅负责断开底层连线（硬件/缓存路由），避免与画布清理耦合。
        self._clear_all_routes()

    def _resolve_module_identity(self, node):
        if isinstance(node, ModulePID):
            return "PID", node.index
        if isinstance(node, ModuleAccumulator):
            return "ACC", node.index
        if isinstance(node, ModuleScaler):
            return "SCLR", node.index
        if isinstance(node, ModuleFIRFilter):
            return "FIR", node.index
        if isinstance(node, ModuleIIRFilter):
            return "IIR", node.index
        if isinstance(node, ModuleLinerTransformer):
            return "LTRN", node.index
        if isinstance(node, ModulePDHFSM):
            return "PDHS", node.index
        if isinstance(node, ModuleSCLOFSM):
            return "SCLO", node.index
        return None, None

    def _direct_param_specs(self, module_type):
        module_class_map = {
            "PID": hw_module_defs.ModulePID,
            "ACC": hw_module_defs.ModuleAccumulator,
            "SCLR": hw_module_defs.ModuleScaler,
            "FIR": hw_module_defs.ModuleFIRFilter,
            "IIR": hw_module_defs.ModuleIIRFilter,
            "LTRN": hw_module_defs.ModuleLinearTransformer,
            "PDHS": hw_module_defs.ModulePDHFSM,
            "SCLO": hw_module_defs.ModuleSCLOFSM,
        }
        module_cls = module_class_map.get(module_type)
        parameter_list = getattr(module_cls, "parameter_list", {}) if module_cls is not None else {}
        specs = {}
        for address in sorted(parameter_list.keys()):
            info = parameter_list.get(address, {})
            name = info.get("name")
            width = int(info.get("width", 32))
            if not name or name == "/":
                continue
            specs[name] = width
        return specs

    def _schema_field_map(self, node):
        field_map = {}
        for field in self._node_schema_fields(node):
            if not isinstance(field, dict):
                continue
            key = field.get("key")
            if key:
                field_map[key] = field
        return field_map

    def _decode_direct_value(self, raw_value, width, field=None):
        if not isinstance(raw_value, (bytes, bytearray)):
            return raw_value

        intval = int.from_bytes(raw_value, "big", signed=False)
        if width == 1:
            return bool(intval & 0x1)

        if isinstance(field, dict):
            if field.get("type") == "bool" or field.get("ui_control") in {"flip_toggle", "flip_pulse"}:
                return bool(intval & 0x1)
            min_value = field.get("min")
            if isinstance(min_value, (int, float)) and min_value >= 0:
                return intval

        if intval >= (1 << (width - 1)):
            intval -= (1 << width)
        return intval

    def _node_schema_fields(self, node):
        fields = getattr(node, "schema", None)
        if isinstance(fields, list):
            return fields
        if hasattr(node, "param_schema"):
            fields = node.param_schema()
            if isinstance(fields, list):
                return fields
        return []

    def _node_direct_params(self, node):
        params = {}
        node_params = getattr(node, "_params", None)
        if not isinstance(node_params, dict):
            return params

        module_type, module_index = self._resolve_module_identity(node)
        direct_specs = self._direct_param_specs(module_type)
        field_map = self._schema_field_map(node)
        hw_module = self.port_ctrl.get_hw_module(module_type, module_index) if module_type is not None else None
        if hw_module is not None and direct_specs:
            for key, width in direct_specs.items():
                try:
                    value = hw_module.read(key)
                    params[key] = self._decode_direct_value(value, width, field_map.get(key))
                except Exception:
                    if key in node_params:
                        params[key] = node_params[key]
                    else:
                        params[key] = False if width == 1 else 0
            return params

        if direct_specs:
            for key, width in direct_specs.items():
                if key in node_params:
                    params[key] = node_params[key]
                else:
                    params[key] = False if width == 1 else 0

        for field in self._node_schema_fields(node):
            if not isinstance(field, dict):
                continue
            if field.get("mode") != "direct":
                continue
            key = field.get("key")
            if not key:
                continue
            if key in node_params:
                params[key] = node_params[key]
            elif hasattr(node, "_default_for_field"):
                params[key] = node._default_for_field(field)
        return params

    def _node_special_method_state(self, node):
        raw = getattr(node, "_special_method_args", None)
        if not isinstance(raw, dict):
            return {}
        stored = {}
        for method_name, args in raw.items():
            if not method_name:
                continue
            stored[method_name] = dict(args or {}) if isinstance(args, dict) else {}
        return stored

    def _apply_param_to_hardware(self, node, params):
        module_type, module_index = self._resolve_module_identity(node)
        if module_type is None:
            return
        try:
            did_write = False
            if isinstance(params, dict) and "__special_method__" in params:
                method_name = params.get("__special_method__")
                method_args = params.get("args", {})
                self.port_ctrl.send_special_method(module_type, module_index, method_name, method_args)
                node._commit_pending_cache_update()
                print(f"[method] sent {node.name}.{method_name}({method_args})")
                self._refresh_node_params_from_device(
                    node,
                    update_panel=not isinstance(node, (ModuleFIRFilter, ModuleIIRFilter)),
                )
                return

            schema_fields = self._node_schema_fields(node)
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
                    did_write = True
                    continue

                if control_mode == "flip_pulse":
                    flip_on_key = field.get("flip_on", key)
                    self.port_ctrl.send_flip_pulse(module_type, module_index, flip_on_key)
                    print(f"[param] flip_pulse {node.name}.{key}")
                    did_write = True
                    continue

                regular_params[key] = value

            if regular_params:
                self.port_ctrl.send_param(module_type, module_index, regular_params)
                for key, value in regular_params.items():
                    print(f"[param] sent {node.name}.{key} = {value}")
                did_write = True

            if did_write:
                if not isinstance(node, (ModuleFIRFilter, ModuleIIRFilter)):
                    self._refresh_node_params_from_device(node)
                node._commit_pending_cache_update()
        except Exception as exc:
            node._rollback_pending_cache_update()
            self._refresh_node_params_from_device(
                node,
                update_panel=not isinstance(node, (ModuleFIRFilter, ModuleIIRFilter)),
            )
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
        module_index = int(getattr(parent, "index", -1))
        component_name = getattr(parent, "component_name", None)
        return {
            "kind": "node",
            "node_name": parent.name,
            "component_name": component_name,
            "module_index": module_index,
            "node_key": f"{component_name}@{module_index}",
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
            node = None

            node_key = ref.get("node_key")
            if isinstance(node_key, str):
                node = node_map.get(node_key)

            component_name = ref.get("component_name")
            module_index = ref.get("module_index", None)
            if node is None and component_name is not None and module_index is not None:
                try:
                    node = node_map.get(f"{component_name}@{int(module_index)}")
                except Exception:
                    node = None

            if node is None:
                node_name = ref.get("node_name")
                node = node_map.get(node_name)
                if node is None and isinstance(node_name, str) and node_name in ("HIGH", "LOW") and module_index is not None:
                    try:
                        node = node_map.get(f"{node_name}{int(module_index) + 1}")
                    except Exception:
                        node = None

            if node is None:
                return None
            if port_type == "out" and 0 <= idx < len(node.out_ports):
                return node.out_ports[idx]
            if port_type == "in" and 0 <= idx < len(node.in_ports):
                return node.in_ports[idx]
        return None

    def _clear_canvas(self, emit_connection_removed: bool = False):
        self._clear_param_panels()
        self._route_queue.clear()
        self._route_sending = False

        existing_edges = [item for item in list(self.scene.items()) if isinstance(item, EdgeItem)]

        if emit_connection_removed:
            for edge in existing_edges:
                start_port = getattr(edge, "start_port", None)
                end_port = getattr(edge, "end_port", None)
                if start_port is None or end_port is None:
                    continue
                src_name = start_port.parent_node.name if hasattr(start_port, "parent_node") and start_port.parent_node else start_port.name
                dst_name = end_port.parent_node.name if hasattr(end_port, "parent_node") and end_port.parent_node else end_port.name
                self.signals.connection_removed.emit(src_name, int(start_port.index), dst_name, int(end_port.index))

        for edge in existing_edges:
            edge.remove()

        # Defensive cleanup: clear all remaining connection refs to avoid invisible ghost edges.
        for item in list(self.scene.items()):
            if not isinstance(item, NodeItem):
                continue
            for port in list(getattr(item, "in_ports", [])) + list(getattr(item, "out_ports", [])):
                if hasattr(port, "connections") and isinstance(port.connections, list):
                    port.connections.clear()
            if hasattr(item, "edges") and isinstance(item.edges, list):
                item.edges.clear()

        for border_port in list(getattr(self.scene, "left_ports", [])) + list(getattr(self.scene, "right_ports", [])):
            if hasattr(border_port, "connections") and isinstance(border_port.connections, list):
                border_port.connections.clear()

        for const_port in list(getattr(self.scene, "constant_out_ports", [])):
            if hasattr(const_port, "connections") and isinstance(const_port.connections, list):
                const_port.connections.clear()

        for item in list(self.scene.items()):
            if isinstance(item, NodeItem):
                if item.scene():
                    item.scene().removeItem(item)

        for key in self.view._used_indices:
            self.view._used_indices[key].clear()

    def confirm_clear_canvas(self):
        reply = QMessageBox.question(self, '清空画布', '确定要清空所有模块和连线吗？', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._disconnect_all_connections()
            self._clear_canvas(emit_connection_removed=False)

    def _build_config_dict(self):
        nodes = []
        edges = []

        for item in self.scene.items():
            if isinstance(item, NodeItem):
                nodes.append(
                    {
                        "name": item.name,
                        "component_name": item.component_name,
                        "index": int(item.index),
                        "pos": {"x": float(item.pos().x()), "y": float(item.pos().y())},
                        "direct_params": self._node_direct_params(item),
                        "special_methods": self._node_special_method_state(item),
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
        cls = self.view.module_factory.get(component_name)
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

        return node

    def _restore_edges(self, edges_cfg, node_map, batch_upload: bool = False):
        staged_routes = 0
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
            src_port_num = resolve_port_number(src_name, src_port.index, "out")
            dst_port_num = resolve_port_number(dst_name, dst_port.index, "in")
            if src_port_num is None or dst_port_num is None:
                print(f"[config] skip unresolved route: {src_name}:{src_port.index} -> {dst_name}:{dst_port.index}")
                continue

            self._apply_routing(
                dst_port_num,
                src_port_num,
                f"{src_name}:Out{src_port.index + 1} -> {dst_name}:In{dst_port.index + 1}",
                upload_immediately=not batch_upload,
            )
            if batch_upload:
                staged_routes += 1

        if batch_upload and staged_routes > 0:
            router = self._ensure_router()
            if router is not None:
                try:
                    router.upload()
                    print(f"[route] uploaded staged routes: {staged_routes}")
                except Exception as exc:
                    print(f"[route] failed final batch upload: {exc}")

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

        self._disconnect_all_connections()
        self._clear_canvas(emit_connection_removed=False)

        mode = config.get("mode")
        if isinstance(mode, str) and mode in ["Free Mode", "Developer Mode"]:
            self.mode_combo.setCurrentText(mode)

        node_map = {}
        loaded_nodes = []
        for node_cfg in nodes_cfg:
            node = self._create_node_from_config(node_cfg)
            if node is not None:
                loaded_nodes.append((node_cfg, node))
                node_map.setdefault(node.name, node)
                node_map[f"{node.component_name}@{int(node.index)}"] = node
                if node.component_name in ("布尔值：是", "布尔值：否"):
                    node_map[f"{node.component_name}{int(node.index) + 1}"] = node

        for node_cfg, node in loaded_nodes:
            special_methods = node_cfg.get("special_methods", {})
            if not isinstance(special_methods, dict):
                continue
            for method_name, method_args in special_methods.items():
                if not method_name:
                    continue
                try:
                    node.apply_special_method(method_name, method_args if isinstance(method_args, dict) else {})
                except Exception as exc:
                    print(f"[config] apply special method failed for {node.name}.{method_name}: {exc}")

        for node_cfg, node in loaded_nodes:
            direct_params = node_cfg.get("direct_params")
            if not isinstance(direct_params, dict):
                direct_params = node_cfg.get("params", {})
            if not isinstance(direct_params, dict) or not direct_params:
                continue
            try:
                node.set_params(direct_params)
            except Exception as exc:
                print(f"[config] apply direct params failed for {node.name}: {exc}")

        self._restore_edges(edges_cfg, node_map, batch_upload=True)
        self.view.center_on_nodes()
        print(f"[config] loaded: {file_path}")

"""User-defined composite module library and visual authoring workbench."""

from __future__ import annotations

import copy
import json
import math
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QRectF, QStandardPaths, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qt_module import (
    FIRDesignerWidget,
    IIRDesignerWidget,
    ModuleFIRFilter,
    ModuleIIRFilter,
    ModulePID,
    NodeItem,
    PIDParamCanvas,
    ParamDialog,
    SpecialMethodDialog,
)
from qt_ui_graph import ComponentPalette, DiagramScene, DiagramView, EdgeItem, NodeSignals
from qt_ui_theme import draw_node_chrome


class CustomCompositeLibrary(QObject):
    """Versioned JSON store for reusable user-authored expanded graphs."""

    changed = Signal()
    FORMAT_VERSION = 1

    def __init__(self, storage_path=None, parent=None):
        super().__init__(parent)
        self.storage_path = Path(storage_path) if storage_path else self.default_storage_path()
        self.last_error = ""
        self._definitions = []
        self.reload()

    @staticmethod
    def default_storage_path():
        root = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        return root / "DClocking" / "custom_composites.json"

    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec="seconds")

    def reload(self):
        self.last_error = ""
        if not self.storage_path.exists():
            self._definitions = []
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            entries = payload.get("composites", []) if isinstance(payload, dict) else []
            if not isinstance(entries, list):
                raise ValueError("composites 必须是数组")
            normalized = []
            ids = set()
            names = set()
            for entry in entries:
                definition = self._normalize(entry, require_id=True)
                name_key = definition["name"].casefold()
                if definition["id"] in ids or name_key in names:
                    continue
                ids.add(definition["id"])
                names.add(name_key)
                normalized.append(definition)
            self._definitions = normalized
        except Exception as exc:
            self._definitions = []
            self.last_error = f"自定义组合模块库读取失败：{exc}"

    def definitions(self):
        return copy.deepcopy(sorted(self._definitions, key=lambda item: item["name"].casefold()))

    def get(self, definition_id):
        for definition in self._definitions:
            if definition["id"] == str(definition_id):
                return copy.deepcopy(definition)
        return None

    def find_by_name(self, name):
        key = str(name or "").strip().casefold()
        for definition in self._definitions:
            if definition["name"].casefold() == key:
                return copy.deepcopy(definition)
        return None

    def save_definition(self, definition, definition_id=None):
        incoming = dict(definition or {})
        target_id = str(definition_id or incoming.get("id") or uuid.uuid4().hex)
        incoming["id"] = target_id
        existing = self.get(target_id)
        incoming["created_at"] = (
            existing.get("created_at") if existing else incoming.get("created_at", self._now())
        )
        incoming["updated_at"] = self._now()
        normalized = self._normalize(incoming, require_id=True)

        duplicate = next(
            (
                item
                for item in self._definitions
                if item["name"].casefold() == normalized["name"].casefold()
                and item["id"] != target_id
            ),
            None,
        )
        if duplicate is not None:
            raise ValueError(f"名称“{normalized['name']}”已存在")

        updated = []
        replaced = False
        for item in self._definitions:
            if item["id"] == target_id:
                updated.append(normalized)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(normalized)
        self._definitions = updated
        self._write()
        self.changed.emit()
        return copy.deepcopy(normalized)

    def delete(self, definition_id):
        definition_id = str(definition_id)
        remaining = [item for item in self._definitions if item["id"] != definition_id]
        if len(remaining) == len(self._definitions):
            return False
        self._definitions = remaining
        self._write()
        self.changed.emit()
        return True

    def _write(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.FORMAT_VERSION,
            "composites": self._definitions,
        }
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.storage_path.parent,
                prefix=".custom_composites_",
                suffix=".tmp",
                delete=False,
            ) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
                tmp_path = Path(handle.name)
            os.replace(tmp_path, self.storage_path)
        finally:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink()

    def _normalize(self, definition, require_id=False):
        if not isinstance(definition, dict):
            raise ValueError("组合模块定义必须是对象")
        name = str(definition.get("name", "")).strip()
        if not name:
            raise ValueError("组合模块名称不能为空")
        if len(name) > 40:
            raise ValueError("组合模块名称不能超过 40 个字符")

        definition_id = str(definition.get("id", "")).strip()
        if require_id and not definition_id:
            raise ValueError("组合模块缺少 id")
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("自定义组合模块至少需要一个非组合模块")
        if not isinstance(edges, list):
            raise ValueError("组合模块连线必须是数组")

        normalized_nodes = []
        node_ids = set()
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError("组合模块节点格式无效")
            local_id = str(node.get("local_id") or f"n{index + 1}")
            component_name = str(node.get("component_name", "")).strip()
            pos = node.get("pos", {})
            try:
                x = float(pos.get("x", 0.0))
                y = float(pos.get("y", 0.0))
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("组合模块节点坐标无效") from exc
            if not component_name or local_id in node_ids or not math.isfinite(x) or not math.isfinite(y):
                raise ValueError("组合模块节点定义无效")
            node_ids.add(local_id)
            normalized_nodes.append(
                {
                    "local_id": local_id,
                    "component_name": component_name,
                    "pos": {"x": x, "y": y},
                    "direct_params": copy.deepcopy(node.get("direct_params", {}))
                    if isinstance(node.get("direct_params", {}), dict)
                    else {},
                    "special_methods": copy.deepcopy(node.get("special_methods", {}))
                    if isinstance(node.get("special_methods", {}), dict)
                    else {},
                }
            )

        normalized_edges = []
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("组合模块连线格式无效")
            src = edge.get("src", {})
            dst = edge.get("dst", {})
            src_id = str(src.get("node_id", ""))
            dst_id = str(dst.get("node_id", ""))
            try:
                src_port = int(src.get("port_index", -1))
                dst_port = int(dst.get("port_index", -1))
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("组合模块连线端口无效") from exc
            if src_id not in node_ids or dst_id not in node_ids or src_port < 0 or dst_port < 0:
                raise ValueError("组合模块连线引用无效")
            normalized_edges.append(
                {
                    "src": {"node_id": src_id, "port_index": src_port},
                    "dst": {"node_id": dst_id, "port_index": dst_port},
                }
            )

        def normalize_ports(items, port_type):
            if not isinstance(items, list):
                raise ValueError("黑盒接口必须是数组")
            normalized_ports = []
            keys = set()
            node_map = {node["local_id"]: node for node in normalized_nodes}
            for index, port in enumerate(items):
                if not isinstance(port, dict):
                    raise ValueError("黑盒接口定义无效")
                node_id = str(port.get("node_id", ""))
                try:
                    port_index = int(port.get("port_index", -1))
                except (TypeError, ValueError, OverflowError) as exc:
                    raise ValueError("黑盒接口端口无效") from exc
                key = str(port.get("key") or f"{port_type}_{index + 1}")
                if node_id not in node_map or port_index < 0 or key in keys:
                    raise ValueError("黑盒接口引用无效")
                keys.add(key)
                raw_signals = port.get("signals", ["level"])
                signals = [str(value) for value in raw_signals] if isinstance(raw_signals, (list, tuple)) else [str(raw_signals)]
                normalized_ports.append(
                    {
                        "key": key,
                        "label": str(port.get("label") or f"{'输入' if port_type == 'input' else '输出'} {index + 1}")[:32],
                        "node_id": node_id,
                        "port_index": port_index,
                        "signals": signals,
                    }
                )
            return normalized_ports

        normalized_inputs = normalize_ports(definition.get("inputs", []), "input")
        normalized_outputs = normalize_ports(definition.get("outputs", []), "output")

        raw_parameters = definition.get("parameters", [])
        if not isinstance(raw_parameters, list):
            raise ValueError("黑盒参数必须是数组")
        normalized_parameters = []
        parameter_keys = set()
        for index, parameter in enumerate(raw_parameters):
            if not isinstance(parameter, dict):
                raise ValueError("黑盒参数定义无效")
            mapping = parameter.get("mapping", {})
            node_id = str(mapping.get("node_id", ""))
            kind = str(mapping.get("kind", "direct"))
            target_key = str(mapping.get("target_key", ""))
            method_name = str(mapping.get("method_name", ""))
            key = str(parameter.get("key") or f"parameter_{index + 1}")
            if (
                node_id not in node_ids
                or kind not in {"direct", "special"}
                or not target_key
                or key in parameter_keys
                or (kind == "special" and not method_name)
            ):
                raise ValueError("黑盒参数映射无效")
            parameter_keys.add(key)
            normalized = {
                "key": key,
                "label": str(parameter.get("label") or target_key)[:48],
                "type": str(parameter.get("type", "float")),
                "default": copy.deepcopy(parameter.get("default", 0)),
                "mapping": {
                    "node_id": node_id,
                    "kind": kind,
                    "target_key": target_key,
                },
            }
            if method_name:
                normalized["mapping"]["method_name"] = method_name
            for field in ("min", "max", "unit", "decimals", "options", "note"):
                if field in parameter:
                    normalized[field] = copy.deepcopy(parameter[field])
            normalized_parameters.append(normalized)

        return {
            "id": definition_id,
            "name": name,
            "description": str(definition.get("description", "")).strip()[:160],
            "schema_version": self.FORMAT_VERSION,
            "topology": "expanded_graph",
            "created_at": str(definition.get("created_at", self._now())),
            "updated_at": str(definition.get("updated_at", self._now())),
            "nodes": normalized_nodes,
            "edges": normalized_edges,
            "inputs": normalized_inputs,
            "outputs": normalized_outputs,
            "parameters": normalized_parameters,
        }


class CustomCompositeNode(NodeItem):
    """Visible black-box proxy backed by allocated hidden runtime modules."""

    def __init__(
        self,
        definition,
        instance_index,
        position,
        runtime_nodes,
        display_ordinal=1,
    ):
        self.definition = copy.deepcopy(definition)
        self.definition_id = str(definition.get("id", ""))
        self.definition_identity = self.definition_id or (
            f"name:{str(definition.get('name', '')).strip().casefold()}"
        )
        self.display_ordinal = max(1, int(display_ordinal))
        self.runtime_nodes = dict(runtime_nodes)
        inputs = list(definition.get("inputs", []))
        outputs = list(definition.get("outputs", []))
        name = f"UCMP{instance_index + 1}"
        super().__init__(name, "自定义组合模块", instance_index, position, len(inputs), len(outputs))
        self.base_display_name = str(definition.get("name", "自定义组合模块"))
        self.display_name = (
            self.base_display_name
            if self.display_ordinal == 1
            else f"{self.base_display_name}{self.display_ordinal}"
        )
        self.inputs = [item.get("key", f"IN{idx + 1}") for idx, item in enumerate(inputs)]
        self.outputs = [item.get("key", f"OUT{idx + 1}") for idx, item in enumerate(outputs)]
        self.inputs_display_name = [item.get("label", f"输入{idx + 1}") for idx, item in enumerate(inputs)]
        self.outputs_display_name = [item.get("label", f"输出{idx + 1}") for idx, item in enumerate(outputs)]
        self.inputs_signals = [item.get("signals", ["level"]) for item in inputs]
        self.outputs_signals = [item.get("signals", ["level"]) for item in outputs]
        self._parameter_definitions = copy.deepcopy(definition.get("parameters", []))
        self._params = {}
        for parameter in self._parameter_definitions:
            self._params[parameter["key"]] = self._mapped_parameter_value(
                parameter,
                fallback=parameter.get("default", 0),
            )
        self._internal_edges = copy.deepcopy(definition.get("edges", []))
        self.free_mode = True
        self._create_ports()

    def _apply_adaptive_size(self):
        max_ports = max(self.num_inputs, self.num_outputs, 1)
        self.width = max(210, min(300, 150 + len(self.display_name) * 7))
        self.height = max(112, 58 + max_ports * 32)

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        painter.setPen(QColor("#FFFFFF"))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        painter.setFont(title_font)
        painter.drawText(
            QRectF(rect.left() + 14, rect.top() + 8, rect.width() - 28, 22),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.display_name,
        )
        meta_font = QFont()
        meta_font.setPointSize(7)
        meta_font.setBold(True)
        painter.setFont(meta_font)
        painter.setPen(QColor("#AEB6C1"))
        painter.drawText(
            QRectF(rect.left() + 14, rect.top() + 30, rect.width() - 28, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"CUSTOM BLACK BOX · {len(self.runtime_nodes)} MODULES",
        )
        label_font = QFont()
        label_font.setPointSize(7)
        painter.setFont(label_font)
        painter.setPen(QColor("#E9EDF2"))
        for index, port in enumerate(self.in_ports):
            painter.drawText(
                QRectF(rect.left() + 12, port.pos().y() - 8, rect.width() * 0.43, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                self.inputs_display_name[index],
            )
        for index, port in enumerate(self.out_ports):
            painter.drawText(
                QRectF(rect.right() - rect.width() * 0.43 - 12, port.pos().y() - 8, rect.width() * 0.43, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                self.outputs_display_name[index],
            )
        painter.setPen(QPen(QColor("#A4003B"), 1))
        painter.drawText(
            QRectF(rect.left() + 12, rect.bottom() - 22, rect.width() - 24, 14),
            Qt.AlignCenter,
            "双击展开内部详情与参数",
        )

    def _mapped_parameter_value(self, parameter, fallback=0):
        mapping = parameter.get("mapping", {})
        node = self.runtime_nodes.get(mapping.get("node_id"))
        if node is None:
            return fallback
        if mapping.get("kind") == "special":
            method_args = getattr(node, "_special_method_args", {}).get(mapping.get("method_name"), {})
            return method_args.get(mapping.get("target_key"), fallback)
        params = node.get_params() if hasattr(node, "get_params") else {}
        return params.get(mapping.get("target_key"), fallback)

    def runtime_port_reference(self, port_type, index):
        definitions = self.definition.get("inputs" if port_type == "in" else "outputs", [])
        if index < 0 or index >= len(definitions):
            return None
        mapping = definitions[index]
        node = self.runtime_nodes.get(mapping.get("node_id"))
        if node is None:
            return None
        return node.name, int(mapping.get("port_index", 0))

    def param_schema(self):
        result = []
        for parameter in self._parameter_definitions:
            field = {key: copy.deepcopy(value) for key, value in parameter.items() if key != "mapping"}
            field["mode"] = "direct"
            field["free"] = True
            result.append(field)
        return result

    def get_params(self):
        return copy.deepcopy(self._params)

    def set_params(self, params):
        if not isinstance(params, dict):
            return
        definitions = {item["key"]: item for item in self._parameter_definitions}
        for key, value in params.items():
            parameter = definitions.get(key)
            if parameter is None:
                continue
            mapping = parameter.get("mapping", {})
            node = self.runtime_nodes.get(mapping.get("node_id"))
            if node is None:
                continue
            if mapping.get("kind") == "special":
                method_name = mapping.get("method_name")
                args = dict(getattr(node, "_special_method_args", {}).get(method_name, {}))
                if not args:
                    for method in node.special_methods_schema():
                        if method.get("name") == method_name:
                            args = {
                                field["key"]: field.get("default")
                                for field in method.get("params", [])
                            }
                            break
                args[mapping.get("target_key")] = value
                node.apply_special_method(method_name, args)
            else:
                node.set_params({mapping.get("target_key"): value})
            # Mirror the runtime node's committed value.  The existing hardware
            # handler can roll its cache back when a device write fails.
            self._params[key] = self._mapped_parameter_value(
                parameter,
                fallback=self._params.get(key, parameter.get("default", value)),
            )

    def release_runtime(self, view, scene):
        for edge in self._internal_edges:
            src = edge.get("src", {})
            dst = edge.get("dst", {})
            src_node = self.runtime_nodes.get(src.get("node_id"))
            dst_node = self.runtime_nodes.get(dst.get("node_id"))
            if src_node is not None and dst_node is not None:
                scene.signals.connection_removed.emit(
                    src_node.name,
                    int(src.get("port_index", 0)),
                    dst_node.name,
                    int(dst.get("port_index", 0)),
                )
        for node in self.runtime_nodes.values():
            view._free_index(node.component_name, int(node.index))
        self.runtime_nodes.clear()


class CustomCompositeDetailsWidget(QWidget):
    """Expandable internal component and route browser for a black-box node."""

    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.setObjectName("custom_composite_details_widget")
        self.setAccessibleName("自定义组合模块内部详情")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        header = QHBoxLayout()
        title = QLabel("INTERNAL GRAPH")
        title.setStyleSheet("color: #6C7685; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        expand = QPushButton("全部展开")
        expand.setObjectName("custom_composite_expand_details_button")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(expand)
        layout.addLayout(header)
        tree = QTreeWidget(self)
        tree.setObjectName("custom_composite_details_tree")
        tree.setHeaderLabels(["内部组件 / 连线", "详情"])
        tree.setAlternatingRowColors(True)
        for local_id, runtime_node in node.runtime_nodes.items():
            component = QTreeWidgetItem(
                [runtime_node.display_name, f"{runtime_node.name} · {runtime_node.component_name}"]
            )
            component.setData(0, Qt.UserRole, local_id)
            params = runtime_node.get_params() if hasattr(runtime_node, "get_params") else {}
            if params:
                params_root = QTreeWidgetItem(["参数快照", f"{len(params)} 项"])
                for key, value in params.items():
                    params_root.addChild(QTreeWidgetItem([str(key), str(value)]))
                component.addChild(params_root)
            tree.addTopLevelItem(component)
        routes_root = QTreeWidgetItem(["内部连线", f"{len(node.definition.get('edges', []))} 条"])
        for edge in node.definition.get("edges", []):
            src = edge.get("src", {})
            dst = edge.get("dst", {})
            routes_root.addChild(
                QTreeWidgetItem(
                    [
                        f"{src.get('node_id')}:Out{int(src.get('port_index', 0)) + 1}",
                        f"→ {dst.get('node_id')}:In{int(dst.get('port_index', 0)) + 1}",
                    ]
                )
            )
        tree.addTopLevelItem(routes_root)
        layout.addWidget(tree)
        expand.clicked.connect(tree.expandAll)


class CustomCompositeWorkbench(QDialog):
    """Isolated graph editor for authoring reusable expanded composites."""

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self.library = library
        self._current_definition_id = None
        self._refresh_pending = False
        self._interface_overrides = {}
        self._parameter_overrides = {}
        self._settings_rebuilding = False
        self.setObjectName("custom_composite_workbench")
        self.setAccessibleName("自定义组合模块工作台")
        self.setWindowTitle("自定义组合模块工作台 · DClocking")
        self.setModal(False)
        self.setMinimumSize(1080, 680)
        self.resize(1420, 820)

        self.signals = NodeSignals()
        self.scene = DiagramScene(self.signals)
        self.scene.param_open_handler = self._open_node_inspector
        for port in self.scene.left_ports + self.scene.right_ports:
            port.setVisible(False)
            port.setEnabled(False)
        self.view = DiagramView(self.scene)
        self.view.setObjectName("custom_composite_canvas")
        self.view.setAccessibleName("自定义组合模块编辑画布")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self._build_status_bar())

        self.signals.connection_created.connect(lambda *_: self._schedule_summary_refresh())
        self.signals.connection_removed.connect(lambda *_: self._schedule_summary_refresh())
        self.scene.changed.connect(lambda *_: self._schedule_summary_refresh())
        self.library.changed.connect(self._refresh_definition_combo)
        self._refresh_definition_combo()
        self._show_inspector_placeholder()
        self._refresh_summary()
        self.setStyleSheet(
            "#custom_composite_header { background: #FFFFFF; border-bottom: 1px solid #D8D4CF; }"
            "#custom_composite_title { color: #243447; font-size: 16px; font-weight: 750; letter-spacing: 1px; }"
            "#custom_composite_chip { color: #8F123D; background: #F5E6EB; border: 1px solid #E5C7D2; "
            "border-radius: 9px; padding: 3px 9px; font-size: 10px; font-weight: 650; }"
            "#custom_composite_left_panel, #custom_composite_right_panel { background: #FBFAF8; }"
            "#custom_composite_status_bar { background: #FFFFFF; border-top: 1px solid #D8D4CF; }"
            "#custom_composite_status { color: #5F6976; font-size: 11px; }"
            "#custom_composite_counts { color: #8F123D; font-size: 11px; font-weight: 650; }"
        )

    def _build_header(self):
        header = QWidget(self)
        header.setObjectName("custom_composite_header")
        header.setFixedHeight(82)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(9)

        identity = QVBoxLayout()
        title_row = QHBoxLayout()
        title = QLabel("CUSTOM COMPOSITE WORKBENCH")
        title.setObjectName("custom_composite_title")
        chip = QLabel("USER GRAPH · EXPANDED TOPOLOGY")
        chip.setObjectName("custom_composite_chip")
        title_row.addWidget(title)
        title_row.addWidget(chip)
        title_row.addStretch()
        identity.addLayout(title_row)

        fields = QHBoxLayout()
        fields.setSpacing(7)
        self._definition_combo = QComboBox(header)
        self._definition_combo.setObjectName("custom_composite_definition_combo")
        self._definition_combo.setAccessibleName("选择已有自定义组合模块")
        self._definition_combo.setMinimumWidth(180)
        self._name_edit = QLineEdit(header)
        self._name_edit.setObjectName("custom_composite_name_edit")
        self._name_edit.setAccessibleName("自定义组合模块名称")
        self._name_edit.setPlaceholderText("组合模块名称（必填）")
        self._name_edit.setMinimumWidth(190)
        self._description_edit = QLineEdit(header)
        self._description_edit.setObjectName("custom_composite_description_edit")
        self._description_edit.setAccessibleName("自定义组合模块说明")
        self._description_edit.setPlaceholderText("用途说明（可选）")
        self._description_edit.setMinimumWidth(230)
        fields.addWidget(self._definition_combo)
        fields.addWidget(self._name_edit)
        fields.addWidget(self._description_edit, 1)
        identity.addLayout(fields)
        layout.addLayout(identity, 1)

        self._new_btn = QPushButton("新建", header)
        self._new_btn.setObjectName("custom_composite_new_button")
        self._delete_btn = QPushButton("删除", header)
        self._delete_btn.setObjectName("custom_composite_delete_button")
        self._save_btn = QPushButton("保存到模块库", header)
        self._save_btn.setObjectName("custom_composite_save_button")
        self._save_btn.setAccessibleName("保存自定义组合模块")
        self._save_btn.setProperty("variant", "primary")
        layout.addWidget(self._new_btn)
        layout.addWidget(self._delete_btn)
        layout.addWidget(self._save_btn)

        self._definition_combo.currentIndexChanged.connect(self._definition_changed)
        self._new_btn.clicked.connect(self.new_definition)
        self._delete_btn.clicked.connect(self._confirm_delete_current)
        self._save_btn.clicked.connect(self._save_clicked)
        return header

    def _build_body(self):
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setObjectName("custom_composite_splitter")
        splitter.setChildrenCollapsible(False)

        left_panel = QWidget(splitter)
        left_panel.setObjectName("custom_composite_left_panel")
        left_panel.setMinimumWidth(220)
        left_panel.setMaximumWidth(290)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 14, 12, 14)
        left_layout.setSpacing(8)
        eyebrow = QLabel("SOURCE MODULES")
        eyebrow.setProperty("role", "eyebrow")
        left_layout.addWidget(eyebrow)
        source_title = QLabel("非组合模块")
        source_title.setProperty("role", "sectionTitle")
        left_layout.addWidget(source_title)
        self._palette_search = QLineEdit(left_panel)
        self._palette_search.setObjectName("custom_composite_palette_search")
        self._palette_search.setPlaceholderText("搜索可用模块…")
        self._palette_search.setClearButtonEnabled(True)
        self._add_module_btn = QPushButton("＋ 添加", left_panel)
        self._add_module_btn.setObjectName("custom_composite_add_module_button")
        self._add_module_btn.setAccessibleName("添加选中的非组合模块")
        self.palette = ComponentPalette(
            include_builtin_composites=False,
            include_custom_section=False,
        )
        self.palette.setObjectName("custom_composite_source_palette")
        self._palette_search.textChanged.connect(self.palette.filter_items)
        self.palette.itemActivated.connect(self._add_palette_module)
        self._add_module_btn.clicked.connect(
            lambda _checked=False: self._add_palette_module(self.palette.currentItem())
        )
        palette_tools = QHBoxLayout()
        palette_tools.setSpacing(6)
        palette_tools.addWidget(self._palette_search, 1)
        palette_tools.addWidget(self._add_module_btn)
        left_layout.addLayout(palette_tools)
        left_layout.addWidget(self.palette, 1)
        hint = QLabel("拖动模块到中央画布，或选中后按回车加入；从输出端口拖到输入端口建立内部连接。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6C7685; font-size: 10px;")
        left_layout.addWidget(hint)

        canvas_host = QFrame(splitter)
        canvas_host.setObjectName("custom_composite_canvas_host")
        canvas_layout = QVBoxLayout(canvas_host)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)
        canvas_toolbar = QWidget(canvas_host)
        canvas_toolbar.setObjectName("custom_composite_canvas_toolbar")
        toolbar_layout = QHBoxLayout(canvas_toolbar)
        toolbar_layout.setContentsMargins(10, 7, 10, 7)
        toolbar_layout.setSpacing(7)
        canvas_label = QLabel("TOPOLOGY / INTERNAL ROUTES")
        canvas_label.setProperty("role", "eyebrow")
        toolbar_layout.addWidget(canvas_label)
        toolbar_layout.addStretch()
        delete_selected = QPushButton("移除选中模块")
        delete_selected.setObjectName("custom_composite_remove_selected_button")
        clear_canvas = QPushButton("清空工作台")
        clear_canvas.setObjectName("custom_composite_clear_button")
        toolbar_layout.addWidget(delete_selected)
        toolbar_layout.addWidget(clear_canvas)
        delete_selected.clicked.connect(self.remove_selected_nodes)
        clear_canvas.clicked.connect(self._confirm_clear_canvas)
        canvas_layout.addWidget(canvas_toolbar)
        canvas_layout.addWidget(self.view, 1)

        right_panel = QWidget(splitter)
        right_panel.setObjectName("custom_composite_right_panel")
        right_panel.setMinimumWidth(280)
        right_panel.setMaximumWidth(360)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 14, 14, 14)
        right_layout.setSpacing(8)
        inspector_label = QLabel("INSPECTOR")
        inspector_label.setProperty("role", "eyebrow")
        right_layout.addWidget(inspector_label)
        self._inspector_title = QLabel("模块参数快照")
        self._inspector_title.setProperty("role", "sectionTitle")
        right_layout.addWidget(self._inspector_title)
        self._right_tabs = QTabWidget(right_panel)
        self._right_tabs.setObjectName("custom_composite_right_tabs")
        parameter_tab = QWidget(self._right_tabs)
        parameter_layout = QVBoxLayout(parameter_tab)
        parameter_layout.setContentsMargins(0, 0, 0, 0)
        self._inspector_scroll = QScrollArea(parameter_tab)
        self._inspector_scroll.setWidgetResizable(True)
        self._inspector_container = QWidget()
        self._inspector_layout = QVBoxLayout(self._inspector_container)
        self._inspector_layout.setContentsMargins(0, 0, 0, 0)
        self._inspector_layout.setSpacing(7)
        self._inspector_scroll.setWidget(self._inspector_container)
        parameter_layout.addWidget(self._inspector_scroll)

        black_box_tab = QWidget(self._right_tabs)
        black_box_layout = QVBoxLayout(black_box_tab)
        black_box_layout.setContentsMargins(7, 8, 7, 8)
        black_box_layout.setSpacing(7)
        help_label = QLabel("系统默认暴露未连接的边界端口和全部可编辑参数；取消勾选即可隐藏，双击最后一列可改黑盒标签。")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #6C7685; font-size: 10px;")
        black_box_layout.addWidget(help_label)
        interface_label = QLabel("黑盒输入 / 输出")
        interface_label.setProperty("role", "sectionTitle")
        black_box_layout.addWidget(interface_label)
        self._interface_tree = QTreeWidget(black_box_tab)
        self._interface_tree.setObjectName("custom_composite_interface_tree")
        self._interface_tree.setHeaderLabels(["暴露", "内部端口", "黑盒标签"])
        self._interface_tree.setAlternatingRowColors(True)
        self._interface_tree.setRootIsDecorated(False)
        black_box_layout.addWidget(self._interface_tree, 1)
        parameter_label = QLabel("黑盒参数窗口")
        parameter_label.setProperty("role", "sectionTitle")
        black_box_layout.addWidget(parameter_label)
        self._parameter_tree = QTreeWidget(black_box_tab)
        self._parameter_tree.setObjectName("custom_composite_parameter_tree")
        self._parameter_tree.setHeaderLabels(["暴露", "内部参数", "黑盒标签"])
        self._parameter_tree.setAlternatingRowColors(True)
        self._parameter_tree.setRootIsDecorated(False)
        black_box_layout.addWidget(self._parameter_tree, 1)
        self._interface_tree.itemChanged.connect(self._settings_item_changed)
        self._parameter_tree.itemChanged.connect(self._settings_item_changed)

        self._right_tabs.addTab(parameter_tab, "模块参数")
        self._right_tabs.addTab(black_box_tab, "接口与参数")
        right_layout.addWidget(self._right_tabs, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(canvas_host)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([235, 850, 315])
        return splitter

    def _add_palette_module(self, item):
        if item is None or not (item.flags() & Qt.ItemIsDragEnabled):
            return None
        component_name = item.text()
        module_cls = self.view.module_factory.get(component_name)
        if module_cls is None:
            return None
        idx = self.view._alloc_index(component_name)
        if idx is None:
            self._set_status(f"{component_name} 已达到可用实例上限", error=True)
            return None
        existing_count = len(
            [entry for entry in self.scene.items() if isinstance(entry, NodeItem)]
        )
        viewport_center = self.view.mapToScene(self.view.viewport().rect().center())
        column = existing_count % 3
        row = existing_count // 3
        position = QPointF(
            viewport_center.x() + (column - 1) * 210.0,
            viewport_center.y() + row * 170.0,
        )
        try:
            node = module_cls(component_name, idx, position)
            self.view._apply_mode_to_node(node)
            self.scene.addItem(node)
            node.setSelected(True)
            self._schedule_summary_refresh()
            self._set_status(f"已加入 {node.display_name} · 可拖动调整位置")
            return node
        except Exception:
            self.view._free_index(component_name, idx)
            raise

    def _build_status_bar(self):
        status = QWidget(self)
        status.setObjectName("custom_composite_status_bar")
        status.setFixedHeight(40)
        layout = QHBoxLayout(status)
        layout.setContentsMargins(14, 6, 14, 6)
        self._status_label = QLabel("新建组合模块 · 等待拖入非组合模块")
        self._status_label.setObjectName("custom_composite_status")
        self._count_label = QLabel("0 modules · 0 routes")
        self._count_label.setObjectName("custom_composite_counts")
        layout.addWidget(self._status_label, 1)
        layout.addWidget(self._count_label)
        return status

    def _set_status(self, text, error=False):
        self._status_label.setText(str(text))
        self._status_label.setStyleSheet(
            "color: #A4003B;" if error else "color: #1F7A64;"
        )

    def _schedule_summary_refresh(self):
        if self._refresh_pending:
            return
        self._refresh_pending = True
        QTimer.singleShot(0, self._refresh_summary)

    def _refresh_summary(self):
        self._refresh_pending = False
        nodes = [item for item in self.scene.items() if isinstance(item, NodeItem)]
        edges = [item for item in self.scene.items() if isinstance(item, EdgeItem)]
        self._count_label.setText(f"{len(nodes)} modules · {len(edges)} routes")
        self._refresh_black_box_settings()

    def _ensure_local_id(self, node):
        local_id = getattr(node, "_custom_local_id", None)
        if not local_id:
            local_id = f"n_{uuid.uuid4().hex[:10]}"
            node._custom_local_id = local_id
        return str(local_id)

    def _capture_tree_overrides(self):
        if self._settings_rebuilding:
            return
        if hasattr(self, "_interface_tree"):
            for row in range(self._interface_tree.topLevelItemCount()):
                item = self._interface_tree.topLevelItem(row)
                data = item.data(0, Qt.UserRole)
                if isinstance(data, dict):
                    self._interface_overrides[data["candidate_key"]] = {
                        "checked": item.checkState(0) == Qt.Checked,
                        "label": item.text(2).strip(),
                    }
        if hasattr(self, "_parameter_tree"):
            for row in range(self._parameter_tree.topLevelItemCount()):
                item = self._parameter_tree.topLevelItem(row)
                data = item.data(0, Qt.UserRole)
                if isinstance(data, dict):
                    self._parameter_overrides[data["candidate_key"]] = {
                        "checked": item.checkState(0) == Qt.Checked,
                        "label": item.text(2).strip(),
                    }

    def _settings_item_changed(self, *_):
        if not self._settings_rebuilding:
            self._capture_tree_overrides()

    @staticmethod
    def _signals_for_port(port):
        signals = port.get_signals()
        return [str(value) for value in signals] if isinstance(signals, (list, tuple, set)) else [str(signals)]

    def _port_candidates(self):
        connected_inputs = set()
        connected_outputs = set()
        for edge in self.scene.items():
            if isinstance(edge, EdgeItem):
                connected_outputs.add(edge.start_port)
                connected_inputs.add(edge.end_port)
        candidates = []
        nodes = sorted(
            [item for item in self.scene.items() if isinstance(item, NodeItem)],
            key=lambda node: (float(node.pos().x()), float(node.pos().y()), node.component_name),
        )
        for node in nodes:
            local_id = self._ensure_local_id(node)
            for index, port in enumerate(node.in_ports):
                if port in connected_inputs:
                    continue
                candidates.append(
                    {
                        "candidate_key": f"input:{local_id}:{index}",
                        "port_type": "input",
                        "key": f"input_{local_id}_{index}",
                        "label": f"输入 · {node.display_name} / {node.inputs_display_name[index]}",
                        "source": f"{node.display_name}.In{index + 1}",
                        "node_id": local_id,
                        "port_index": index,
                        "signals": self._signals_for_port(port),
                    }
                )
            for index, port in enumerate(node.out_ports):
                if port in connected_outputs:
                    continue
                candidates.append(
                    {
                        "candidate_key": f"output:{local_id}:{index}",
                        "port_type": "output",
                        "key": f"output_{local_id}_{index}",
                        "label": f"输出 · {node.display_name} / {node.outputs_display_name[index]}",
                        "source": f"{node.display_name}.Out{index + 1}",
                        "node_id": local_id,
                        "port_index": index,
                        "signals": self._signals_for_port(port),
                    }
                )
        return candidates

    def _parameter_candidates(self):
        candidates = []
        nodes = sorted(
            [item for item in self.scene.items() if isinstance(item, NodeItem)],
            key=lambda node: (float(node.pos().x()), float(node.pos().y()), node.component_name),
        )
        for node in nodes:
            local_id = self._ensure_local_id(node)
            current = node.get_params() if hasattr(node, "get_params") else {}
            for field in node.param_schema() if hasattr(node, "param_schema") else []:
                if not isinstance(field, dict) or not field.get("key"):
                    continue
                if field.get("free") is False:
                    continue
                target_key = str(field["key"])
                candidate = {
                    key: copy.deepcopy(value)
                    for key, value in field.items()
                    if key in {"type", "min", "max", "unit", "decimals", "options", "note"}
                }
                candidate.update(
                    {
                        "candidate_key": f"parameter:{local_id}:direct:{target_key}",
                        "key": f"p_{local_id}_{target_key}",
                        "label": f"{node.display_name} · {field.get('label', target_key)}",
                        "source": f"{node.display_name}.{field.get('label', target_key)}",
                        "default": copy.deepcopy(current.get(target_key, field.get("default", 0))),
                        "mapping": {
                            "node_id": local_id,
                            "kind": "direct",
                            "target_key": target_key,
                        },
                    }
                )
                candidates.append(candidate)
            for method in node.special_methods_schema() if hasattr(node, "special_methods_schema") else []:
                method_name = str(method.get("name", ""))
                stored_args = getattr(node, "_special_method_args", {}).get(method_name, {})
                for field in method.get("params", []):
                    if not isinstance(field, dict) or not field.get("key"):
                        continue
                    target_key = str(field["key"])
                    candidate = {
                        key: copy.deepcopy(value)
                        for key, value in field.items()
                        if key in {"type", "min", "max", "unit", "decimals", "options", "note"}
                    }
                    candidate.update(
                        {
                            "candidate_key": f"parameter:{local_id}:special:{method_name}:{target_key}",
                            "key": f"p_{local_id}_{method_name}_{target_key}",
                            "label": f"{node.display_name} · {field.get('label', target_key)}",
                            "source": f"{node.display_name}.{method.get('label', method_name)} / {field.get('label', target_key)}",
                            "default": copy.deepcopy(stored_args.get(target_key, field.get("default", 0))),
                            "mapping": {
                                "node_id": local_id,
                                "kind": "special",
                                "method_name": method_name,
                                "target_key": target_key,
                            },
                        }
                    )
                    candidates.append(candidate)
        return candidates

    def _refresh_black_box_settings(self):
        if not hasattr(self, "_interface_tree"):
            return
        self._capture_tree_overrides()
        self._settings_rebuilding = True
        try:
            self._interface_tree.clear()
            for candidate in self._port_candidates():
                override = self._interface_overrides.get(candidate["candidate_key"], {})
                item = QTreeWidgetItem(
                    ["", candidate["source"], override.get("label") or candidate["label"]]
                )
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
                item.setCheckState(0, Qt.Checked if override.get("checked", True) else Qt.Unchecked)
                item.setData(0, Qt.UserRole, candidate)
                self._interface_tree.addTopLevelItem(item)
            self._parameter_tree.clear()
            for candidate in self._parameter_candidates():
                override = self._parameter_overrides.get(candidate["candidate_key"], {})
                item = QTreeWidgetItem(
                    ["", candidate["source"], override.get("label") or candidate["label"]]
                )
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
                item.setCheckState(0, Qt.Checked if override.get("checked", True) else Qt.Unchecked)
                item.setData(0, Qt.UserRole, candidate)
                self._parameter_tree.addTopLevelItem(item)
            for tree in (self._interface_tree, self._parameter_tree):
                tree.resizeColumnToContents(0)
                tree.resizeColumnToContents(1)
        finally:
            self._settings_rebuilding = False

    def _selected_black_box_settings(self):
        self._capture_tree_overrides()
        inputs = []
        outputs = []
        for row in range(self._interface_tree.topLevelItemCount()):
            item = self._interface_tree.topLevelItem(row)
            if item.checkState(0) != Qt.Checked:
                continue
            candidate = copy.deepcopy(item.data(0, Qt.UserRole))
            candidate.pop("candidate_key", None)
            candidate.pop("source", None)
            port_type = candidate.pop("port_type")
            candidate["label"] = item.text(2).strip() or candidate["label"]
            (inputs if port_type == "input" else outputs).append(candidate)
        parameters = []
        for row in range(self._parameter_tree.topLevelItemCount()):
            item = self._parameter_tree.topLevelItem(row)
            if item.checkState(0) != Qt.Checked:
                continue
            candidate = copy.deepcopy(item.data(0, Qt.UserRole))
            candidate.pop("candidate_key", None)
            candidate.pop("source", None)
            candidate["label"] = item.text(2).strip() or candidate["label"]
            parameters.append(candidate)
        return inputs, outputs, parameters

    def _clear_inspector(self):
        while self._inspector_layout.count():
            item = self._inspector_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _show_inspector_placeholder(self):
        self._clear_inspector()
        label = QLabel("双击画布中的模块，可编辑并保存该模块的参数快照。")
        label.setWordWrap(True)
        label.setStyleSheet("color: #6C7685; padding: 8px;")
        self._inspector_layout.addWidget(label)
        self._inspector_layout.addStretch()

    def _cache_node_params(self, node, params):
        node._stage_param_cache_update(dict(params or {}))
        node._commit_pending_cache_update()
        self._set_status(f"已更新 {node.display_name} 的参数快照")

    def _cache_special_method(self, node, method_name, args):
        node._stage_special_method_cache_update(method_name, dict(args or {}))
        node._commit_pending_cache_update()
        self._set_status(f"已更新 {node.display_name}.{method_name} 设计快照")

    def _open_node_inspector(self, node):
        self._clear_inspector()
        self._inspector_title.setText(f"{node.display_name} · 参数快照")
        schema = node.param_schema() if hasattr(node, "param_schema") else []
        special_methods = node.special_methods_schema() if hasattr(node, "special_methods_schema") else []

        if schema:
            companion = None
            if isinstance(node, ModulePID):
                companion = lambda parent: PIDParamCanvas(parent)
            param_widget = ParamDialog(
                schema,
                node.get_params(),
                parent=self,
                apply_callback=lambda params, target=node: self._cache_node_params(target, params),
                companion_widget_factory=companion,
            )
            param_widget.setWindowFlags(Qt.Widget)
            self._inspector_layout.addWidget(param_widget)

        if special_methods:
            apply_callback = lambda method, args, target=node: self._cache_special_method(target, method, args)
            if isinstance(node, ModuleFIRFilter):
                special_widget = FIRDesignerWidget(
                    parent=self,
                    apply_callback=apply_callback,
                    initial_values=getattr(node, "_special_method_args", {}),
                )
            elif isinstance(node, ModuleIIRFilter):
                special_widget = IIRDesignerWidget(
                    parent=self,
                    apply_callback=apply_callback,
                    initial_values=getattr(node, "_special_method_args", {}),
                )
            else:
                special_widget = SpecialMethodDialog(
                    special_methods,
                    parent=self,
                    apply_callback=apply_callback,
                    initial_values=getattr(node, "_special_method_args", {}),
                )
            special_widget.setWindowFlags(Qt.Widget)
            self._inspector_layout.addWidget(special_widget)

        if not schema and not special_methods:
            label = QLabel("该模块没有可编辑参数；其端口与拓扑仍会保存。")
            label.setWordWrap(True)
            label.setStyleSheet("color: #6C7685; padding: 8px;")
            self._inspector_layout.addWidget(label)
        self._inspector_layout.addStretch()
        return True

    def serialize_definition(self):
        # Flush the zero-delay scene summary before reading check states.  This
        # also covers programmatic/Agent graph edits that happen in one event turn.
        self._refresh_black_box_settings()
        nodes = sorted(
            [item for item in self.scene.items() if isinstance(item, NodeItem)],
            key=lambda node: (float(node.pos().x()), float(node.pos().y()), node.component_name, int(node.index)),
        )
        if not nodes:
            raise ValueError("请至少拖入一个非组合模块")
        min_x = min(float(node.pos().x()) for node in nodes)
        min_y = min(float(node.pos().y()) for node in nodes)
        local_ids = {node: self._ensure_local_id(node) for node in nodes}
        serialized_nodes = []
        for node in nodes:
            direct_params = node.get_params() if hasattr(node, "get_params") else {}
            serialized_nodes.append(
                {
                    "local_id": local_ids[node],
                    "component_name": node.component_name,
                    "pos": {
                        "x": float(node.pos().x()) - min_x,
                        "y": float(node.pos().y()) - min_y,
                    },
                    "direct_params": copy.deepcopy(direct_params) if isinstance(direct_params, dict) else {},
                    "special_methods": copy.deepcopy(getattr(node, "_special_method_args", {})),
                }
            )

        serialized_edges = []
        for edge in self.scene.items():
            if not isinstance(edge, EdgeItem):
                continue
            src_node = getattr(edge.start_port, "parent_node", None)
            dst_node = getattr(edge.end_port, "parent_node", None)
            if src_node not in local_ids or dst_node not in local_ids:
                continue
            serialized_edges.append(
                {
                    "src": {
                        "node_id": local_ids[src_node],
                        "port_index": int(edge.start_port.index),
                    },
                    "dst": {
                        "node_id": local_ids[dst_node],
                        "port_index": int(edge.end_port.index),
                    },
                }
            )
        inputs, outputs, parameters = self._selected_black_box_settings()
        return {
            "name": self._name_edit.text().strip(),
            "description": self._description_edit.text().strip(),
            "nodes": serialized_nodes,
            "edges": serialized_edges,
            "inputs": inputs,
            "outputs": outputs,
            "parameters": parameters,
        }

    def save_current_definition(self):
        definition = self.serialize_definition()
        saved = self.library.save_definition(
            definition,
            definition_id=self._current_definition_id,
        )
        self._current_definition_id = saved["id"]
        self._refresh_definition_combo()
        self._set_status(f"“{saved['name']}”已保存到自定义组合模块库")
        return saved

    def _save_clicked(self):
        try:
            self.save_current_definition()
        except Exception as exc:
            self._set_status(str(exc), error=True)

    def _refresh_definition_combo(self):
        current_id = self._current_definition_id
        self._definition_combo.blockSignals(True)
        self._definition_combo.clear()
        self._definition_combo.addItem("＋ 新建组合模块", None)
        for definition in self.library.definitions():
            self._definition_combo.addItem(definition["name"], definition["id"])
        index = self._definition_combo.findData(current_id)
        self._definition_combo.setCurrentIndex(index if index >= 0 else 0)
        self._definition_combo.blockSignals(False)
        self._delete_btn.setEnabled(current_id is not None and index >= 0)

    def _definition_changed(self, _index):
        definition_id = self._definition_combo.currentData()
        if definition_id is None:
            self.new_definition()
            return
        definition = self.library.get(definition_id)
        if definition is not None:
            self.load_definition(definition)

    def new_definition(self, *_):
        self._current_definition_id = None
        self._interface_overrides.clear()
        self._parameter_overrides.clear()
        self._name_edit.clear()
        self._description_edit.clear()
        self.clear_canvas()
        self._refresh_definition_combo()
        self._set_status("新建组合模块 · 等待拖入非组合模块")

    def load_definition(self, definition):
        self.clear_canvas()
        self._current_definition_id = definition.get("id")
        self._interface_overrides = {
            f"{port_type}:{port.get('node_id')}:{int(port.get('port_index', 0))}": {
                "checked": True,
                "label": port.get("label", ""),
            }
            for port_type, items in (("input", definition.get("inputs", [])), ("output", definition.get("outputs", [])))
            for port in items
        }
        self._parameter_overrides = {}
        for parameter in definition.get("parameters", []):
            mapping = parameter.get("mapping", {})
            if mapping.get("kind") == "special":
                key = f"parameter:{mapping.get('node_id')}:special:{mapping.get('method_name')}:{mapping.get('target_key')}"
            else:
                key = f"parameter:{mapping.get('node_id')}:direct:{mapping.get('target_key')}"
            self._parameter_overrides[key] = {
                "checked": True,
                "label": parameter.get("label", ""),
            }
        self._name_edit.setText(definition.get("name", ""))
        self._description_edit.setText(definition.get("description", ""))
        self._load_internal_graph(definition)
        self.view.auto_fit_nodes(max_scale=1.0)
        self._refresh_summary()
        self._refresh_definition_combo()
        self._set_status(f"正在编辑“{definition.get('name', '')}”")

    def _load_internal_graph(self, definition):
        node_map = {}
        for spec in definition.get("nodes", []):
            component_name = spec.get("component_name")
            module_cls = self.view.module_factory.get(component_name)
            if module_cls is None:
                continue
            idx = self.view._alloc_index(component_name)
            if idx is None:
                continue
            pos = spec.get("pos", {})
            node = module_cls(
                component_name,
                idx,
                QPointF(float(pos.get("x", 0.0)), float(pos.get("y", 0.0))),
            )
            node._custom_local_id = str(spec.get("local_id"))
            direct_params = spec.get("direct_params", {})
            if isinstance(direct_params, dict) and direct_params:
                node._stage_param_cache_update(direct_params)
                node._commit_pending_cache_update()
            node._special_method_args = copy.deepcopy(spec.get("special_methods", {}))
            self.scene.addItem(node)
            node_map[node._custom_local_id] = node
        for edge in definition.get("edges", []):
            src = edge.get("src", {})
            dst = edge.get("dst", {})
            src_node = node_map.get(src.get("node_id"))
            dst_node = node_map.get(dst.get("node_id"))
            src_index = int(src.get("port_index", -1))
            dst_index = int(dst.get("port_index", -1))
            if (
                src_node is not None
                and dst_node is not None
                and 0 <= src_index < len(src_node.out_ports)
                and 0 <= dst_index < len(dst_node.in_ports)
            ):
                self.scene.create_connection(src_node.out_ports[src_index], dst_node.in_ports[dst_index])
        self._refresh_black_box_settings()

    def _confirm_delete_current(self):
        if self._current_definition_id is None:
            return
        name = self._name_edit.text().strip()
        reply = QMessageBox.question(
            self,
            "删除自定义组合模块",
            f"确定从模块库删除“{name}”吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.library.delete(self._current_definition_id)
            self.new_definition()

    def clear_canvas(self):
        for edge in [item for item in self.scene.items() if isinstance(item, EdgeItem)]:
            edge.remove()
        for node in [item for item in self.scene.items() if isinstance(item, NodeItem)]:
            self.view._free_index(node.component_name, int(node.index))
            self.scene.removeItem(node)
        self.scene.clearSelection()
        self._show_inspector_placeholder()
        self._inspector_title.setText("模块参数快照")
        self._refresh_summary()

    def _confirm_clear_canvas(self):
        if not any(isinstance(item, NodeItem) for item in self.scene.items()):
            return
        reply = QMessageBox.question(
            self,
            "清空组合工作台",
            "确定移除工作台中的全部模块和内部连线吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.clear_canvas()
            self._set_status("工作台已清空")

    def remove_selected_nodes(self):
        selected = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        for node in selected:
            for edge in list(node.edges):
                edge.remove()
            self.view._free_index(node.component_name, int(node.index))
            self.scene.removeItem(node)
        if selected:
            self._show_inspector_placeholder()
            self._refresh_summary()
            self._set_status(f"已移除 {len(selected)} 个模块")

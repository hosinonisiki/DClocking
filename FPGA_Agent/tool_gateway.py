"""Application-owned safety and Qt-thread boundary for every Agent runtime.

The model proposes typed calls; it cannot grant itself operator approval.  Qt
work is queued onto the application's thread, and approvals are non-modal.
Cancellation invalidates pending work without requiring the GUI event loop to
run. Once a synchronous tool has started, it completes atomically: cancelling
an Agent is not a rollback or an emergency hardware-stop command.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
import json
import keyword
import math
import re
import threading
import uuid

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication

from tool_definitions import TOOLS


_SCHEMAS = {item["function"]["name"]: item["function"]["parameters"] for item in TOOLS}
_READ_ONLY = frozenset({"list_modules", "get_module_info"})
_HARDWARE_TOOLS = frozenset({"create_module", "connect_modules", "disconnect_module",
                             "set_parameter", "clear_canvas"})
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
_MODULE_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*\Z")
_SCHEMA_NAMES = {
    "PID控制器": "PID_SCHEMA", "累加器": "ACCM_SCHEMA", "线性缩放器": "SCLR_SCHEMA",
    "线性放大器": "SCLR_SCHEMA", "FIR滤波器": "FIRF_SCHEMA", "IIR滤波器": "IIR_SCHEMA",
    "线性变换器": "LTRN_SCHEMA", "线性变换": "LTRN_SCHEMA", "PDH状态机": "PDH_SCHEMA",
    "LO自动校准状态机": "SCLO_SCHEMA",
}


def _finite_json(value, depth=0):
    if depth > 12:
        raise ValueError("Tool arguments are nested too deeply")
    if isinstance(value, dict):
        if len(value) > 128 or any(type(key) is not str for key in value):
            raise ValueError("Tool objects require bounded string keys")
        for item in value.values():
            _finite_json(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 128:
            raise ValueError("Tool arrays are limited to 128 items")
        for item in value:
            _finite_json(item, depth + 1)
    elif type(value) in (int, float):
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError("Tool arguments require finite numeric values")
    elif type(value) is str:
        if len(value) > 8192 or "\x00" in value:
            raise ValueError("Tool text is too long or contains a NUL character")
    elif value is not None and type(value) is not bool:
        raise ValueError("Tool arguments must be JSON values")


def _validate_schema(value, schema, path="arguments"):
    kind = schema.get("type")
    allowed = {
        "object": lambda: type(value) is dict,
        "array": lambda: type(value) is list,
        "string": lambda: type(value) is str,
        "number": lambda: type(value) in (int, float),
        "integer": lambda: type(value) is int,
        "boolean": lambda: type(value) is bool,
    }
    if kind in allowed and not allowed[kind]():
        raise ValueError(f"{path} must be {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is not an allowed value")
    if kind == "object":
        missing = set(schema.get("required", ())) - value.keys()
        if missing:
            raise ValueError(f"{path} is missing {', '.join(sorted(missing))}")
        if "properties" in schema:
            properties = schema["properties"]
            unknown = value.keys() - properties.keys()
            if unknown:
                raise ValueError(f"{path} contains unknown fields: {', '.join(sorted(unknown))}")
            for key, item in value.items():
                _validate_schema(item, properties[key], f"{path}.{key}")
    elif kind == "array":
        for index, item in enumerate(value):
            _validate_schema(item, schema.get("items", {}), f"{path}[{index}]")


def _validate_parameters(params, fields):
    fields = {field["key"]: field for field in fields if field.get("key")}
    for key, value in params.items():
        if key not in fields:
            raise ValueError(f"Unknown or unavailable parameter: {key}")
        field = fields[key]
        kind = field.get("type")
        if kind in ("float", "int"):
            if type(value) not in ((int,) if kind == "int" else (int, float)):
                raise ValueError(f"Parameter {key} requires {kind}, not text or boolean")
            if "min" in field and value < field["min"]:
                raise ValueError(f"Parameter {key} is below minimum {field['min']}")
            if "max" in field and value > field["max"]:
                raise ValueError(f"Parameter {key} exceeds maximum {field['max']}")
        elif kind == "bool":
            if type(value) is not bool:
                raise ValueError(f"Parameter {key} requires a JSON boolean")
        elif kind in ("str", "string", "choice", "enum"):
            if type(value) is not str:
                raise ValueError(f"Parameter {key} requires text")
        else:
            raise ValueError(f"Parameter {key} has no safe typed schema; use its dedicated editor")
        if "options" in field and value not in field["options"]:
            raise ValueError(f"Parameter {key} is not an allowed option")


@dataclass
class _Call:
    name: str
    args: dict
    run_id: str
    call_id: str
    cancel_event: object
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    done: threading.Event = field(default_factory=threading.Event)
    result: str = ""
    executing: bool = False
    awaiting_approval: bool = False
    approval_context: tuple = ()
    direct: bool = False


class ToolGateway(QObject):
    """Dispatch validated calls, with per-call approval and correlated receipts.

    Construct on the QApplication thread. ``dispatch`` may be called by a
    background runtime; GUI callers may run non-approval tools directly, but
    cannot synchronously wait for approval. ``cancel_pending(run_id)`` is
    thread-safe and permanently invalidates that run ID. ``shutdown`` prevents
    all future calls. No method pumps a nested Qt event loop.
    """

    supports_run_context = True
    approval_requested = Signal(str, str, object)
    approval_finished = Signal(str)
    audit_recorded = Signal(object)
    _requested = Signal(object)

    def __init__(self, executor, bridge, parent=None):
        super().__init__(parent)
        app = QApplication.instance()
        if app is None or QThread.currentThread() != app.thread():
            raise RuntimeError("ToolGateway must be created on the QApplication thread")
        self._executor = executor
        self._bridge = bridge
        self._lock = threading.RLock()
        self._pending = {}
        self._invalid_runs = set()
        self._closed = False
        self._requested.connect(self._handle, Qt.QueuedConnection)

    def dispatch(self, name, args, *, cancel_event=None, run_id="", call_id=""):
        call = _Call(name, {}, str(run_id), str(call_id), cancel_event)
        if type(name) is not str or name not in _SCHEMAS:
            self._finish(call, "denied", "Tool is not in the application allowlist")
            return call.result
        try:
            _finite_json(args)
            _validate_schema(args, _SCHEMAS[name])
            if len(json.dumps(args, ensure_ascii=False)) > 65536:
                raise ValueError("Tool arguments exceed the 64 KiB limit")
            call.args = deepcopy(args)
        except (ValueError, TypeError, OverflowError) as exc:
            self._finish(call, "failed", str(exc))
            return call.result
        with self._lock:
            self._pending[call.request_id] = call
            if self._is_cancelled(call):
                self._finish(call, "cancelled", "Tool cancelled before execution")
                return call.result
        if QThread.currentThread() == self.thread():
            call.direct = True
            self._handle(call)
        else:
            self._requested.emit(call)
        while not call.done.wait(0.02):
            with self._lock:
                if self._is_cancelled(call) and not call.executing:
                    self._finish(call, "cancelled", "Tool cancelled before execution")
        return call.result

    def cancel_pending(self, run_id=None):
        """Cancel queued calls, never interrupt an in-flight hardware operation."""
        with self._lock:
            if run_id is not None:
                self._invalid_runs.add(str(run_id))
            for call in tuple(self._pending.values()):
                if run_id is None or call.run_id == str(run_id):
                    if not call.executing:
                        self._finish(call, "cancelled", "Tool cancelled before execution")

    def shutdown(self):
        with self._lock:
            self._closed = True
        self.cancel_pending()

    def _is_cancelled(self, call):
        return (self._closed or call.run_id in self._invalid_runs
                or (call.cancel_event is not None and call.cancel_event.is_set()))

    @Slot(object)
    def _handle(self, call):
        with self._lock:
            if call.done.is_set():
                return
            if self._is_cancelled(call):
                self._finish(call, "cancelled", "Tool cancelled before execution")
                return
        try:
            self._validate_live(call)
            state = self._transport_state()
            approval = (call.name in {"clear_canvas", "generate_module"}
                        or (call.name == "disconnect_module" and "port_index" not in call.args)
                        or (call.name in _HARDWARE_TOOLS and state != "offline"))
            if approval:
                if call.direct:
                    self._finish(call, "denied", "Operator approval requires a background Agent call")
                    return
                with self._lock:
                    if self._is_cancelled(call):
                        self._finish(call, "cancelled", "Tool cancelled before approval")
                        return
                    call.awaiting_approval = True
                    call.approval_context = self._context(call)
                summary = ("允许 Agent 生成本地模块代码？" if call.name == "generate_module"
                           else "允许 Agent 执行此画布或硬件操作？")
                with self._lock:
                    # Do not deliver a stale approval card after cancellation
                    # has already delivered approval_finished to the GUI.
                    if call.done.is_set() or self._is_cancelled(call):
                        self._finish(call, "cancelled", "Tool cancelled before approval")
                        return
                    self.approval_requested.emit(call.request_id, summary, {
                        "tool": call.name, "arguments": deepcopy(call.args),
                        "run_id": call.run_id, "call_id": call.call_id,
                        "transport_state": state,
                        "warning": "本次授权仅适用于此调用；停止生成不会撤销已执行的硬件操作。",
                    })
                return
            self._execute(call, state)
        except Exception as exc:
            self._finish(call, "failed", str(exc))

    @Slot(str, bool)
    def resolve_approval(self, request_id, approved):
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Approval must be resolved on the GUI thread")
        with self._lock:
            call = self._pending.get(request_id)
            if call is None or not call.awaiting_approval or call.done.is_set():
                return
            call.awaiting_approval = False
            if self._is_cancelled(call):
                self._finish(call, "cancelled", "Tool cancelled while awaiting approval")
                return
        if approved is not True:
            self._finish(call, "denied", "Operator declined this tool call")
            return
        try:
            if call.approval_context != self._context(call):
                self._finish(call, "denied", "Target or device changed; request fresh approval")
                return
            self._validate_live(call)
            self._execute(call, self._transport_state())
        except Exception as exc:
            self._finish(call, "failed", str(exc))

    def _transport_state(self):
        """Only positive evidence of a disconnected transport permits staging."""
        port = getattr(getattr(self._bridge, "_mw", None), "port_ctrl", None)
        observations = []
        try:
            probe = getattr(port, "is_open", None)
            if callable(probe):
                observations.append(bool(probe()))
            serial = getattr(port, "serial_port", None)
            if serial is not None and callable(getattr(serial, "isOpen", None)):
                observations.append(bool(serial.isOpen()))
            controller = getattr(port, "hw_controller", None)
            if controller is not None and hasattr(controller, "ser"):
                observations.append(controller.ser is not None)
        except Exception:
            return "unknown"
        return "online" if any(observations) else "offline" if observations else "unknown"

    def _context(self, call):
        mw = getattr(self._bridge, "_mw", None)
        port = getattr(mw, "port_ctrl", None)
        controller = getattr(port, "hw_controller", None)
        targets = []
        for key in ("node_name", "source_node", "destination_node"):
            if key in call.args:
                node = self._bridge._find_node(call.args[key])
                getter = getattr(node, "get_params", None)
                cache = getter() if callable(getter) else {}
                targets.append((id(node), json.dumps(cache, sort_keys=True, default=str)))
        scene = getattr(self._bridge, "_scene", None)
        # A delayed clear/remove/connect approval must not apply to a newly
        # edited graph. Item identities detect replaced modules and routes.
        graph = tuple(sorted(id(item) for item in scene.items())) if scene is not None else ()
        return (self._transport_state(), id(port), id(controller),
                id(getattr(controller, "ser", None)), tuple(targets), graph)

    def _validate_live(self, call):
        args = call.args
        for key in ("source_port", "destination_port", "port_index"):
            if key in args and not 0 <= args[key] <= 255:
                raise ValueError(f"{key} must be between 0 and 255")
        if call.name == "set_parameter":
            node = self._bridge._find_node(args["node_name"])
            if node is None:
                raise ValueError("Parameter target no longer exists; use list_modules")
            _validate_parameters(args["params"], node.param_schema())
            if getattr(node, "name", "") == "PDHS":
                from pdh_experiment import validate_parameters
                validate_parameters(args["params"], for_write=True)
        elif call.name == "create_module":
            if ("position_x" in args) != ("position_y" in args):
                raise ValueError("Provide both position_x and position_y, or neither")
            for key in ("position_x", "position_y"):
                if abs(args.get(key, 0)) > 1_000_000:
                    raise ValueError("Canvas coordinates exceed the supported range")
            if args.get("params"):
                _validate_parameters(args["params"], self._creation_schema(args["module_type"]))
        elif call.name == "clear_canvas" and args["confirm"] is not True:
            raise ValueError("clear_canvas requires confirm=true plus separate operator approval")
        elif call.name == "generate_module":
            self._validate_generation(args)

    def _creation_schema(self, module_type):
        mw = getattr(self._bridge, "_mw", None)
        library = getattr(mw, "custom_composite_library", None)
        definition = library.find_by_name(module_type) if library is not None else None
        if definition is not None:
            return definition.get("parameters", [])
        schema_name = _SCHEMA_NAMES.get(module_type)
        if schema_name:
            import qt_module_schema
            fields = getattr(qt_module_schema, schema_name)
            # Before allocation use the same active mode as DiagramView.
            developer = bool(getattr(getattr(self._bridge, "_scene", None), "developer_mode", False))
            return fields if developer else [item for item in fields if item.get("free", True)]
        from module_registry import get_module
        module = get_module(module_type) or {}
        return module.get("direct_params", []) + module.get("indirect_params", [])

    def _module_info_receipt(self, module_type, result):
        """Supplement legacy catalog fields with the schema the gateway uses.

        This reads Python metadata only: no node allocation, hardware query or
        generated-code import. Older direct/indirect lists remain for clients
        that use them, but are explicitly labelled as historical reference.
        """
        mw = getattr(self._bridge, "_mw", None)
        library = getattr(mw, "custom_composite_library", None)
        custom = library.find_by_name(module_type) if library is not None else None
        if custom is not None:
            result = {
                "display_name": custom["name"], "purpose": custom.get("description", ""),
                "category": "custom_composite", "max_instances": "limited by contained modules",
                "internal_names": [],
                "instance_note": "Use the exact instance name returned by create_module/list_modules",
            }
            for direction in ("inputs", "outputs"):
                result[direction] = [
                    {"index": index, "name": item.get("key", f"{direction}_{index}"),
                     "display": item.get("label", ""), "signal": list(item.get("signals", []))}
                    for index, item in enumerate(custom.get(direction, []))
                ]
        elif result.get("error") or result.get("success") is False:
            return result
        fields = []
        for field in self._creation_schema(module_type):
            public = {key: deepcopy(value) for key, value in field.items() if key != "mapping"}
            public["agent_writable"] = field.get("type") in {
                "float", "int", "bool", "str", "string", "choice", "enum",
            }
            fields.append(public)
        developer = bool(getattr(getattr(self._bridge, "_scene", None), "developer_mode", False))
        return {
            **result,
            "available_mode": "developer" if developer else "free",
            "parameter_schema": fields,
            "parameter_schema_source": ("custom_composite_library" if custom is not None
                                        else "qt_module_schema" if module_type in _SCHEMA_NAMES
                                        else "module_registry"),
            "parameter_schema_note": (
                "Use parameter_schema for current-mode parameter keys, types, ranges and units. "
                "Only agent_writable=true fields can be set through Agent tools. "
                "Numeric inputs must be finite JSON numbers; boolean inputs must be true/false. "
                "Special infinity values shown by the UI require its dedicated editor."
            ),
            "legacy_parameter_note": (
                "direct_params/indirect_params are legacy catalog reference, not the selected-mode "
                "allowlist or authoritative ranges; prefer parameter_schema."
            ),
        }

    @staticmethod
    def _validate_generation(args):
        name = args["module_name"]
        if len(name) > 64 or not _MODULE_IDENTIFIER.fullmatch(name) or keyword.iskeyword(name):
            raise ValueError("module_name must be a safe lowercase snake_case identifier")
        # Existing templates interpolate these fields as Python source. Never
        # accept syntax escapes even when the operator approves generation.
        text_fields = [args["display_name"], args["description"]]
        for field in args.get("params", []):
            text_fields.extend([field["label"], field.get("note", "")])
        if any(any(char in text for char in ('"', "'", "\\", "\n", "\r", "{", "}"))
               for text in text_fields):
            raise ValueError("Generated labels/descriptions must not contain source-code delimiters")
        if not 1 <= args.get("max_instances", 2) <= 16:
            raise ValueError("max_instances must be between 1 and 16")
        for fields, key in ((args["inputs"], "name"), (args["outputs"], "name"),
                            (args.get("params", []), "key")):
            names = [item[key] for item in fields]
            if len(names) != len(set(names)) or any(
                not _IDENTIFIER.fullmatch(name) or keyword.iskeyword(name) for name in names
            ):
                raise ValueError("Generated ports and parameter keys require unique safe identifiers")
        for param in args.get("params", []):
            if "min" in param and "max" in param and param["min"] > param["max"]:
                raise ValueError("Generated parameter minimum exceeds maximum")
            if "default" in param:
                _validate_parameters({param["key"]: param["default"]}, [param])

    @contextmanager
    def _execution_observer(self, state, call, errors):
        """Observe swallowed GUI errors; offline parameter edits never call I/O."""
        mw = getattr(self._bridge, "_mw", None)
        old_report = getattr(mw, "_report_error", None)
        scene = getattr(self._bridge, "_scene", None)
        old_apply = getattr(scene, "param_apply_handler", None)
        swapped = (state == "offline" and scene is not None
                   and call.name in {"set_parameter", "create_module"})

        def report(message):
            errors.append(str(message))
            if callable(old_report):
                old_report(message)

        def stage(node, params):
            commit = getattr(node, "_commit_pending_cache_update", None)
            if callable(commit):
                commit()

        try:
            if callable(old_report):
                mw._report_error = report
            if swapped:
                scene.param_apply_handler = stage
            yield
        finally:
            if swapped:
                scene.param_apply_handler = old_apply
            if callable(old_report):
                mw._report_error = old_report

    def _execute(self, call, state):
        with self._lock:
            if call.done.is_set() or self._is_cancelled(call):
                self._finish(call, "cancelled", "Tool cancelled before execution")
                return
            call.executing = True
        errors = []
        result = {}
        try:
            with self._execution_observer(state, call, errors):
                raw = self._executor.dispatch(call.name, deepcopy(call.args))
                result = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(result, dict):
                raise ValueError("Tool executor returned a non-object receipt")
            if call.name == "get_module_info":
                result = self._module_info_receipt(call.args["module_type"], result)
            if result.get("error") or result.get("success") is False:
                self._finish(call, "failed", result.get("error", "Tool reported a failure"), result)
            elif errors and (state != "offline" or call.name == "set_parameter"):
                self._finish(call, "failed", "Application reported an execution error; effects may be partial", {
                    **result, "success": False, "execution_errors": errors,
                })
            elif call.name == "set_parameter" and not self._cache_accepted(call):
                self._finish(call, "failed", "Parameter cache did not accept the requested values; check application logs",
                             {**result, "success": False})
            else:
                if state == "offline" and call.name in {"set_parameter", "create_module"}:
                    target = call.args.get("node_name", result.get("node_name"))
                    node = self._bridge._find_node(target) if target else None
                    if node is not None:
                        self._refresh_staged_view(node)
                status = ("read_only" if call.name in _READ_ONLY else
                          "hardware_unverified" if call.name in _HARDWARE_TOOLS and state != "offline"
                          else "local_staged")
                summaries = {
                    "read_only": "Read-only application information; cached values are not hardware readback",
                    "local_staged": "Local change completed; no hardware write confirmed",
                    "hardware_unverified": "Application operation completed; hardware effect/readback not verified",
                }
                self._finish(call, status, summaries[status], result)
        except Exception as exc:
            self._finish(call, "failed", str(exc), result if isinstance(result, dict) else {})

    def _refresh_staged_view(self, node):
        """Reflect cached edits without invoking the device-refresh entrypoint."""
        mw = getattr(self._bridge, "_mw", None)
        key = f"{node.name}@{node.component_name}:{getattr(node, 'index', -1)}"
        panel = getattr(mw, "_param_panels", {}).get(key)
        updater = getattr(mw, "_update_panel_from_node", None)
        if panel is not None and callable(updater):
            updater(panel, node)
        designer = getattr(mw, "_pdh_designers", {}).get(id(node))
        if designer is not None:
            designer.mark_conflict("Agent 已修改本地配置；未写入 FPGA，请刷新并核对原有预览")
        repaint = getattr(node, "update", None)
        if callable(repaint):
            repaint()

    def _cache_accepted(self, call):
        node = self._bridge._find_node(call.args["node_name"])
        if node is None or not callable(getattr(node, "get_params", None)):
            return False
        values = node.get_params()
        # Online indirect parameters may legitimately be quantized by existing
        # hardware conversions. Do not treat equality as hardware verification.
        if self._transport_state() != "offline":
            return True
        return all(key in values and values[key] == value for key, value in call.args["params"].items())

    def _finish(self, call, status, summary, result=None):
        with self._lock:
            if call.done.is_set():
                return
            original = result or {}
            receipt = {
                **original, "status": status, "summary": str(summary),
                "run_id": call.run_id, "call_id": call.call_id,
                "readback_verified": False, "result": original,
                "next_actions": (["Inspect application state before retrying; do not assume rollback"]
                                 if status == "failed" else
                                 ["Stop this operation; obtain new operator approval before retrying"]
                                 if status == "denied" else []),
                "artifacts": original.get("files", []),
            }
            if status in {"failed", "denied", "cancelled"}:
                receipt["success"] = False
                receipt.setdefault("error", str(summary))
            call.result = json.dumps(receipt, ensure_ascii=False, default=str)
            self._pending.pop(call.request_id, None)
            call.done.set()
        self.approval_finished.emit(call.request_id)
        self.audit_recorded.emit(receipt)

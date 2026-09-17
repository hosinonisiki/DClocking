"""Pure, read-only catalog operations exposed by the local MCP server.

The service deliberately depends only on :mod:`module_registry`.  It does not
import Qt, inspect files, create sockets, call an LLM, or write to hardware.
Every public operation returns a bounded, JSON-serializable result so the
transport layer never needs to expose Python tracebacks to an MCP client.
"""

from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any

from . import module_registry as registry

# ``module_registry`` imports this pure-Python file before the MCP service is
# loaded and resolves it from this repository when it is not already on
# ``sys.path``.  Reuse the exact schemas consumed by the Qt nodes so the MCP
# contract cannot silently drift from the desktop parameter editor.
from qt_module_schema import (  # type: ignore[import-not-found]
    ACCM_SCHEMA,
    FIRF_SCHEMA,
    IIR_SCHEMA,
    LTRN_SCHEMA,
    PDH_SCHEMA,
    PID_SCHEMA,
    SCLO_SCHEMA,
    SCLR_SCHEMA,
)


_SAFE_FIELD_COMPONENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")

_AUTHORITATIVE_PARAMETER_SCHEMAS: dict[str, list[dict[str, Any]]] = {
    "PID控制器": PID_SCHEMA,
    "累加器": ACCM_SCHEMA,
    "线性缩放器": SCLR_SCHEMA,
    "FIR滤波器": FIRF_SCHEMA,
    "IIR滤波器": IIR_SCHEMA,
    "线性变换器": LTRN_SCHEMA,
    "PDH状态机": PDH_SCHEMA,
    "LO自动校准状态机": SCLO_SCHEMA,
}

# Constraints that are enforced by the hardware implementation but are only
# described in prose in the shared Qt schema.  Values here remain raw register
# values, not the friendlier values accepted by designer-specific methods.
_PARAMETER_CONSTRAINT_OVERRIDES: dict[tuple[str, str], dict[str, Any]] = {
    ("FIR滤波器", "taps"): {"enum": [15, 31, 63]},
}


class McpCatalogService:
    """Validate module metadata and prospective designs without side effects."""

    MAX_NODES = 256
    MAX_CONNECTIONS = 1024
    MAX_PARAMETERS = 128
    MAX_ERRORS = 100
    MAX_NAME_LENGTH = 128
    MAX_ABS_NUMBER = 1e308

    def list_module_types(self, category: str | None = None) -> dict[str, Any]:
        """Return the placeable module types, optionally filtered by category."""
        entries = self._catalog_entries()
        categories = {entry["category"] for entry in entries}
        if category is not None:
            if type(category) is not str:  # bool and string-like objects are rejected
                return self._failure(
                    self._error("invalid_type", "category", "Category must be a string.")
                )
            if len(category) > self.MAX_NAME_LENGTH:
                return self._failure(
                    self._error(
                        "value_too_long",
                        "category",
                        "Category exceeds the supported length.",
                    )
                )
            if category not in categories:
                return self._failure(
                    self._error(
                        "unknown_category",
                        "category",
                        "Category is not present in the module registry.",
                    )
                )
            entries = [entry for entry in entries if entry["category"] == category]
        return {"ok": True, "count": len(entries), "modules": entries, "errors": []}

    def get_module_spec(self, module_type: str) -> dict[str, Any]:
        """Return a detached copy of one module's complete registry contract."""
        name_error = self._validate_name(module_type, "module_type")
        if name_error:
            return self._failure(name_error)
        resolved = self._lookup_module(module_type)
        if resolved is None:
            return self._failure(
                self._error(
                    "unknown_module",
                    "module_type",
                    "Module type is not present in the registry.",
                )
            )

        kind, raw_spec = resolved
        spec = deepcopy(raw_spec)
        spec["module_type"] = module_type
        spec["kind"] = kind
        spec.setdefault("display_name", module_type)
        spec.setdefault("category", "composite" if kind == "composite" else "unknown")
        spec.setdefault("inputs", [])
        spec.setdefault("outputs", [])
        spec.setdefault("direct_params", [])
        spec.setdefault("indirect_params", [])
        if kind == "composite":
            direct, indirect = self._composite_parameter_specs(raw_spec)
            spec["direct_params"] = direct
            spec["indirect_params"] = indirect
            # Built-in composites are expanded by the Qt canvas and do not
            # exist as ordinary persisted nodes.  Avoid exposing the registry's
            # legacy auto_connections field as a loadable graph contract.
            spec.pop("auto_connections", None)
            spec["design_validation_supported"] = False
            spec["validation_note"] = (
                "Composite metadata is catalog-only; validate the expanded "
                "primitive-module graph instead."
            )
        else:
            direct, indirect = self._module_parameter_specs(module_type, raw_spec)
            spec["direct_params"] = direct
            spec["indirect_params"] = indirect
            spec["design_validation_supported"] = True
        return {"ok": True, "module": spec, "errors": []}

    def validate_parameters(
        self, module_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate only parameters explicitly declared for ``module_type``."""
        name_error = self._validate_name(module_type, "module_type")
        if name_error:
            return self._failure(name_error)
        resolved = self._lookup_module(module_type)
        if resolved is None:
            return self._failure(
                self._error(
                    "unknown_module",
                    "module_type",
                    "Module type is not present in the registry.",
                )
            )
        if type(parameters) is not dict:
            return self._failure(
                self._error(
                    "invalid_type", "parameters", "Parameters must be an object."
                )
            )
        if len(parameters) > self.MAX_PARAMETERS:
            return self._failure(
                self._error(
                    "too_many_parameters",
                    "parameters",
                    "Parameter object exceeds the supported size.",
                )
            )

        kind, raw_spec = resolved
        if kind == "composite":
            direct, indirect = self._composite_parameter_specs(raw_spec)
        else:
            direct, indirect = self._module_parameter_specs(module_type, raw_spec)
        declared = {
            parameter["key"]: parameter
            for parameter in (*direct, *indirect)
            if type(parameter) is dict and type(parameter.get("key")) is str
        }

        errors: list[dict[str, str]] = []
        normalized: dict[str, Any] = {}
        for key in sorted(parameters, key=lambda value: str(value)):
            field = self._parameter_field(key)
            if type(key) is not str:
                errors.append(
                    self._error(
                        "invalid_type", "parameters", "Parameter names must be strings."
                    )
                )
                continue
            if len(key) > self.MAX_NAME_LENGTH:
                errors.append(
                    self._error(
                        "value_too_long", field, "Parameter name is too long."
                    )
                )
                continue
            definition = declared.get(key)
            if definition is None:
                errors.append(
                    self._error(
                        "unknown_parameter",
                        field,
                        "Parameter is not declared for this module type.",
                    )
                )
                continue
            value, value_error = self._normalize_parameter(
                parameters[key], definition, field
            )
            if value_error:
                errors.append(value_error)
            elif module_type == "累加器" and key == "ratio" and not self._is_power_of_two(value):
                errors.append(
                    self._error(
                        "constraint_violation",
                        field,
                        "Accumulator ratio must be a power of two from 1 to 32768.",
                    )
                )
            else:
                normalized[key] = value

        if errors:
            return self._failure(*errors[: self.MAX_ERRORS])
        return {
            "ok": True,
            "module_type": module_type,
            "normalized_parameters": normalized,
            "errors": [],
        }

    def validate_connection(
        self,
        source_module: str,
        source_port: str | int,
        destination_module: str,
        destination_port: str | int,
        developer_mode: bool = False,
    ) -> dict[str, Any]:
        """Resolve a prospective edge and apply registry signal compatibility."""
        errors: list[dict[str, str]] = []
        for value, field in (
            (source_module, "source_module"),
            (destination_module, "destination_module"),
        ):
            error = self._validate_name(value, field)
            if error:
                errors.append(error)
        if type(developer_mode) is not bool:
            errors.append(
                self._error(
                    "invalid_type",
                    "developer_mode",
                    "Developer mode must be a boolean.",
                )
            )
        if errors:
            return self._failure(*errors)

        source = self._lookup_module(source_module)
        destination = self._lookup_module(destination_module)
        if source is None:
            errors.append(
                self._error(
                    "unknown_module",
                    "source_module",
                    "Source module type is not present in the registry.",
                )
            )
        if destination is None:
            errors.append(
                self._error(
                    "unknown_module",
                    "destination_module",
                    "Destination module type is not present in the registry.",
                )
            )
        if errors:
            return self._failure(*errors)

        source_spec = source[1]
        destination_spec = destination[1]
        resolved_source, source_error = self._resolve_port(
            source_spec.get("outputs", []), source_port, "source_port"
        )
        resolved_destination, destination_error = self._resolve_port(
            destination_spec.get("inputs", []),
            destination_port,
            "destination_port",
        )
        if source_error:
            errors.append(source_error)
        if destination_error:
            errors.append(destination_error)
        if errors:
            return self._failure(*errors)

        compatible = registry.check_signal_compat(
            resolved_source["signal"],
            resolved_destination["signal"],
            developer_mode,
        )
        return {
            "ok": True,
            "compatible": bool(compatible),
            "developer_mode": developer_mode,
            "source_module": source_module,
            "source_port": deepcopy(resolved_source),
            "destination_module": destination_module,
            "destination_port": deepcopy(resolved_destination),
            "errors": [],
        }

    def validate_design(self, design: dict[str, Any]) -> dict[str, Any]:
        """Validate the bounded MCP proposed-graph schema without applying it.

        This is intentionally not the Qt ``version/nodes/edges`` save-file
        contract. Callers submit primitive module nodes and prospective
        connections for offline reasoning only.
        """
        if type(design) is not dict:
            return self._failure(
                self._error("invalid_type", "design", "Design must be an object.")
            )

        errors: list[dict[str, str]] = []
        overflowed = False

        def add(error: dict[str, str]) -> None:
            nonlocal overflowed
            if len(errors) < self.MAX_ERRORS - 1:
                errors.append(error)
            else:
                overflowed = True

        allowed_top_level = {"nodes", "connections"}
        for key in design:
            if key not in allowed_top_level:
                add(
                    self._error(
                        "unknown_field",
                        self._child_field("design", key),
                        "Design contains an unsupported field.",
                    )
                )
        for required in ("nodes", "connections"):
            if required not in design:
                add(
                    self._error(
                        "missing_field",
                        f"design.{required}",
                        "Design is missing a required field.",
                    )
                )

        nodes = design.get("nodes")
        connections = design.get("connections")
        if type(nodes) is not list:
            add(self._error("invalid_type", "design.nodes", "Nodes must be an array."))
        if type(connections) is not list:
            add(
                self._error(
                    "invalid_type", "design.connections", "Connections must be an array."
                )
            )
        if type(nodes) is not list or type(connections) is not list:
            return self._design_result(errors, 0, 0, overflowed)
        if len(nodes) > self.MAX_NODES or len(connections) > self.MAX_CONNECTIONS:
            add(
                self._error(
                    "graph_too_large",
                    "design",
                    "Design exceeds the supported node or connection limit.",
                )
            )
            return self._design_result(
                errors, len(nodes), len(connections), overflowed
            )

        node_types: dict[str, str] = {}
        instance_counts: dict[str, int] = {}
        allowed_node_fields = {"id", "module_type", "parameters"}
        for index, node in enumerate(nodes):
            base = f"design.nodes[{index}]"
            if type(node) is not dict:
                add(self._error("invalid_type", base, "Node must be an object."))
                continue
            for key in node:
                if key not in allowed_node_fields:
                    add(
                        self._error(
                            "unknown_field",
                            self._child_field(base, key),
                            "Node contains an unsupported field.",
                        )
                    )
            node_id = node.get("id")
            module_type = node.get("module_type")
            if type(node_id) is not str or not node_id or len(node_id) > self.MAX_NAME_LENGTH:
                add(
                    self._error(
                        "invalid_node_id", f"{base}.id", "Node id must be a short string."
                    )
                )
                node_id = None
            elif node_id in node_types:
                add(
                    self._error(
                        "duplicate_node_id", f"{base}.id", "Node id must be unique."
                    )
                )
                node_id = None

            resolved_module = None
            module_error = self._validate_name(module_type, f"{base}.module_type")
            if module_error:
                add(module_error)
                module_type = None
            else:
                resolved_module = self._lookup_module(module_type)
            if module_type is not None and resolved_module is None:
                add(
                    self._error(
                        "unknown_module",
                        f"{base}.module_type",
                        "Module type is not present in the registry.",
                    )
                )
                module_type = None
            elif (
                module_type is not None
                and resolved_module is not None
                and resolved_module[0] == "composite"
            ):
                add(
                    self._error(
                        "unsupported_composite_node",
                        f"{base}.module_type",
                        "Composite modules must be expanded before graph validation.",
                    )
                )
                module_type = None

            parameters = node.get("parameters", {})
            if module_type is not None:
                parameter_result = self.validate_parameters(module_type, parameters)
                for error in parameter_result.get("errors", []):
                    add(self._rebase_error(error, base))
                instance_counts[module_type] = instance_counts.get(module_type, 0) + 1
            elif type(parameters) is not dict:
                add(
                    self._error(
                        "invalid_type",
                        f"{base}.parameters",
                        "Parameters must be an object.",
                    )
                )
            if node_id is not None and module_type is not None:
                node_types[node_id] = module_type

        for module_type, count in instance_counts.items():
            resolved = self._lookup_module(module_type)
            maximum = resolved[1].get("max_instances", -1) if resolved else -1
            if type(maximum) is int and maximum >= 0 and count > maximum:
                add(
                    self._error(
                        "instance_limit_exceeded",
                        "design.nodes",
                        "Design exceeds a module instance limit.",
                    )
                )

        allowed_connection_fields = {"source", "destination", "developer_mode"}
        allowed_endpoint_fields = {"node", "port"}
        occupied_destinations: set[tuple[str, int]] = set()
        for index, connection in enumerate(connections):
            base = f"design.connections[{index}]"
            if type(connection) is not dict:
                add(
                    self._error("invalid_type", base, "Connection must be an object.")
                )
                continue
            for key in connection:
                if key not in allowed_connection_fields:
                    add(
                        self._error(
                            "unknown_field",
                            self._child_field(base, key),
                            "Connection contains an unsupported field.",
                        )
                    )
            source = connection.get("source")
            destination = connection.get("destination")
            endpoints_valid = True
            for label, endpoint in (("source", source), ("destination", destination)):
                endpoint_base = f"{base}.{label}"
                if type(endpoint) is not dict:
                    add(
                        self._error(
                            "invalid_type", endpoint_base, "Endpoint must be an object."
                        )
                    )
                    endpoints_valid = False
                    continue
                for key in endpoint:
                    if key not in allowed_endpoint_fields:
                        add(
                            self._error(
                                "unknown_field",
                                self._child_field(endpoint_base, key),
                                "Endpoint contains an unsupported field.",
                            )
                        )
                for required in ("node", "port"):
                    if required not in endpoint:
                        add(
                            self._error(
                                "missing_field",
                                f"{endpoint_base}.{required}",
                                "Endpoint is missing a required field.",
                            )
                        )
                        endpoints_valid = False
            developer_mode = connection.get("developer_mode", False)
            if type(developer_mode) is not bool:
                add(
                    self._error(
                        "invalid_type",
                        f"{base}.developer_mode",
                        "Developer mode must be a boolean.",
                    )
                )
                endpoints_valid = False
            if not endpoints_valid:
                continue

            source_id = source["node"]
            destination_id = destination["node"]
            if type(source_id) is not str or source_id not in node_types:
                add(
                    self._error(
                        "unknown_node",
                        f"{base}.source.node",
                        "Connection references an unknown source node.",
                    )
                )
                endpoints_valid = False
            if type(destination_id) is not str or destination_id not in node_types:
                add(
                    self._error(
                        "unknown_node",
                        f"{base}.destination.node",
                        "Connection references an unknown destination node.",
                    )
                )
                endpoints_valid = False
            if not endpoints_valid:
                continue

            if source_id == destination_id:
                add(
                    self._error(
                        "self_connection",
                        base,
                        "A node cannot connect to one of its own input ports.",
                    )
                )
                continue

            connection_result = self.validate_connection(
                node_types[source_id],
                source["port"],
                node_types[destination_id],
                destination["port"],
                developer_mode,
            )
            for error in connection_result.get("errors", []):
                add(self._rebase_error(error, base))
            if connection_result.get("ok") and not connection_result["compatible"]:
                add(
                    self._error(
                        "incompatible_signal",
                        base,
                        "Source and destination signal types are incompatible.",
                    )
                )
            elif connection_result.get("ok"):
                destination_key = (
                    destination_id,
                    int(connection_result["destination_port"]["index"]),
                )
                if destination_key in occupied_destinations:
                    add(
                        self._error(
                            "input_port_already_connected",
                            f"{base}.destination.port",
                            "Each input port can have only one incoming connection.",
                        )
                    )
                else:
                    occupied_destinations.add(destination_key)

        return self._design_result(errors, len(nodes), len(connections), overflowed)

    @classmethod
    def _catalog_entries(cls) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        for kind, collection, fallback_category in (
            ("module", registry.MODULE_REGISTRY, "unknown"),
            ("special", registry.SPECIAL_NODES, "constant"),
            ("composite", registry.COMPOSITE_MODULES, "composite"),
        ):
            for name, spec in collection.items():
                entries.append(
                    {
                        "module_type": name,
                        "display_name": spec.get("display_name", name),
                        "category": spec.get("category", fallback_category),
                        "kind": kind,
                    }
                )
        return entries

    @staticmethod
    def _lookup_module(module_type: str) -> tuple[str, dict[str, Any]] | None:
        if module_type in registry.MODULE_REGISTRY:
            return "module", registry.MODULE_REGISTRY[module_type]
        if module_type in registry.SPECIAL_NODES:
            return "special", registry.SPECIAL_NODES[module_type]
        if module_type in registry.COMPOSITE_MODULES:
            return "composite", registry.COMPOSITE_MODULES[module_type]
        return None

    @classmethod
    def _composite_parameter_specs(
        cls, composite: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        exposed = composite.get("params", [])
        direct: list[dict[str, Any]] = []
        indirect: list[dict[str, Any]] = []
        for key in exposed:
            found = False
            for child_name in composite.get("sub_modules", []):
                child = registry.MODULE_REGISTRY.get(child_name, {})
                child_direct, child_indirect = cls._module_parameter_specs(
                    child_name, child
                )
                for parameters, target in (
                    (child_direct, direct),
                    (child_indirect, indirect),
                ):
                    for parameter in parameters:
                        if parameter.get("key") == key:
                            target.append(deepcopy(parameter))
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
        return direct, indirect

    @staticmethod
    def _module_parameter_specs(
        module_type: str, raw_spec: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return Qt metadata with any stricter runtime registry constraints."""
        schema = _AUTHORITATIVE_PARAMETER_SCHEMAS.get(module_type)
        if schema is None:
            return (
                deepcopy(raw_spec.get("direct_params", [])),
                deepcopy(raw_spec.get("indirect_params", [])),
            )
        registry_parameters = {
            parameter.get("key"): parameter
            for parameter in (
                *raw_spec.get("direct_params", []),
                *raw_spec.get("indirect_params", []),
            )
            if type(parameter) is dict and type(parameter.get("key")) is str
        }

        def normalized(parameter: dict[str, Any]) -> dict[str, Any]:
            result = deepcopy(parameter)
            runtime = registry_parameters.get(result.get("key"), {})
            if "type" not in result and "type" in runtime:
                result["type"] = runtime["type"]
            runtime_minimum = runtime.get("min")
            if runtime_minimum is not None:
                schema_minimum = result.get("min")
                result["min"] = (
                    runtime_minimum
                    if schema_minimum is None
                    else max(schema_minimum, runtime_minimum)
                )
            runtime_maximum = runtime.get("max")
            if runtime_maximum is not None:
                schema_maximum = result.get("max")
                result["max"] = (
                    runtime_maximum
                    if schema_maximum is None
                    else min(schema_maximum, runtime_maximum)
                )
            result.update(
                deepcopy(
                    _PARAMETER_CONSTRAINT_OVERRIDES.get(
                        (module_type, result.get("key")), {}
                    )
                )
            )
            return result

        direct = [
            normalized(parameter)
            for parameter in schema
            if parameter.get("mode", "direct") != "indirect"
        ]
        indirect = [
            normalized(parameter)
            for parameter in schema
            if parameter.get("mode") == "indirect"
        ]
        return direct, indirect

    @staticmethod
    def _is_power_of_two(value: Any) -> bool:
        return type(value) is int and value > 0 and value & (value - 1) == 0

    @classmethod
    def _validate_name(cls, value: Any, field: str) -> dict[str, str] | None:
        if type(value) is not str:
            return cls._error("invalid_type", field, "Value must be a string.")
        if not value:
            return cls._error("empty_value", field, "Value must not be empty.")
        if len(value) > cls.MAX_NAME_LENGTH:
            return cls._error(
                "value_too_long", field, "Value exceeds the supported length."
            )
        return None

    @classmethod
    def _normalize_parameter(
        cls, value: Any, definition: dict[str, Any], field: str
    ) -> tuple[Any, dict[str, str] | None]:
        declared_type = definition.get("type")
        if declared_type == "bool":
            if type(value) is not bool:
                return None, cls._error(
                    "invalid_type", field, "Parameter must be a boolean."
                )
            normalized: Any = value
        elif declared_type == "int":
            if type(value) is not int:
                return None, cls._error(
                    "invalid_type", field, "Parameter must be an integer."
                )
            normalized = value
        elif declared_type == "float":
            special_values = set(definition.get("special_values", ()))
            if type(value) is str:
                if value in special_values:
                    # JSON has no portable Infinity value.  Preserve the Qt
                    # schema's explicit sentinel spelling rather than placing
                    # a non-finite Python float in an MCP response.
                    return value, None
                return None, cls._error(
                    "invalid_choice",
                    field,
                    "Parameter is not an allowed numeric special value.",
                )
            if type(value) not in (int, float):
                return None, cls._error(
                    "invalid_type", field, "Parameter must be a number."
                )
            if type(value) is float and not math.isfinite(value):
                return None, cls._error(
                    "non_finite_number", field, "Parameter must be finite."
                )
            if abs(value) > cls.MAX_ABS_NUMBER:
                return None, cls._error(
                    "out_of_range", field, "Parameter is outside the safe numeric range."
                )
            normalized = float(value)
        elif declared_type == "str":
            if type(value) is not str:
                return None, cls._error(
                    "invalid_type", field, "Parameter must be a string."
                )
            if len(value) > cls.MAX_NAME_LENGTH:
                return None, cls._error(
                    "value_too_long", field, "Parameter string is too long."
                )
            normalized = value
        else:
            return None, cls._error(
                "unsupported_parameter_type",
                field,
                "Registry parameter type is not supported by this service.",
            )

        minimum = definition.get("min")
        maximum = definition.get("max")
        if minimum is not None and normalized < minimum:
            return None, cls._error(
                "out_of_range", field, "Parameter is below its declared minimum."
            )
        if maximum is not None and normalized > maximum:
            return None, cls._error(
                "out_of_range", field, "Parameter is above its declared maximum."
            )
        choices = definition.get("enum")
        if choices is not None and normalized not in choices:
            return None, cls._error(
                "invalid_choice", field, "Parameter is not an allowed value."
            )
        return normalized, None

    @classmethod
    def _resolve_port(
        cls, ports: list[dict[str, Any]], reference: Any, field: str
    ) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
        if type(reference) not in (str, int):
            return None, cls._error(
                "invalid_type", field, "Port must be a name, display label, or index."
            )
        if type(reference) is str and len(reference) > cls.MAX_NAME_LENGTH:
            return None, cls._error(
                "value_too_long", field, "Port reference exceeds the supported length."
            )
        for port in ports:
            if type(reference) is int and port.get("index") == reference:
                return port, None
            if type(reference) is str and reference in (
                port.get("name"),
                port.get("display"),
            ):
                return port, None
        return None, cls._error(
            "unknown_port", field, "Port is not declared for this module direction."
        )

    @classmethod
    def _design_result(
        cls,
        errors: list[dict[str, str]],
        node_count: int,
        connection_count: int,
        overflowed: bool,
    ) -> dict[str, Any]:
        if overflowed:
            errors = errors[: cls.MAX_ERRORS - 1] + [
                cls._error(
                    "too_many_errors",
                    "design",
                    "Additional validation errors were omitted.",
                )
            ]
        return {
            "ok": not errors,
            "schema": "dclocking.mcp.proposed-graph.v1",
            "summary": {
                "node_count": node_count,
                "connection_count": connection_count,
            },
            "errors": errors,
        }

    @staticmethod
    def _error(code: str, field: str, message: str) -> dict[str, str]:
        return {"code": code, "field": field, "message": message}

    @classmethod
    def _failure(cls, *errors: dict[str, str]) -> dict[str, Any]:
        return {"ok": False, "errors": list(errors)}

    @staticmethod
    def _parameter_field(key: Any) -> str:
        if type(key) is str and _SAFE_FIELD_COMPONENT.fullmatch(key):
            return f"parameters.{key}"
        return "parameters"

    @staticmethod
    def _child_field(base: str, key: Any) -> str:
        if type(key) is str and _SAFE_FIELD_COMPONENT.fullmatch(key):
            return f"{base}.{key}"
        return base

    @staticmethod
    def _rebase_error(error: dict[str, str], base: str) -> dict[str, str]:
        field = error.get("field", "")
        if field == "module_type":
            field = f"{base}.module_type"
        elif field == "parameters":
            field = f"{base}.parameters"
        elif field.startswith("parameters."):
            field = f"{base}.{field}"
        elif field == "source_port":
            field = f"{base}.source.port"
        elif field == "destination_port":
            field = f"{base}.destination.port"
        elif field == "source_module":
            field = f"{base}.source.node"
        elif field == "destination_module":
            field = f"{base}.destination.node"
        elif field == "developer_mode":
            field = f"{base}.developer_mode"
        return {
            "code": error.get("code", "validation_error"),
            "field": field or base,
            "message": error.get("message", "Validation failed."),
        }

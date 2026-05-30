"""Tool executor — dispatches LLM tool calls to CanvasBridge / ModuleRegistry.

Each tool method takes the args dict from the LLM's function call and
returns a JSON-serializable result string.
"""

from __future__ import annotations

import json
import textwrap


class ToolExecutor:
    """Executes agent tool calls against the canvas and module registry."""

    def __init__(self, canvas_bridge, module_registry, code_generator=None):
        self._bridge = canvas_bridge
        self._registry = module_registry
        self._code_gen = code_generator
        # Build dispatch table
        self._handlers = {
            "create_module": self._create_module,
            "connect_modules": self._connect_modules,
            "list_modules": self._list_modules,
            "disconnect_module": self._disconnect_module,
            "set_parameter": self._set_parameter,
            "get_module_info": self._get_module_info,
            "generate_module": self._generate_module,
            "auto_layout": self._auto_layout,
            "clear_canvas": self._clear_canvas,
        }

    def dispatch(self, tool_name: str, args: dict) -> str:
        """Execute a tool call and return a result string."""
        handler = self._handlers.get(tool_name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: '{tool_name}'"},
                              ensure_ascii=False)
        try:
            result = handler(args)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "tool": tool_name},
                              ensure_ascii=False)

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _create_module(self, args: dict) -> dict:
        module_type = args["module_type"]
        pos = None
        if "position_x" in args and "position_y" in args:
            pos = (args["position_x"], args["position_y"])
        params = args.get("params")
        return self._bridge.create_node(module_type, pos, params)

    def _connect_modules(self, args: dict) -> dict:
        return self._bridge.create_connection(
            args["source_node"], args["source_port"],
            args["destination_node"], args["destination_port"],
        )

    def _list_modules(self, args: dict) -> dict:
        scope = args.get("scope", "both")
        result = {}

        if scope in ("available", "both"):
            from module_registry import MODULE_REGISTRY, SPECIAL_NODES, COMPOSITE_MODULES
            available = []
            for name, mod in MODULE_REGISTRY.items():
                entry = {
                    "name": name,
                    "internal_names": mod.get("internal_names", []),
                    "max_instances": mod.get("max_instances", "?"),
                    "category": mod.get("category", ""),
                    "purpose": mod.get("purpose", ""),
                    "num_inputs": len(mod.get("inputs", [])),
                    "num_outputs": len(mod.get("outputs", [])),
                }
                available.append(entry)
            for name, mod in SPECIAL_NODES.items():
                available.append({
                    "name": name,
                    "internal_names": mod.get("internal_names", []),
                    "max_instances": "unlimited",
                    "category": "constant",
                    "purpose": mod.get("purpose", ""),
                })
            for name, mod in COMPOSITE_MODULES.items():
                available.append({
                    "name": name,
                    "category": "composite",
                    "purpose": mod.get("purpose", ""),
                    "contains": mod.get("sub_modules", []),
                })
            result["available_modules"] = available

        if scope in ("on_canvas", "both"):
            result["nodes_on_canvas"] = self._bridge.list_nodes()
            result["connections_on_canvas"] = self._bridge.list_connections()

        return result

    def _disconnect_module(self, args: dict) -> dict:
        node_name = args["node_name"]
        if "port_index" in args:
            return self._bridge.disconnect_input(node_name, args["port_index"])
        else:
            return self._bridge.remove_node(node_name)

    def _set_parameter(self, args: dict) -> dict:
        return self._bridge.set_node_params(args["node_name"], args["params"])

    def _get_module_info(self, args: dict) -> dict:
        from module_registry import get_module
        module_type = args["module_type"]
        mod = get_module(module_type)
        if mod is None:
            return {"error": f"No module type named '{module_type}'.",
                    "hint": "Use list_modules to see available types."}
        # Return full details (but keep it concise for the LLM)
        info = {"display_name": module_type,
                "purpose": mod.get("purpose", ""),
                "max_instances": mod.get("max_instances", "?"),
                "category": mod.get("category", ""),
                "internal_names": mod.get("internal_names", [])}
        if "inputs" in mod:
            info["inputs"] = mod["inputs"]
        if "outputs" in mod:
            info["outputs"] = mod["outputs"]
        if "direct_params" in mod:
            info["direct_params"] = [
                {"key": p["key"], "label": p["label"], "type": p["type"]}
                for p in mod["direct_params"]
            ]
        if "indirect_params" in mod:
            info["indirect_params"] = [
                {"key": p["key"], "label": p["label"], "type": p["type"]}
                for p in mod["indirect_params"]
            ]
        if "special_methods" in mod:
            info["special_methods"] = mod["special_methods"]
        if "sub_modules" in mod:
            info["sub_modules"] = mod["sub_modules"]
        if "auto_connections" in mod:
            info["auto_connections"] = mod["auto_connections"]
        if "typical_connections" in mod:
            info["typical_connections"] = mod["typical_connections"]
        return info

    def _generate_module(self, args: dict) -> dict:
        if self._code_gen is None:
            return {"error": "Code generator not available.",
                    "hint": "Module code generation is not enabled in this session."}
        try:
            result = self._code_gen.generate(args)
            return result
        except Exception as e:
            return {"error": f"Code generation failed: {e}"}

    def _auto_layout(self, _args: dict) -> dict:
        return self._bridge.auto_layout()

    def _clear_canvas(self, args: dict) -> dict:
        if not args.get("confirm"):
            return {"error": "Set confirm=true to clear the canvas."}
        return self._bridge.clear_canvas()

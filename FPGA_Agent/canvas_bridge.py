"""Canvas bridge — safe access layer for MainWindow / DiagramScene / DiagramView.

Provides a clean facade API for the Agent to manipulate the graph canvas
without directly touching Qt objects or knowing internal widget structure.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QGraphicsItem


class CanvasBridge:
    """Facade wrapping MainWindow internals for agent-driven canvas operations."""

    def __init__(self, main_window):
        self._mw = main_window
        self._scene = main_window.scene
        self._view = main_window.view
        self._auto_pos_x = 0
        self._auto_pos_y = 0
        self._auto_pos_step = 250

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def create_node(self, component_name: str,
                    position: tuple[float, float] | None = None,
                    params: dict | None = None) -> dict:
        """Create a new module node on the canvas. Supports composites.

        Returns {"success": True, "node_name": ..., ...} or {"success": False, "error": ...}.
        """
        try:
            scene = self._scene
            view = self._view

            # Composite modules
            if component_name in view.composite_modules:
                composite_cls = view.composite_modules[component_name]
                if position is None:
                    position = self._next_auto_position()
                pos = QPointF(position[0], position[1])
                created = composite_cls.create_sub_modules(
                    scene, pos, view._alloc_index,
                    connect_func=scene.create_connection,
                )
                # Apply params if provided (params for composite's sub-modules not
                # currently implemented)
                return {"success": True, "node_name": component_name,
                        "composite": True, "position": list(position)}

            # Regular modules
            module_cls = view.module_factory.get(component_name)
            if module_cls is None:
                return {"success": False,
                        "error": f"Unknown module type: '{component_name}'. "
                                 f"Use list_modules to see available types."}

            idx = view._alloc_index(component_name)
            if idx is None:
                from module_registry import get_module
                mod = get_module(component_name)
                limit = mod["max_instances"] if mod else "?"
                return {"success": False,
                        "error": f"Max instances ({limit}) reached for '{component_name}'."}

            if position is None:
                position = self._next_auto_position()
            pos = QPointF(position[0], position[1])

            node = module_cls(component_name, idx, pos)
            view._apply_mode_to_node(node)
            scene.addItem(node)

            # Set initial params if provided
            if params:
                try:
                    node.set_params(params)
                except Exception as e:
                    pass  # params applied but may need hardware

            return {
                "success": True,
                "node_name": node.name,
                "display_name": getattr(node, "display_name", component_name),
                "component_name": component_name,
                "index": idx,
                "position": list(position),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_node(self, node_name: str) -> dict:
        """Remove a node and all its connections from the canvas."""
        node = self._find_node(node_name)
        if node is None:
            return {"success": False,
                    "error": f"No node named '{node_name}' on canvas."}
        try:
            self._view.remove_node(node)
            return {"success": True, "node_name": node_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_nodes(self) -> list[dict]:
        """Return all NodeItem instances currently on the canvas."""
        from qt_module import NodeItem
        result = []
        for item in self._scene.items():
            if isinstance(item, NodeItem):
                result.append({
                    "name": item.name,
                    "display_name": getattr(item, "display_name", ""),
                    "component_name": item.component_name,
                    "index": getattr(item, "index", -1),
                    "position": [item.pos().x(), item.pos().y()],
                    "num_inputs": int(item.num_inputs),
                    "num_outputs": int(item.num_outputs),
                })
        return result

    def _find_node(self, name: str):
        """Find a NodeItem by its internal name."""
        from qt_module import NodeItem
        for item in self._scene.items():
            if isinstance(item, NodeItem) and item.name == name:
                return item
        return None

    def _next_auto_position(self) -> tuple[float, float]:
        """Generate an auto-layout position for the next node."""
        from qt_module import NodeItem
        existing = [item for item in self._scene.items()
                    if isinstance(item, NodeItem)]
        if not existing:
            x, y = 0.0, 0.0
        else:
            max_x = max(item.pos().x() for item in existing)
            x = max_x + 250
            y = 0.0
        self._auto_pos_x = x
        self._auto_pos_y = y
        return (x, y)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def create_connection(self, src_node_name: str, src_port_idx: int,
                          dst_node_name: str, dst_port_idx: int) -> dict:
        """Create a connection between two module ports."""
        src_node = self._find_node(src_node_name)
        dst_node = self._find_node(dst_node_name)

        if src_node is None:
            return {"success": False,
                    "error": f"Source node '{src_node_name}' not found."}
        if dst_node is None:
            return {"success": False,
                    "error": f"Destination node '{dst_node_name}' not found."}

        # Get port items
        if src_port_idx < 0 or src_port_idx >= len(src_node.out_ports):
            return {"success": False,
                    "error": f"Source port index {src_port_idx} out of range "
                             f"(0-{len(src_node.out_ports)-1})."}
        if dst_port_idx < 0 or dst_port_idx >= len(dst_node.in_ports):
            return {"success": False,
                    "error": f"Destination port index {dst_port_idx} out of range "
                             f"(0-{len(dst_node.in_ports)-1})."}

        src_port = src_node.out_ports[src_port_idx]
        dst_port = dst_node.in_ports[dst_port_idx]

        # Check if destination already has a connection
        if hasattr(dst_port, 'has_connection') and dst_port.has_connection():
            return {"success": False,
                    "error": f"Port In{dst_port_idx+1} of '{dst_node_name}' "
                             f"already has a connection. Disconnect it first."}

        try:
            ok = self._scene.create_connection(src_port, dst_port)
            if ok:
                return {"success": True,
                        "connection": f"{src_node_name}:Out{src_port_idx+1} → "
                                      f"{dst_node_name}:In{dst_port_idx+1}"}
            else:
                return {"success": False,
                        "error": "Connection rejected (signal type mismatch "
                                 "or other validation failure)."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect_input(self, node_name: str, port_idx: int) -> dict:
        """Disconnect an input port (remove the edge feeding into it)."""
        node = self._find_node(node_name)
        if node is None:
            return {"success": False,
                    "error": f"No node named '{node_name}' on canvas."}
        if port_idx < 0 or port_idx >= len(node.in_ports):
            return {"success": False,
                    "error": f"Input port index {port_idx} out of range."}

        port = node.in_ports[port_idx]
        if not (hasattr(port, 'has_connection') and port.has_connection()):
            return {"success": False,
                    "error": f"Port In{port_idx+1} of '{node_name}' "
                             f"has no connection."}

        try:
            self._scene.remove_connection(port)
            return {"success": True,
                    "detail": f"Disconnected {node_name}:In{port_idx+1}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_connections(self) -> list[dict]:
        """Return all edges currently on the canvas."""
        from qt_ui_graph import EdgeItem
        result = []
        for item in self._scene.items():
            if isinstance(item, EdgeItem):
                try:
                    sp = item.start_port
                    ep = item.end_port
                    src_node = getattr(sp, 'parent_node', None)
                    dst_node = getattr(ep, 'parent_node', None)
                    result.append({
                        "source": {
                            "node": src_node.name if src_node else "?",
                            "port_idx": sp.index,
                        },
                        "destination": {
                            "node": dst_node.name if dst_node else "?",
                            "port_idx": ep.index,
                        },
                    })
                except Exception:
                    continue
        return result

    # ------------------------------------------------------------------
    # Port introspection
    # ------------------------------------------------------------------

    def get_port_info(self, node_name: str) -> dict:
        """Return detailed port information for a node."""
        node = self._find_node(node_name)
        if node is None:
            return {"success": False,
                    "error": f"No node named '{node_name}' on canvas."}

        inputs = []
        for i, port in enumerate(node.in_ports):
            signals = getattr(port, 'signals', [])
            has_conn = port.has_connection() if hasattr(port, 'has_connection') else False
            inputs.append({
                "index": i,
                "name": port.name if hasattr(port, 'name') else f"In{i}",
                "signals": list(signals) if signals else [],
                "connected": has_conn,
            })

        outputs = []
        for i, port in enumerate(node.out_ports):
            signals = getattr(port, 'signals', [])
            outputs.append({
                "index": i,
                "name": port.name if hasattr(port, 'name') else f"Out{i}",
                "signals": list(signals) if signals else [],
            })

        return {
            "success": True,
            "node_name": node_name,
            "component_name": getattr(node, "component_name", ""),
            "inputs": inputs,
            "outputs": outputs,
        }

    # ------------------------------------------------------------------
    # Parameter access
    # ------------------------------------------------------------------

    def get_node_params(self, node_name: str) -> dict:
        """Get cached parameters from a node (does not read hardware)."""
        node = self._find_node(node_name)
        if node is None:
            return {"success": False,
                    "error": f"No node named '{node_name}' on canvas."}
        try:
            params = node.get_params() if hasattr(node, 'get_params') else {}
            return {"success": True, "params": params}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_node_params(self, node_name: str, params: dict) -> dict:
        """Set parameters on a node (updates cache + triggers hardware write)."""
        node = self._find_node(node_name)
        if node is None:
            return {"success": False,
                    "error": f"No node named '{node_name}' on canvas."}
        try:
            if hasattr(node, 'set_params'):
                node.set_params(params)
            return {"success": True, "params": params}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Canvas operations
    # ------------------------------------------------------------------

    def clear_canvas(self) -> dict:
        """Remove all nodes and connections."""
        try:
            # Call MainWindow clear methods
            if hasattr(self._mw, '_clear_canvas'):
                self._mw._clear_canvas()
            if hasattr(self._mw, '_disconnect_all_connections'):
                self._mw._disconnect_all_connections()
            return {"success": True, "detail": "Canvas cleared."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def auto_layout(self) -> dict:
        """Auto-arrange nodes using the built-in layered graph layout."""
        from qt_module import NodeItem
        from qt_ui_graph import EdgeItem
        try:
            nodes = [item for item in self._scene.items()
                     if isinstance(item, NodeItem)]
            edges = [item for item in self._scene.items()
                     if isinstance(item, EdgeItem)]
            if hasattr(self._mw, '_optimize_grid_layout'):
                positions = self._mw._optimize_grid_layout(nodes, edges)
                if positions:
                    for node, pos in positions.items():
                        if hasattr(node, 'setPos'):
                            node.setPos(pos)
            return {"success": True,
                    "detail": f"Laid out {len(nodes)} nodes."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_canvas_state(self) -> dict:
        """Return full canvas snapshot: nodes + connections."""
        return {
            "nodes": self.list_nodes(),
            "connections": self.list_connections(),
        }

    # ------------------------------------------------------------------
    # Mode
    # ------------------------------------------------------------------

    def set_developer_mode(self, enabled: bool) -> None:
        """Toggle developer mode on the scene."""
        self._scene.set_developer_mode(enabled)
        from qt_module import NodeItem
        free_mode = not enabled
        for item in self._scene.items():
            if isinstance(item, NodeItem):
                item.free_mode = free_mode

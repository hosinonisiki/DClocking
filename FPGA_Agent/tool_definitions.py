"""Tool definitions in OpenAI function-calling JSON Schema format."""

TOOLS = [
    # ------------------------------------------------------------------
    # create_module
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "create_module",
            "description": (
                "Create a new signal processing module node on the FPGA canvas. "
                "Choose from the available module types. The module will appear "
                "at the specified position (or auto-placed if omitted). "
                "You can optionally provide initial parameter values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "module_type": {
                        "type": "string",
                        "description": (
                            "The Chinese display name of the module type, e.g. "
                            "'PID控制器', '累加器', '混频器', '三角函数运算器', "
                            "'PDH状态机', '正弦波发生器'.  Must exactly match "
                            "a type from list_modules."
                        ),
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X coordinate on canvas (omit for auto-placement).",
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y coordinate on canvas (omit for auto-placement).",
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "Optional initial parameter values as key→value pairs. "
                            "Use parameter keys from get_module_info, e.g. "
                            '{"freq": 10000000.0, "enable_auto_reset": 1}.'
                        ),
                    },
                },
                "required": ["module_type"],
            },
        },
    },

    # ------------------------------------------------------------------
    # connect_modules
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "connect_modules",
            "description": (
                "Create a wire connection from an output port of one module "
                "to an input port of another module.  The signal types of the "
                "two ports must be compatible (e.g. both support 'level', "
                "or both support 'bool').  Each input port accepts at most "
                "ONE incoming connection.  Use get_module_info or list_modules "
                "first to see port indices and signal types."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_node": {
                        "type": "string",
                        "description": (
                            "Internal (short) name of the source node, e.g. "
                            "'ACCM', 'TRIG', 'MIXR', 'PIDC', 'PDHS'. "
                            "Use the names returned by list_modules or create_module."
                        ),
                    },
                    "source_port": {
                        "type": "integer",
                        "description": "Zero-based index of the OUTPUT port on the source node.",
                    },
                    "destination_node": {
                        "type": "string",
                        "description": "Internal (short) name of the destination node.",
                    },
                    "destination_port": {
                        "type": "integer",
                        "description": "Zero-based index of the INPUT port on the destination node.",
                    },
                },
                "required": ["source_node", "source_port",
                             "destination_node", "destination_port"],
            },
        },
    },

    # ------------------------------------------------------------------
    # list_modules
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "list_modules",
            "description": (
                "List available module types (that can be placed on the canvas) "
                "AND/OR the modules currently placed on the canvas with their "
                "connections. Use this to understand what's available and what's "
                "already on the canvas before making changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "enum": ["available", "on_canvas", "both"],
                        "description": (
                            "'available' = list all module types you can create. "
                            "'on_canvas' = list currently placed nodes + connections. "
                            "'both' = return everything.  Default: 'both'."
                        ),
                    },
                },
                "required": [],
            },
        },
    },

    # ------------------------------------------------------------------
    # disconnect_module
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "disconnect_module",
            "description": (
                "Remove a single connection from an input port, or remove an "
                "entire module node (and all its connections) from the canvas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Internal name of the node.",
                    },
                    "port_index": {
                        "type": "integer",
                        "description": (
                            "If specified: disconnect only this INPUT port. "
                            "If omitted: remove the entire node."
                        ),
                    },
                },
                "required": ["node_name"],
            },
        },
    },

    # ------------------------------------------------------------------
    # set_parameter
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "set_parameter",
            "description": (
                "Set one or more parameter values on an existing module. "
                "Use get_module_info first to see the available parameter keys "
                "and their valid ranges.  Parameters are written to hardware "
                "if connected."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Internal name of the node.",
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "Key→value pairs of parameter names to values, e.g. "
                            '{"freq": 1e6, "enable_auto_reset": 1}.'
                        ),
                    },
                },
                "required": ["node_name", "params"],
            },
        },
    },

    # ------------------------------------------------------------------
    # get_module_info
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "get_module_info",
            "description": (
                "Get detailed information about a specific module TYPE (not an "
                "instance on the canvas): what ports it has (with signal types "
                "and indices), what parameters are available, max instances, etc. "
                "Always call this before creating connections so you use the "
                "correct port indices."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "module_type": {
                        "type": "string",
                        "description": (
                            "The Chinese display name of the module type, e.g. "
                            "'PID控制器', '累加器', '混频器', etc."
                        ),
                    },
                },
                "required": ["module_type"],
            },
        },
    },

    # ------------------------------------------------------------------
    # generate_module
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "generate_module",
            "description": (
                "Generate VHDL and Python code for a NEW custom module type "
                "that does not currently exist in the library.  After generation, "
                "the module becomes available for create_module in this session. "
                "Use this ONLY when the user explicitly requests a module type "
                "that is not in the available modules list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": (
                            "Short snake_case internal name, e.g. 'envelope_detector'. "
                            "Used for VHDL entity name and Python class name."
                        ),
                    },
                    "display_name": {
                        "type": "string",
                        "description": (
                            "Chinese display name shown in UI, e.g. '包络检波器'."
                        ),
                    },
                    "description": {
                        "type": "string",
                        "description": "One paragraph describing what the module does.",
                    },
                    "inputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Short port identifier, e.g. 'SIGNAL_IN'.",
                                },
                                "display": {
                                    "type": "string",
                                    "description": "Chinese display label.",
                                },
                                "signal": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["level", "phase", "differential", "bool"],
                                    },
                                    "description": "Accepted signal types for this port.",
                                },
                            },
                            "required": ["name", "display", "signal"],
                        },
                        "description": "List of input port definitions.",
                    },
                    "outputs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Short port identifier.",
                                },
                                "display": {
                                    "type": "string",
                                    "description": "Chinese display label.",
                                },
                                "signal": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["level", "phase", "differential", "bool"],
                                    },
                                    "description": "Output signal types for this port.",
                                },
                            },
                            "required": ["name", "display", "signal"],
                        },
                        "description": "List of output port definitions.",
                    },
                    "params": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {
                                    "type": "string",
                                    "enum": ["int", "float", "bool"],
                                },
                                "min": {"type": "number"},
                                "max": {"type": "number"},
                                "default": {},
                                "note": {"type": "string"},
                            },
                            "required": ["key", "label", "type"],
                        },
                        "description": "Parameter definitions (optional).",
                    },
                    "max_instances": {
                        "type": "integer",
                        "description": "Maximum instances allowed on canvas (default 2).",
                    },
                },
                "required": ["module_name", "display_name", "description",
                             "inputs", "outputs"],
            },
        },
    },

    # ------------------------------------------------------------------
    # auto_layout
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "auto_layout",
            "description": (
                "Automatically arrange all nodes on the canvas using a "
                "layered graph layout algorithm.  Call this after creating "
                "several modules to make the diagram readable."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    # ------------------------------------------------------------------
    # clear_canvas
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "clear_canvas",
            "description": (
                "Remove ALL modules and connections from the canvas. "
                "Use with caution — this cannot be undone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be explicitly set to true.",
                    },
                },
                "required": ["confirm"],
            },
        },
    },
]

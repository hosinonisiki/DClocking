"""Tests for the read-only MCP-facing FPGA module catalog service."""

from __future__ import annotations

import json
import math
import unittest
from unittest import mock

from FPGA_Agent import mcp_catalog_service
from FPGA_Agent.mcp_catalog_service import McpCatalogService


class McpCatalogServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = McpCatalogService()

    @staticmethod
    def error_codes(result: dict) -> set[str]:
        return {error["code"] for error in result.get("errors", [])}

    def assert_json_value(self, value: object) -> None:
        encoded = json.dumps(value, allow_nan=False, ensure_ascii=False)
        self.assertIsInstance(encoded, str)

    def test_lists_registered_modules_in_stable_json_shape(self):
        first = self.service.list_module_types()
        second = self.service.list_module_types()

        self.assertTrue(first["ok"])
        self.assertEqual(first, second)
        self.assertEqual(first["count"], len(first["modules"]))
        self.assertIn("PID控制器", [item["module_type"] for item in first["modules"]])
        self.assertIn("布尔值：是", [item["module_type"] for item in first["modules"]])
        self.assertIn("正弦波发生器", [item["module_type"] for item in first["modules"]])
        for item in first["modules"]:
            self.assertEqual(
                set(item),
                {"module_type", "display_name", "category", "kind"},
            )
        self.assert_json_value(first)

    def test_list_category_filter_is_strict(self):
        filtered = self.service.list_module_types("filter")
        self.assertTrue(filtered["ok"])
        self.assertEqual(
            [item["module_type"] for item in filtered["modules"]],
            ["FIR滤波器", "IIR滤波器"],
        )

        unknown = self.service.list_module_types("does-not-exist")
        self.assertFalse(unknown["ok"])
        self.assertIn("unknown_category", self.error_codes(unknown))

        wrong_type = self.service.list_module_types(7)
        self.assertFalse(wrong_type["ok"])
        self.assertIn("invalid_type", self.error_codes(wrong_type))

    def test_get_module_spec_returns_a_detached_normalized_copy(self):
        result = self.service.get_module_spec("PID控制器")
        self.assertTrue(result["ok"])
        spec = result["module"]
        self.assertEqual(spec["module_type"], "PID控制器")
        self.assertEqual(spec["kind"], "module")
        self.assertEqual(spec["inputs"][1]["name"], "IN")
        self.assertEqual(spec["outputs"][0]["name"], "OUT")
        self.assertIn("gain_p", [param["key"] for param in spec["direct_params"]])
        pi_corner = next(
            param for param in spec["indirect_params"] if param["key"] == "pi_corner"
        )
        self.assertEqual(pi_corner["min"], 0.0)
        self.assertEqual(pi_corner["max"], 1e9)

        spec["inputs"][0]["name"] = "MUTATED"
        again = self.service.get_module_spec("PID控制器")
        self.assertEqual(again["module"]["inputs"][0]["name"], "RESET")
        self.assert_json_value(result)

    def test_get_module_spec_rejects_unknown_or_oversized_names(self):
        unknown = self.service.get_module_spec("/Users/alice/private/module")
        self.assertFalse(unknown["ok"])
        self.assertIn("unknown_module", self.error_codes(unknown))
        self.assertNotIn("/Users/", json.dumps(unknown, ensure_ascii=False))

        oversized = self.service.get_module_spec("x" * 300)
        self.assertFalse(oversized["ok"])
        self.assertIn("value_too_long", self.error_codes(oversized))

    def test_validate_parameters_accepts_exact_types_and_ranges(self):
        result = self.service.validate_parameters(
            "PID控制器",
            {"gain_p": 12, "enable_auto_reset": True, "pi_corner": 1250.5},
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(
            result["normalized_parameters"],
            {"enable_auto_reset": True, "gain_p": 12, "pi_corner": 1250.5},
        )
        self.assert_json_value(result)

    def test_validate_parameters_rejects_unknown_wrong_type_range_and_nonfinite(self):
        unknown = self.service.validate_parameters("PID控制器", {"secret_path": "x"})
        self.assertFalse(unknown["ok"])
        self.assertIn("unknown_parameter", self.error_codes(unknown))

        bool_as_int = self.service.validate_parameters("PID控制器", {"gain_p": True})
        self.assertFalse(bool_as_int["ok"])
        self.assertIn("invalid_type", self.error_codes(bool_as_int))

        int_as_bool = self.service.validate_parameters(
            "PID控制器", {"enable_auto_reset": 1}
        )
        self.assertFalse(int_as_bool["ok"])
        self.assertIn("invalid_type", self.error_codes(int_as_bool))

        out_of_range = self.service.validate_parameters(
            "PID控制器", {"gain_p": 8_388_608}
        )
        self.assertFalse(out_of_range["ok"])
        self.assertIn("out_of_range", self.error_codes(out_of_range))

        negative_corner = self.service.validate_parameters(
            "PID控制器", {"pi_corner": -5.0}
        )
        self.assertFalse(negative_corner["ok"])
        self.assertIn("out_of_range", self.error_codes(negative_corner))

        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                nonfinite = self.service.validate_parameters(
                    "PID控制器", {"pi_corner": value}
                )
                self.assertFalse(nonfinite["ok"])
                self.assertIn("non_finite_number", self.error_codes(nonfinite))
                self.assert_json_value(nonfinite)

    def test_validate_parameters_matches_accumulator_runtime_constraints(self):
        valid = self.service.validate_parameters(
            "累加器", {"freq": 125_000_000.0, "ratio": 4}
        )
        self.assertTrue(valid["ok"], valid)

        invalid_ratio = self.service.validate_parameters("累加器", {"ratio": 3})
        self.assertFalse(invalid_ratio["ok"])
        self.assertIn("constraint_violation", self.error_codes(invalid_ratio))

        above_nyquist = self.service.validate_parameters(
            "累加器", {"freq": 125_000_000.1}
        )
        self.assertFalse(above_nyquist["ok"])
        self.assertIn("out_of_range", self.error_codes(above_nyquist))

    def test_validate_parameters_supports_only_declared_json_special_values(self):
        result = self.service.validate_parameters(
            "PID控制器",
            {
                "overall_gain": "-inf",
                "pd_corner": "inf",
                "saturation_gain": "inf",
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(
            result["normalized_parameters"],
            {
                "overall_gain": "-inf",
                "pd_corner": "inf",
                "saturation_gain": "inf",
            },
        )
        self.assert_json_value(result)

        for key, value in (
            ("overall_gain", "inf"),
            ("pd_corner", "-inf"),
            ("pi_corner", "inf"),
        ):
            with self.subTest(key=key, value=value):
                invalid = self.service.validate_parameters(
                    "PID控制器", {key: value}
                )
                self.assertFalse(invalid["ok"])
                self.assertIn("invalid_choice", self.error_codes(invalid))

        numeric_infinity = self.service.validate_parameters(
            "PID控制器", {"pd_corner": math.inf}
        )
        self.assertFalse(numeric_infinity["ok"])
        self.assertIn("non_finite_number", self.error_codes(numeric_infinity))

    def test_validate_parameters_exposes_filter_low_level_schema(self):
        fir = self.service.validate_parameters(
            "FIR滤波器", {"coef_0": 123, "taps": 31}
        )
        self.assertTrue(fir["ok"], fir)

        fir_spec = self.service.get_module_spec("FIR滤波器")["module"]
        taps_spec = next(
            item for item in fir_spec["direct_params"] if item["key"] == "taps"
        )
        self.assertEqual(taps_spec["enum"], [15, 31, 63])

        for invalid_taps in (-1, 0, 16, 32, 64, 10**100):
            with self.subTest(taps=invalid_taps):
                invalid_fir = self.service.validate_parameters(
                    "FIR滤波器", {"taps": invalid_taps}
                )
                self.assertFalse(invalid_fir["ok"])
                self.assertIn("invalid_choice", self.error_codes(invalid_fir))

        iir = self.service.validate_parameters("IIR滤波器", {"coef_bq1_b0": -123})
        self.assertTrue(iir["ok"], iir)

        iir_out_of_range = self.service.validate_parameters(
            "IIR滤波器", {"coef_bq1_b0": 2**26}
        )
        self.assertFalse(iir_out_of_range["ok"])
        self.assertIn("out_of_range", self.error_codes(iir_out_of_range))

    def test_validate_parameters_supports_declared_composite_parameters(self):
        result = self.service.validate_parameters(
            "正弦波发生器", {"freq": 10_000.0, "enable_auto_reset": False}
        )
        self.assertTrue(result["ok"], result)

        undeclared = self.service.validate_parameters("正弦波发生器", {"ratio": 2})
        self.assertFalse(undeclared["ok"])
        self.assertIn("unknown_parameter", self.error_codes(undeclared))

        spec = self.service.get_module_spec("正弦波发生器")["module"]
        self.assertFalse(spec["design_validation_supported"])
        self.assertNotIn("auto_connections", spec)

    def test_validate_connection_resolves_names_displays_and_indices(self):
        by_name = self.service.validate_connection(
            "三角函数运算器", "SIN", "混频器", "IN_A"
        )
        self.assertTrue(by_name["ok"], by_name)
        self.assertTrue(by_name["compatible"])
        self.assertEqual(by_name["source_port"]["index"], 0)
        self.assertEqual(by_name["destination_port"]["index"], 0)

        by_display_and_index = self.service.validate_connection(
            "三角函数运算器", "正弦信号输出", "混频器", 0
        )
        self.assertTrue(by_display_and_index["ok"], by_display_and_index)
        self.assertTrue(by_display_and_index["compatible"])
        self.assert_json_value(by_display_and_index)

    def test_validate_connection_rejects_unknown_modules_ports_and_flags(self):
        unknown_module = self.service.validate_connection("不存在", 0, "混频器", 0)
        self.assertFalse(unknown_module["ok"])
        self.assertIn("unknown_module", self.error_codes(unknown_module))

        unknown_port = self.service.validate_connection(
            "三角函数运算器", "NO_SUCH_OUTPUT", "混频器", 0
        )
        self.assertFalse(unknown_port["ok"])
        self.assertIn("unknown_port", self.error_codes(unknown_port))

        invalid_flag = self.service.validate_connection(
            "三角函数运算器", 0, "混频器", 0, developer_mode=1
        )
        self.assertFalse(invalid_flag["ok"])
        self.assertIn("invalid_type", self.error_codes(invalid_flag))

    def test_validate_connection_reuses_registry_compatibility_rules(self):
        with mock.patch.object(
            mcp_catalog_service.registry,
            "check_signal_compat",
            wraps=mcp_catalog_service.registry.check_signal_compat,
        ) as compatibility:
            result = self.service.validate_connection(
                "PID控制器", "OUT", "累加器", "BIAS_IN", developer_mode=False
            )

        self.assertTrue(result["ok"], result)
        compatibility.assert_called_once_with(
            ["level", "differential"], ["differential"], False
        )

    def test_validate_design_checks_nodes_parameters_and_connections(self):
        design = {
            "nodes": [
                {
                    "id": "oscillator",
                    "module_type": "三角函数运算器",
                    "parameters": {},
                },
                {"id": "mixer", "module_type": "混频器", "parameters": {}},
            ],
            "connections": [
                {
                    "source": {"node": "oscillator", "port": "SIN"},
                    "destination": {"node": "mixer", "port": "IN_A"},
                }
            ],
        }
        result = self.service.validate_design(design)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["schema"], "dclocking.mcp.proposed-graph.v1")
        self.assertEqual(result["summary"], {"node_count": 2, "connection_count": 1})
        self.assert_json_value(result)

    def test_validate_design_rejects_unexpanded_composite_nodes(self):
        result = self.service.validate_design(
            {
                "nodes": [
                    {
                        "id": "oscillator",
                        "module_type": "正弦波发生器",
                        "parameters": {"freq": 10_000.0},
                    }
                ],
                "connections": [],
            }
        )

        self.assertFalse(result["ok"])
        self.assertIn("unsupported_composite_node", self.error_codes(result))

    def test_validate_design_enforces_canvas_connection_topology(self):
        result = self.service.validate_design(
            {
                "nodes": [
                    {"id": "trig1", "module_type": "三角函数运算器", "parameters": {}},
                    {"id": "trig2", "module_type": "三角函数运算器", "parameters": {}},
                    {"id": "mix", "module_type": "混频器", "parameters": {}},
                ],
                "connections": [
                    {
                        "source": {"node": "trig1", "port": "SIN"},
                        "destination": {"node": "trig1", "port": "IN"},
                    },
                    {
                        "source": {"node": "trig1", "port": "SIN"},
                        "destination": {"node": "mix", "port": "IN_A"},
                    },
                    {
                        "source": {"node": "trig2", "port": "COS"},
                        "destination": {"node": "mix", "port": "IN_A"},
                    },
                ],
            }
        )

        self.assertFalse(result["ok"])
        self.assertIn("self_connection", self.error_codes(result))
        self.assertIn("input_port_already_connected", self.error_codes(result))

    def test_validate_design_strictly_rejects_unknown_fields_and_references(self):
        unknown_top_level = self.service.validate_design(
            {"nodes": [], "connections": [], "file_path": "/tmp/secret"}
        )
        self.assertFalse(unknown_top_level["ok"])
        self.assertIn("unknown_field", self.error_codes(unknown_top_level))
        self.assertNotIn("/tmp/secret", json.dumps(unknown_top_level, ensure_ascii=False))

        malformed = self.service.validate_design(
            {
                "nodes": [
                    {"id": "same", "module_type": "PID控制器", "parameters": {}},
                    {"id": "same", "module_type": "累加器", "parameters": {}},
                ],
                "connections": [
                    {
                        "source": {"node": "missing", "port": "OUT"},
                        "destination": {"node": "same", "port": "ERROR_IN"},
                    }
                ],
            }
        )
        self.assertFalse(malformed["ok"])
        self.assertIn("duplicate_node_id", self.error_codes(malformed))
        self.assertIn("unknown_node", self.error_codes(malformed))

    def test_validate_design_rejects_oversized_graph_without_traversing_it(self):
        design = {
            "nodes": [
                {"id": f"n{i}", "module_type": "PID控制器", "parameters": {}}
                for i in range(self.service.MAX_NODES + 1)
            ],
            "connections": [],
        }
        result = self.service.validate_design(design)
        self.assertFalse(result["ok"])
        self.assertIn("graph_too_large", self.error_codes(result))

    def test_public_operations_have_no_file_network_or_process_side_effects(self):
        with (
            mock.patch("builtins.open", side_effect=AssertionError("file access")),
            mock.patch("socket.socket", side_effect=AssertionError("network access")),
            mock.patch("subprocess.Popen", side_effect=AssertionError("process access")),
        ):
            self.assertTrue(self.service.list_module_types()["ok"])
            self.assertTrue(self.service.get_module_spec("PID控制器")["ok"])
            self.assertTrue(
                self.service.validate_parameters("PID控制器", {"gain_p": 1})["ok"]
            )
            self.assertTrue(
                self.service.validate_connection(
                    "三角函数运算器", "SIN", "混频器", "IN_A"
                )["ok"]
            )
            self.assertTrue(
                self.service.validate_design({"nodes": [], "connections": []})["ok"]
            )


if __name__ == "__main__":
    unittest.main()

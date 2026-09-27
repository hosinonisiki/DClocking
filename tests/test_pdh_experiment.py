"""Pure experiment semantics: preserve hardware ABI and never claim telemetry."""

import json
import math
import unittest

from FPGA_Agent.pdh_experiment import (
    ExperimentProfile, WaveformTrace, cycles_to_us, demo_trace, export_report,
    parse_trace_csv, percent_to_q15, preflight, q15_to_percent, replay_manual,
    suggest_parameters, us_to_cycles, validate_parameters,
)


PARAMETERS = {
    "pc_cmd": 1, "threshold_signal_scan": 20, "threshold_signal_lock": 70,
    "time_scan": 2, "time_lock": 2, "coef_scan": 8192, "coef_lock": 21299,
}


class ProfileTests(unittest.TestCase):
    def test_json_round_trip_is_lossless_and_detached(self):
        profile = ExperimentProfile(name="反射谷", detector_source="PD1",
                                    polarity="dip", clock_hz=250_000_000,
                                    units_per_count=.001, signal_unit="V")
        data = profile.to_dict()
        self.assertEqual(ExperimentProfile.from_dict(json.loads(json.dumps(data))), profile)
        data["name"] = "edited"
        self.assertEqual(profile.name, "反射谷")
        self.assertEqual(ExperimentProfile().signal_unit, "内部信号码")

    def test_invalid_profiles_fail_instead_of_coercing(self):
        for field, value in [
            ("version", True), ("version", 2), ("version", "1"),
            ("name", 12), ("name", ""), ("polarity", "negative"),
            ("clock_hz", True), ("clock_hz", 0), ("clock_hz", math.nan),
            ("clock_hz", math.inf), ("units_per_count", -1),
            ("signal_unit", ""), ("notes", "x" * 8193),
        ]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                ExperimentProfile.from_dict({field: value})
        with self.assertRaises(ValueError):
            ExperimentProfile.from_dict({"unexpected": "discard me"})
        with self.assertRaises(ValueError):
            ExperimentProfile.from_dict([])


class NumericContractTests(unittest.TestCase):
    def test_time_conversion_and_explicit_half_up_rounding(self):
        self.assertEqual(cycles_to_us(250, 250_000_000), 1)
        self.assertEqual(us_to_cycles(1, 250_000_000), 250)
        self.assertEqual(us_to_cycles(.5, 1_000_000), 1)
        self.assertEqual(us_to_cycles(0, 1_000_000), 0)
        self.assertEqual(us_to_cycles(2**31 - 1, 1_000_000), 2**31 - 1)
        self.assertEqual(cycles_to_us(2**32 - 1, 1_000_000), 2**32 - 1)

    def test_legacy_times_load_losslessly_but_cannot_be_new_writes(self):
        old = dict(PARAMETERS, time_lock=2**32 - 1, coef_lock=-32768)
        self.assertEqual(validate_parameters(old), old)
        with self.assertRaises(ValueError):
            validate_parameters(old, for_write=True)
        self.assertEqual(validate_parameters({"coef_scan": -1}), {"coef_scan": -1})

    def test_invalid_numbers_are_not_silently_clipped(self):
        for args in [(True, 1e6), (-1, 1e6), (math.inf, 1e6), (1, None),
                     (1, False), (1, 0), (1, math.nan), (2**31, 1e6),
                     (10**400, 1e6)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                us_to_cycles(*args)
        for value in [True, 1.5, -1, 2**32]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                cycles_to_us(value, 1e6)
        for data in [{"pc_cmd": 4}, {"pc_cmd": True}, {"time_scan": -1},
                     {"time_scan": 1.0}, {"coef_scan": 32768},
                     {"threshold_signal_scan": -32769}, {"surprise": 1}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_parameters(data)

    def test_q15_percent_roundtrip_for_boundaries_and_negative_legacy(self):
        for raw in [-32768, -1, 0, 8192, 16384, 32767]:
            self.assertEqual(percent_to_q15(q15_to_percent(raw)), raw)
        self.assertEqual(q15_to_percent(16384), 50)
        for value in [100, -101, True, math.nan, "50"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                percent_to_q15(value)
        with self.assertRaises(ValueError):
            q15_to_percent(32768)


class TraceTests(unittest.TestCase):
    def test_csv_import_preserves_source_and_physical_time(self):
        trace = parse_trace_csv("\ufefftime_s,value\n-0.001,100\n\n0,0\n0.001,200\n",
                                label="capture.csv")
        self.assertEqual(trace.source, "import")
        self.assertEqual(trace.label, "capture.csv")
        self.assertEqual(trace.time_s, (-.001, 0., .001))
        self.assertEqual(trace.duration_s, .002)
        self.assertEqual((trace.minimum, trace.maximum), (0, 200))
        self.assertEqual(WaveformTrace.from_dict(trace.to_dict()), trace)

    def test_rejects_bad_or_unbounded_trace_data(self):
        for text in ["", "t,value\n0,1\n1,2", "time_s,value\n0,1",
                     "time_s,value\n0,1\n0,2", "time_s,value\n1,1\n0,2",
                     "time_s,value\n0,nan\n1,2", "time_s,value\n0,1\n1,32768",
                     "time_s,value\n0,1,2\n1,2", "x" * 2_000_001,
                     'time_s,value\n0,"1\n1,2']:
            with self.subTest(text=text[:30]), self.assertRaises(ValueError):
                parse_trace_csv(text)
        for kwargs in [dict(time_s=(0, 1), value=(1,)),
                       dict(time_s="0,1", value=(1, 2)),
                       dict(time_s=(0, 1), value=(True, 1)),
                       dict(time_s=(0, 1), value=(1, 2), source="device-confirmed"),
                       dict(time_s=tuple(range(20_001)), value=(0,) * 20_001)]:
            with self.subTest(kwargs=str(kwargs)[:60]), self.assertRaises(ValueError):
                WaveformTrace(**kwargs)
        with self.assertRaises(ValueError):
            WaveformTrace.from_dict({"time_s": [0, 1]})

    def test_demo_is_explicitly_synthetic_and_immutable(self):
        trace = demo_trace()
        self.assertEqual(trace.source, "demo")
        self.assertIn("DEMO", trace.label)
        self.assertGreater(trace.maximum, trace.minimum)
        values = [2, 3]
        copied = WaveformTrace([0, 1], values)
        values[0] = 100
        self.assertEqual(copied.value[0], 2)

    def test_suggestions_only_create_drafts_and_require_clock_for_times(self):
        trace = demo_trace()
        suggestion = suggest_parameters(trace)
        self.assertEqual(suggestion["source"], "demo")
        self.assertEqual(suggestion["provenance"], "suggestion")
        self.assertNotIn("time_scan", suggestion["parameters"])
        self.assertNotIn("pc_cmd", suggestion["parameters"])
        self.assertLess(suggestion["parameters"]["threshold_signal_scan"],
                        suggestion["parameters"]["threshold_signal_lock"])
        timed = suggest_parameters(trace, clock_hz=1e6)
        self.assertGreater(timed["parameters"]["time_scan"], 0)
        self.assertIn("采样", timed["duration_basis"])
        self.assertIn("不是", timed["explanation"])
        with self.assertRaises(ValueError):
            suggest_parameters(trace, .2, .3)
        with self.assertRaises(ValueError):
            suggest_parameters(trace, 0, .00001)
        with self.assertRaises(ValueError):
            suggest_parameters(WaveformTrace((0, 1), (5, 5)))
        sparse = suggest_parameters(WaveformTrace((0, 1), (0, 100)), clock_hz=1e6)
        self.assertNotIn("time_scan", sparse["parameters"])

    def test_suggestion_uses_selected_interval_not_entire_recording(self):
        trace = WaveformTrace((0, 1, 2, 3, 4), (-100, 100, 200, 100, 300))
        result = suggest_parameters(trace, 1, 3)
        self.assertEqual(result["parameters"]["threshold_signal_scan"], 125)
        self.assertEqual(result["parameters"]["threshold_signal_lock"], 165)


class ReplayTests(unittest.TestCase):
    def test_replay_is_prediction_and_does_not_auto_relock(self):
        trace = WaveformTrace(tuple(i / 1e6 for i in range(14)),
                              (100, 10, 10, 10, 30, 80, 80, 80, 100, 10, 10, 10, 10, 10))
        result = replay_manual(trace, PARAMETERS, 1e6)
        self.assertEqual(result["provenance"], "prediction")
        self.assertEqual([e["event"] for e in result["events"]],
                         ["predicted_enter", "predicted_loss"])
        self.assertAlmostEqual(result["events"][0]["time_s"], 3e-6)
        self.assertNotIn("locked", result)
        self.assertTrue(result["warnings"])

    def test_threshold_equality_and_short_crossings_do_not_trigger(self):
        trace = WaveformTrace((0, 1, 2, 3, 4, 5), (20, 10, 20, 10, 20, 10))
        result = replay_manual(trace, dict(PARAMETERS, time_scan=2), 1)
        self.assertEqual(result["events"], [])
        with self.assertRaises(ValueError):
            replay_manual(trace, PARAMETERS, None)
        with self.assertRaises(ValueError):
            replay_manual(trace, {"pc_cmd": 1}, 1e6)


class GuidanceTests(unittest.TestCase):
    def test_preflight_gives_actionable_missing_information_not_fake_state(self):
        messages = preflight(ExperimentProfile(), PARAMETERS)
        codes = {m["code"] for m in messages}
        self.assertTrue({"offline", "clock_unknown", "polarity_unknown", "signal_path_missing"} <= codes)
        self.assertTrue(all(m["action"] for m in messages))
        issues = preflight(ExperimentProfile(polarity="peak"), PARAMETERS,
                           topology_issues=["判锁信号未连接"])
        self.assertIn("polarity_incompatible", {m["code"] for m in issues})
        self.assertIn("topology", {m["code"] for m in issues})

    def test_preflight_preserves_but_flags_unsafe_legacy_values(self):
        parameters = dict(PARAMETERS, threshold_signal_lock=1,
                          time_lock=2**32 - 1, coef_scan=-1)
        messages = preflight(ExperimentProfile(polarity="dip", clock_hz=1e6,
                                               units_per_count=.001),
                             parameters, connected=True)
        codes = {m["code"] for m in messages}
        self.assertTrue({"threshold_order", "legacy_counter", "legacy_coefficient"} <= codes)
        self.assertNotIn("offline", codes)
        self.assertNotIn("clock_unknown", codes)
        self.assertEqual(parameters["time_lock"], 2**32 - 1)

    def test_report_contains_provenance_and_never_calls_prediction_real_state(self):
        trace = demo_trace()
        report = export_report(ExperimentProfile(name="测试"), PARAMETERS, trace,
                               {"provenance": "prediction", "events": []})
        for text in ["测试", "demo", "未提供", "预测", "time_scan", "内部信号码"]:
            self.assertIn(text, report)
        self.assertNotIn("设备已锁定", report)
        self.assertIn("未加载", export_report(ExperimentProfile(), PARAMETERS))
        with_events = export_report(ExperimentProfile(), PARAMETERS, trace,
                                    {"events": [{"time_s": .1, "label": "预计接入反馈"}]})
        self.assertIn("0.1 s：预计接入反馈", with_events)


if __name__ == "__main__":
    unittest.main()

# DClocking Integrated UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved B2 precision-instrument workstation UI while preserving DClocking's FPGA routing, parameter, persistence, and Agent contracts.

**Architecture:** Add one focused Qt theme module, then compose the existing MainWindow controls into a canvas-first shell. Keep `DiagramScene`, `NodeItem`, serial routing, parameter handlers, configuration JSON, and the Agent tool chain as the behavioral owners; new UI methods only present or expose those existing behaviors.

**Tech Stack:** Python 3.14, PySide6, standard-library `unittest`, Qt offscreen platform, QSS, QSettings.

**Spec:** `docs/superpowers/specs/2026-08-13-dclocking-integrated-ui-redesign.md`

## Global Constraints

- Keep the native macOS title bar.
- Do not change UART/Bus protocols, FPGA addresses, port numbers, internal node names, parameter encoding, configuration JSON, Agent tool schemas, prompts, or CanvasBridge contracts.
- Do not add a third-party Qt library or font dependency.
- Use `#85172E` as the brand/primary-action color; preserve existing dynamic signal colors.
- `EdgeItem` path start and end must equal the two port `scenePos()` values within `0.01` scene unit.
- Agent is absent in the ordinary entry and hidden by default in the integrated entry.
- Work in the requested DClocking checkout; stage only substantive diffs because unrelated CRLF-only working-tree changes predate this task.
- Tests use `python3 -m unittest`; no pytest installation is required.
- Hardware-dependent checks remain explicitly unverified without a connected FPGA.

---

### Task 1: Theme Tokens and QSS

**Files:**
- Create: `python control/qt_ui_theme.py`
- Create: `tests/qt_test_support.py`
- Create: `tests/test_qt_ui_theme.py`

**Interfaces:**
- Produces: `UiColors`, `build_application_stylesheet() -> str`, `apply_application_theme(widget: QWidget) -> None`, and `draw_node_chrome(painter: QPainter, rect: QRectF, selected: bool = False) -> None`.
- Consumes: PySide6 only.

- [ ] **Step 1: Write the failing theme tests**

Create a real `QApplication` helper and tests that require the new module:

```python
# tests/qt_test_support.py
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "python control"
AGENT = ROOT / "FPGA_Agent"
for path in (str(CONTROL), str(AGENT), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtWidgets import QApplication


def ensure_app():
    return QApplication.instance() or QApplication([])
```

```python
# tests/test_qt_ui_theme.py
import unittest
from PySide6.QtWidgets import QWidget
from qt_test_support import ensure_app
from qt_ui_theme import UiColors, apply_application_theme, build_application_stylesheet


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def test_brand_and_canvas_tokens_match_approved_design(self):
        self.assertEqual(UiColors.PKU_WINE, "#85172E")
        self.assertEqual(UiColors.CANVAS_BG, "#171B1D")
        self.assertEqual(UiColors.SURFACE, "#FBFBF9")

    def test_stylesheet_covers_named_shell_widgets_and_states(self):
        qss = build_application_stylesheet()
        for selector in (
            "#left_rail", "#command_bar", "#inspector_panel",
            "#status_bar", "#agent_toggle_button", ":disabled", ":focus",
        ):
            self.assertIn(selector, qss)

    def test_apply_theme_sets_font_and_stylesheet_without_dependency(self):
        widget = QWidget()
        apply_application_theme(widget)
        self.assertIn("#85172E", widget.styleSheet())
        self.assertIn(widget.font().family(), {"Helvetica Neue", "PingFang SC", ".AppleSystemUIFont"})
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_qt_ui_theme -v
```

Expected: import failure for missing `qt_ui_theme`.

- [ ] **Step 3: Implement the minimal theme module**

Implement exact approved tokens, the widget selectors asserted above, Helvetica Neue/PingFang SC with system fallback, Menlo for log/status/numeric widgets, flat primary/secondary buttons, keyboard focus borders, scrollbars, splitters, tabs, tooltips, and disabled states. `draw_node_chrome` must draw:

```python
def draw_node_chrome(painter, rect, selected=False):
    border = UiColors.ERROR if selected else UiColors.NODE_BORDER
    painter.setBrush(QBrush(QColor(UiColors.NODE_BG)))
    painter.setPen(QPen(QColor(border), 2 if selected else 1))
    painter.drawRoundedRect(rect, 8, 8)
    header = QRectF(rect.left(), rect.top(), rect.width(), min(28.0, rect.height()))
    painter.setBrush(QBrush(QColor(UiColors.NODE_HEADER)))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(header, 8, 8)
    painter.drawRect(QRectF(header.left(), header.bottom() - 8, header.width(), 8))
    painter.setBrush(QBrush(QColor(UiColors.PKU_WINE)))
    painter.drawRoundedRect(QRectF(rect.left() + 8, rect.top() + 7, 4, 14), 2, 2)
```

- [ ] **Step 4: Run tests and verify GREEN**

Run the Task 1 command and expect three passing tests.

- [ ] **Step 5: Commit Task 1**

Stage the new files and commit:

```bash
git commit -m "feat: add DClocking workstation theme"
```

---

### Task 2: Graph, Palette, Node Chrome, and Continuous Edge Geometry

**Files:**
- Modify: `python control/qt_ui_graph.py`
- Modify: `python control/qt_module.py`
- Create: `tests/test_qt_graph_visuals.py`

**Interfaces:**
- Consumes: `UiColors` and `draw_node_chrome` from Task 1.
- Produces: `ComponentPalette.filter_items(query: str) -> None` and consistent node/edge rendering.
- Preserves: `EdgeItem.update_path()`, node classes, port indices, signal types, and module factories.

- [ ] **Step 1: Write failing graph tests**

Tests must use real ports/nodes and cover:

```python
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage, QPainter

from qt_module import ModuleScaler
from qt_ui_graph import ComponentPalette, DiagramScene, EdgeItem
from qt_ui_theme import UiColors


class GraphVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def assert_path_touches_ports(self, edge):
        path = edge.path()
        first = path.elementAt(0)
        last = path.elementAt(path.elementCount() - 1)
        start = edge.start_port.scenePos()
        end = edge.end_port.scenePos()
        self.assertAlmostEqual(first.x, start.x(), delta=0.01)
        self.assertAlmostEqual(first.y, start.y(), delta=0.01)
        self.assertAlmostEqual(last.x, end.x(), delta=0.01)
        self.assertAlmostEqual(last.y, end.y(), delta=0.01)

    def test_forward_reverse_bypass_and_fanout_edges_touch_port_centers(self):
        layouts = (
            (QPointF(0, 0), QPointF(420, 0)),
            (QPointF(0, 0), QPointF(420, 280)),
            (QPointF(420, 0), QPointF(0, 0)),
        )
        for source_pos, target_pos in layouts:
            scene = DiagramScene()
            source = ModuleScaler("线性缩放器", 0, source_pos)
            target = ModuleScaler("线性缩放器", 1, target_pos)
            scene.addItem(source)
            scene.addItem(target)
            edge = EdgeItem(source.out_ports[0], target.in_ports[0])
            scene.addItem(edge)
            self.assert_path_touches_ports(edge)

        scene = DiagramScene()
        source = ModuleScaler("线性缩放器", 0, QPointF(0, 0))
        targets = (
            ModuleScaler("线性缩放器", 1, QPointF(420, -140)),
            ModuleScaler("线性缩放器", 2, QPointF(420, 140)),
        )
        scene.addItem(source)
        for target in targets:
            scene.addItem(target)
            edge = EdgeItem(source.out_ports[0], target.in_ports[0])
            scene.addItem(edge)
            self.assert_path_touches_ports(edge)

    def test_edge_updates_to_new_port_center_after_node_move(self):
        scene = DiagramScene()
        source = ModuleScaler("线性缩放器", 0, QPointF(0, 0))
        target = ModuleScaler("线性缩放器", 1, QPointF(420, 0))
        scene.addItem(source)
        scene.addItem(target)
        edge = EdgeItem(source.out_ports[0], target.in_ports[0])
        scene.addItem(edge)
        target.setPos(520, 180)
        self.app.processEvents()
        edge.update_path()
        self.assert_path_touches_ports(edge)

    def test_palette_filter_hides_nonmatching_modules_and_keeps_section_headers(self):
        palette = ComponentPalette()
        palette.filter_items("PID")
        visible = [palette.item(i).text() for i in range(palette.count()) if not palette.item(i).isHidden()]
        self.assertIn("PID控制器", visible)
        self.assertNotIn("累加器", visible)
        self.assertIn("非组合模块", visible)

    def test_selected_node_renders_wine_accent_strip(self):
        node = ModuleScaler("线性缩放器", 0, QPointF())
        node.setSelected(True)
        image = QImage(220, 180, QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        painter.translate(110, 90)
        node.paint(painter, None, None)
        painter.end()
        accent_x = int(110 + node.boundingRect().left() + 10)
        accent_y = int(90 + node.boundingRect().top() + 12)
        self.assertIn(
            QColor(image.pixelColor(accent_x, accent_y)).name().upper(),
            {UiColors.PKU_WINE, UiColors.ERROR},
        )
```

Also render one selected scaler to a transparent `QImage` and assert a pixel in the node accent strip is `UiColors.PKU_WINE` or `UiColors.ERROR`.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_qt_graph_visuals -v
```

Expected: `ComponentPalette.filter_items` missing and approved node accent pixel absent. Endpoint characterization assertions should already pass; if they fail, preserve the failing cases as the regression before changing geometry.

- [ ] **Step 3: Implement graph and node visual changes**

- Import `UiColors` and `draw_node_chrome` in graph/model modules.
- Replace scene background with `UiColors.CANVAS_BG`.
- Enable antialiasing and draw a low-contrast point grid through `drawBackground`; do not add grid items to the scene.
- Style `BorderPort` labels and port outlines using theme tokens while preserving brush and signal colors.
- Keep `EdgeItem` endpoints at exact `scenePos()` and use round cap/join pens. Keep edge Z below ports/nodes and do not add detached endpoint circles.
- Give `ComponentPalette` a flexible width, semantic object name, section metadata, and `filter_items` that keeps a section header visible only when one of its children matches.
- Replace each node subclass's duplicated shell brush/pen with `draw_node_chrome(painter, rect, self.isSelected())`; retain its existing title and port labels.
- Update drag thumbnails to use the same node chrome.

- [ ] **Step 4: Run tests and verify GREEN**

Run Task 2 tests and Task 1 tests; expect all passing.

- [ ] **Step 5: Commit Task 2**

Stage only substantive graph/model diffs plus tests and commit:

```bash
git commit -m "feat: refresh graph and node visuals"
```

---

### Task 3: Canvas-First MainWindow Shell, Inspector, Log, and Settings

**Files:**
- Modify: `python control/qt_ui_mainwindow.py`
- Create: `tests/test_qt_mainwindow_shell.py`

**Interfaces:**
- Consumes: `apply_application_theme`, `ComponentPalette.filter_items`, and all existing MainWindow controls/slots.
- Produces: `register_agent_dock(dock: QDockWidget) -> QAction`, `set_log_expanded(expanded: bool) -> None`, `is_log_expanded() -> bool`, `open_agent_settings() -> None`, and injectable `MainWindow(settings: QSettings | None = None)`.
- Preserves: all existing public fields used by `CanvasBridge` (`scene`, `view`, `palette`, `port_ctrl`, `router`) and all hardware/configuration methods.

- [ ] **Step 1: Write failing shell tests**

Use an INI-format `QSettings` in a temporary directory and construct a real MainWindow. Assert:

```python
def test_b2_shell_has_named_regions_and_canvas_first_split(self):
    self.assertIsNotNone(self.window.findChild(QWidget, "left_rail"))
    self.assertIsNotNone(self.window.findChild(QWidget, "command_bar"))
    self.assertIsNotNone(self.window.findChild(QWidget, "inspector_panel"))
    self.assertIsNotNone(self.window.findChild(QWidget, "status_bar"))
    self.assertFalse(self.window.agent_toggle_btn.isVisible())
    self.assertFalse(self.window.agent_fab.isVisible())
    self.assertFalse(self.window.is_log_expanded())

def test_existing_controls_and_slots_are_reused(self):
    self.assertEqual(self.window.connect_btn.text(), "连接设备")
    self.assertIs(self.window.workspace_splitter.widget(0), self.window.view)
    self.assertTrue(self.window.save_cfg_btn.receivers(self.window.save_cfg_btn.clicked) >= 1)

def test_stderr_expands_log_and_preserves_message(self):
    self.window.set_log_expanded(False)
    self.window._append_error_text("route failed\n")
    self.assertTrue(self.window.is_log_expanded())
    self.assertIn("route failed", self.window.log_output.toPlainText())

def test_ui_state_round_trip_restores_log_and_splitter(self):
    self.window.set_log_expanded(True)
    self.window.workspace_splitter.setSizes([900, 310])
    self.window._save_ui_state()
    restored = MainWindow(settings=self.settings)
    self.assertTrue(restored.is_log_expanded())
    self.assertGreater(restored.workspace_splitter.sizes()[1], 0)
```

Always call `close()` in teardown to restore stdout/stderr.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_qt_mainwindow_shell -v
```

Expected: missing object names, methods, settings injection, and B2 layout.

- [ ] **Step 3: Implement the B2 shell**

- Change `MainWindow.__init__` to accept optional settings while preserving no-argument callers.
- Reuse the seven existing control instances in a named `command_bar`; rename only visible text (`连接` → `连接设备`) without changing signal owners.
- Build a 58 px named `left_rail` with design/parameter/config/log/settings buttons and accessible names/tooltips.
- Convert the side panel to one vertical inspector: search field, palette, selected-parameter area. Connect search text to `palette.filter_items`.
- Add horizontal `workspace_splitter` (`view`, `side_panel`) and vertical `content_splitter` (`workspace_splitter`, `log_panel`).
- Add named status labels for offline/mode/route count and a log toggle.
- Implement log expansion without deleting content; stderr calls `_append_error_text` and expands.
- Install an event filter on the view viewport to keep `agent_fab` at its lower-right corner. Both Agent buttons remain hidden until Task 4 registration.
- Persist geometry, splitter sizes, log state, and last log height via the injected/default QSettings.
- Call `_refresh_ui_status()` after mode and connection creation/removal paths, reading real scene/router state only.

- [ ] **Step 4: Run tests and verify GREEN**

Run Task 3, Task 2, and Task 1 tests. Expect all passing and no Qt warnings.

- [ ] **Step 5: Commit Task 3**

Stage substantive MainWindow changes and tests, then commit:

```bash
git commit -m "feat: add canvas-first workstation shell"
```

---

### Task 4: Integrated Agent Drawer and Unified Chat Styling

**Files:**
- Modify: `FPGA_Agent/chat_styles.py`
- Modify: `FPGA_Agent/agent_chat_widget.py`
- Modify: `FPGA_Agent/main.py`
- Create: `tests/test_agent_ui_integration.py`

**Interfaces:**
- Consumes: `MainWindow.register_agent_dock` and theme token values.
- Produces: `AgentChatWidget.open_settings() -> None` as a public presentation method.
- Preserves: `user_message_submitted`, message methods, thinking state, tool display, config file format, and AgentCore wiring.

- [ ] **Step 1: Write failing Agent UI tests**

```python
def test_registered_agent_is_hidden_by_default_and_two_controls_share_state(self):
    chat = AgentChatWidget(self.window)
    action = self.window.register_agent_dock(chat)
    self.assertFalse(chat.isVisible())
    self.assertFalse(action.isChecked())
    self.window.agent_toggle_btn.click()
    self.assertTrue(chat.isVisible())
    self.window.agent_fab.click()
    self.assertFalse(chat.isVisible())

def test_hiding_agent_does_not_destroy_messages(self):
    chat = AgentChatWidget(self.window)
    self.window.register_agent_dock(chat)
    chat.add_assistant_message("persistent message")
    chat.hide()
    chat.show()
    self.assertIn("persistent message", chat._msg_container.findChildren(QTextBrowser)[0].toPlainText())

def test_chat_uses_precision_workstation_colors_and_accessible_controls(self):
    chat = AgentChatWidget(self.window)
    self.assertIn("#85172E", chat.widget().styleSheet())
    self.assertEqual(chat._send_btn.accessibleName(), "发送 Agent 消息")
    self.assertTrue(callable(chat.open_settings))
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_agent_ui_integration -v
```

Expected: missing registration/public settings/accessibility behavior and old blue-purple chat theme.

- [ ] **Step 3: Implement Agent integration**

- Change chat QSS to `#FBFBF9`/`#272D30` surfaces with `#85172E` user/action accents, visible focus, and Menlo tool output.
- Add semantic object/accessibility names to header, settings, message scroll, input, and send button.
- Rename `_open_settings` to public `open_settings` and keep a private alias only if existing internal connections need it.
- Implement `MainWindow.register_agent_dock`: add to right dock area, wire `toggleViewAction`, toolbar button and floating button, hide by default, and expose settings rail button.
- Update `FPGA_Agent/main.py` to call `window.register_agent_dock(chat)` instead of calling `addDockWidget` directly. Do not change Agent component creation or signals.

- [ ] **Step 4: Run tests and verify GREEN**

Run all tests from Tasks 1–4 and expect all passing.

- [ ] **Step 5: Commit Task 4**

Stage only Agent presentation/integration files and tests, then commit:

```bash
git commit -m "feat: integrate on-demand FPGA Agent drawer"
```

---

### Task 5: Offline Functional Regression and Responsive Screenshots

**Files:**
- Create: `tests/test_ui_functional_regression.py`
- Create: `python tools/capture_ui_screenshots.py`
- Modify: `python control/qt_UI1.py`
- Modify: `FPGA_Agent/main.py`

**Interfaces:**
- Consumes: the completed B2 shell and both entry points.
- Produces: deterministic screenshot files under an explicit output directory passed to the script; no screenshots are committed.
- Preserves: entry point command behavior.

- [ ] **Step 1: Write failing functional tests**

Cover real offline flows without opening file dialogs:

```python
def test_node_create_connect_move_disconnect_and_index_reuse(self):
    source_index = self.window.view._alloc_index("线性缩放器")
    target_index = self.window.view._alloc_index("线性缩放器")
    source = self.window.view.module_factory["线性缩放器"](
        "线性缩放器", source_index, QPointF(0, 0)
    )
    target = self.window.view.module_factory["线性缩放器"](
        "线性缩放器", target_index, QPointF(420, 0)
    )
    self.window.scene.addItem(source)
    self.window.scene.addItem(target)
    edge = self.window.scene.create_connection(source.out_ports[0], target.in_ports[0])
    self.assert_path_touches_ports(edge)
    target.setPos(520, 180)
    self.app.processEvents()
    self.assert_path_touches_ports(edge)
    self.window.scene.remove_connection(target.in_ports[0])
    self.window.view.remove_node(target)
    QTest.qWait(250)
    self.assertEqual(self.window.view._alloc_index("线性缩放器"), target_index)

def test_configuration_dict_round_trip_preserves_nodes_direct_params_and_edges(self):
    source, target = self.add_scaler_pair()
    source.set_params({"scale": 0.75})
    self.window.scene.create_connection(source.out_ports[0], target.in_ports[0])
    expected = self.window._build_config_dict()
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
        json.dump(expected, handle, ensure_ascii=False)
        handle.flush()
        with patch(
            "qt_ui_mainwindow.QFileDialog.getOpenFileName",
            return_value=(handle.name, "JSON (*.json)"),
        ):
            self.window.load_configuration()
    self.assertEqual(self.window._build_config_dict(), expected)

def test_parameter_failure_rolls_back_staged_value(self):
    node, _ = self.add_scaler_pair()
    key = next(iter(node.get_params()))
    previous = node.get_params()[key]
    node.set_params({key: previous + 1})
    self.window._pending_param_values[(id(node), key)] = previous
    with patch.object(self.window.port_ctrl, "send_param", side_effect=RuntimeError("offline")):
        self.window._apply_param_to_hardware(node, key, previous + 1)
    self.assertEqual(node.get_params()[key], previous)

def test_ordinary_and_integrated_windows_construct_at_target_sizes(self):
    for width, height in ((1280, 720), (1600, 900), (1920, 1080)):
        for factory in (create_ordinary_window, create_integrated_window):
            window = factory()
            window.resize(width, height)
            window.show()
            self.app.processEvents()
            for object_name in ("commandBar", "canvasFrame", "inspectorPanel", "statusStrip"):
                widget = window.findChild(QWidget, object_name)
                self.assertIsNotNone(widget)
                top_left = widget.mapTo(window, QPoint(0, 0))
                self.assertTrue(window.rect().contains(QRect(top_left, widget.size())))
            window.close()
```

Because `Port` is a physical boundary, use a minimal fake only for the failing send call; use real nodes, scene, MainWindow, and parameter cache.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_ui_functional_regression -v
```

Expected: screenshot/entry helper interfaces or responsive assertions fail until the final composition details are implemented.

- [ ] **Step 3: Add deterministic screenshot mode and finish responsive details**

- Factor each entry point to expose `create_window()` while keeping `main()` behavior unchanged.
- Implement `capture_ui_screenshots.py --output <dir>` that uses real windows, creates a representative PID→Scaler graph, expands/collapses Agent/log states, renders 1280×720, 1600×900, and 1920×1080 PNGs, and closes every window.
- Adjust minimum sizes, splitter stretch factors, text elision/scrolling, and inspector width until assertions and screenshots match the approved B2 direction.
- Do not add device fakes to production code.

- [ ] **Step 4: Run the full offline suite and screenshot script**

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
tmp_ui_shots=$(mktemp -d)
QT_QPA_PLATFORM=offscreen python3 'python tools/capture_ui_screenshots.py' --output "$tmp_ui_shots"
find "$tmp_ui_shots" -type f -name '*.png' -size +10k | sort
```

Expected: all unittest cases pass and six nontrivial PNG files exist (ordinary/integrated at three sizes).

- [ ] **Step 5: Run syntax and scope checks**

```bash
python3 -m compileall -q 'python control' FPGA_Agent tests 'python tools/capture_ui_screenshots.py'
git diff --ignore-space-at-eol --check
git diff --ignore-space-at-eol -- 'packages' modules Top.vhdl main_control.vhdl central_control.vhdl 'python control/port_numbers.py' 'python control/qt_Port.py' FPGA_Agent/tool_definitions.py FPGA_Agent/tool_executor.py FPGA_Agent/canvas_bridge.py
```

Expected: compilation/checks exit zero; the protected-contract diff command prints nothing.

- [ ] **Step 6: Launch and inspect both GUI entries**

```bash
python3 'python control/qt_UI1.py'
python3 FPGA_Agent/main.py
```

Inspect with the local UI surface: native window controls, B2 layout, palette drag, node move, continuous connections, log toggle, Agent toggle, close/float/redock, and message persistence. Terminate only the launched verification processes after inspection.

- [ ] **Step 7: Commit Task 5**

Stage the regression tests, screenshot script, and entry-point refactor; commit:

```bash
git commit -m "test: cover integrated UI regression flows"
```

---

### Task 6: Final Verification and Delivery Audit

**Files:**
- Modify only if verification reveals a tested defect.

**Interfaces:**
- Consumes: all prior tasks and the approved spec.
- Produces: verification evidence and an explicit list of hardware-only checks not run.

- [ ] **Step 1: Run fresh complete verification**

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
python3 -m compileall -q 'python control' FPGA_Agent tests 'python tools/capture_ui_screenshots.py'
git diff --ignore-space-at-eol --check
```

- [ ] **Step 2: Audit requirements against the spec**

Confirm with source searches and runtime inspection:

- B2 named layout regions exist.
- ordinary entry contains no Agent button.
- integrated Agent is hidden by default and state-preserving.
- existing hardware/config methods and Agent tool schemas have no substantive diff.
- edge endpoint tests cover forward, reverse, bypass, fan-out, and moved nodes.
- screenshot dimensions and non-empty content cover all target sizes.

- [ ] **Step 3: Record unverified hardware work**

The final report must say that serial connection, initialization, route upload, parameter readback, `sync_from_device`, Vivado, and target-board behavior were not verified unless a physical FPGA was actually connected during Task 5.

- [ ] **Step 4: Review and finish the branch/workspace**

Use `superpowers:requesting-code-review`, address verified findings, rerun the full suite, then use `superpowers:finishing-a-development-branch`. Do not push unless the user asks.

# 概述
这是一个用于创建和管理信号处理模块（如PID控制器、累加器、滤波器等）及其连接的图形化节点编辑器。它支持模块拖放、连线、参数设置、视图控制以及与硬件端口的信号路由。

# 模块依赖图（新版）
当前代码已按“入口层 -> 编排层 -> 图形层/工具层 -> 设备与模块层”拆分。

依赖关系（简图）：

qt_UI1.py
  -> qt_ui_mainwindow.py
      -> qt_ui_graph.py
      -> qt_ui_utils.py
      -> qt_Port.py
      -> qt_module.py
      -> port_numbers.py

qt_ui_graph.py
  -> qt_module.py

qt_ui_utils.py
  -> qt_Port.py
  -> port_numbers.py

qt_Port.py
  -> qt_uart.py
  -> qt_env.py

说明：
- qt_UI1.py：仅保留程序启动与主窗口装配。
- qt_ui_mainwindow.py：主业务编排（同步、路由、参数下发、配置读写）。
- qt_ui_graph.py：纯图形交互（Scene/View/Edge/Palette）。
- qt_ui_utils.py：纯工具函数（端口映射、节点映射、端口扩展方法）。

# 核心功能模块

## 1. 主窗口与基础布局
**功能:** 提供应用程序的主窗口，包含菜单栏（选择串口、模式、连接）、右侧模块列表、左侧画布以及状态栏。
- **代码位置:** qt_UI1.py中通过 QMainWindow派生的主类。
- 主窗口采用 QSplitter分割布局，右侧是 QListWidget显示的模块列表，左侧是承载 DiagramScene的 DiagramView画布视图，上方是菜单栏，可以选择串口、模式以及连接串口。

## 2.模块列表
**功能:** 在界面右侧显示可用的模块类型列表，用户可从中拖拽模块到画布。
- **代码位置:** qt_UI1.py主窗口初始化部分，通过 QListWidget实现。
- 模块名称包括：*"PID控制器"*、*"累加器"*、*"三角函数运算器"*、*"反三角函数运算器"*、*"线性缩放器"*、*"FIR滤波器"*、*"线性变换器"*、*"混频器"*、*"解卷绕器"*、*"PDH状态机"*、*"LO自动校准状态机"*，以及组合模块 *"正弦波发生器"*和 *"数字控制振荡器"*。

## 3.画布场景
**功能:** 作为节点的图形化容器，管理所有节点、端口、连线等图形项的添加、删除、交互和渲染。
- **代码位置:** qt_UI1.py中的 DiagramScene类。
- 继承自 QGraphicsScene，设置深色背景。
- 管理连线创建的临时预览线。
- 包含左侧8个输出端口和右侧8个输入端口 (BorderPort)。
- 处理鼠标事件以进行连线、删除连线等操作。

## 4.画布视图
**功能:** 提供对画布的滚动、缩放、拖拽查看等视图控制。
- **代码位置:** qt_UI1.py中的 DiagramView类。
- 继承自 QGraphicsView，渲染 DiagramScene。
- 实现视图的拖拽平移（按住空白区域拖动）和滚轮缩放。
- 接收拖拽事件，处理模块从列表到画布的放置。
- 动态更新边框端口的位置以匹配视口。

## 5.节点模块
**功能:** 表示各种信号处理模块的图形化实体，每个模块包含输入/输出端口，可移动、选中和双击打开参数对话框。
- **代码位置:**
  - 基础节点类: qt_module.py中的 NodeItem类。
  - 具体模块类: qt_module.py中的 ModulePID、ModuleAccumulator、ModuleBase、ModuleScaler、ModuleFIRFilter、ModuleLinerTransformer、ModulePDHFSM、ModuleSCLOFSM等。
- 每个模块类定义了自身的尺寸、端口数量、端口标签、信号类型、最大实例数和参数模式。
- 端口通过 PortItem类表示，具有信号类型标记、颜色、工具提示和交互功能。

## 6.端口
**功能:** 表示节点的输入/输出连接点，带有信号类型图标，是连线的起点和终点。

- **代码位置:**
  - 通用端口: qt_module.py中的 PortItem类。
  - 边框端口: qt_UI1.py中的 BorderPort类。
- 端口绘制为圆形，并带有指示信号类型的图形标记（如五角星表示 level，圆形表示 phase，方块表示 bool，菱形表示 differential）。
  - 位置：qt_module.py中_draw_signal_markers

- 输出端口有唯一的颜色，输入端口为固定颜色。

## 7.连线
**功能:** 在两个端口之间建立连接，以可视化的线条表示数据流。支持正向连接、反向连接（绕行）和自动路径计算。
- **代码位置:** qt_UI1.py中的 EdgeItem类。
- 线条颜色与源输出端口颜色一致。
- 线条样式反映信号类型：实线 (level)、虚线 (phase)、点划线 (differential)。
- 线条宽度表示是否承载物理信号。
- 路径计算考虑节点相对位置和垂直距离，自动生成Z字形或多段绕行路径。
- 连线可悬停高亮、选中。

## 8.连线创建与删除
**功能:** 通过鼠标交互创建和删除连线。
- **代码位置:**
  - 连线创建: DiagramScene中的 mousePressEvent、mouseMoveEvent、mouseReleaseEvent方法，以及 finalize_connection方法。
  - 连线删除: DiagramScene中的 remove_connection方法和 EdgeItem的 remove方法。
- 创建流程：
  1. 在输出端口按下鼠标，开始拖动。
  2. 移动鼠标时，显示临时预览线。
  3. 释放鼠标在输入端口上，完成连线。
- 在已有连接的输入端口上按下鼠标，删除该连线。
- 连线建立时会进行信号类型匹配检查。

## 9.参数对话框
**功能:** 双击节点模块打开参数设置对话框，修改模块内部参数。
- **代码位置:**
  - 对话框类: qt_module.py中的 ParamDialog类。
  - 触发逻辑: NodeItem的 mouseDoubleClickEvent和 open_param_dialog方法。
- 参数根据模块对应的模式（"direct"或 "indirect"）和 free_mode属性动态生成表单。
- 支持 int、float、bool、str类型的参数控件。
- 数值和文本参数支持按 Enter 立即提交当前字段，不需要点击按钮。
- 若输入框失去焦点且未按 Enter 提交，该字段会回滚到上一次已确认的值，避免联动参数被旧值覆盖。
- 仍保留“确认本模块参数（全部）”按钮，用于一次性提交当前模块全部字段。

## 10.模块拖放
**功能:** 从左侧列表拖拽模块到画布创建实例，或在画布内拖拽节点移动位置，或将节点拖出画布到右侧组件栏区域进行删除。
- 代码位置:
  - 列表到画布: DiagramView的 dragEnterEvent、dragMoveEvent、dropEvent方法。
  - 画布内移动/删除: DiagramView的 mousePressEvent、mouseMoveEvent、mouseReleaseEvent方法，以及 remove_node方法。
- 模块在画布内有实例数量限制 (maxm)。
- 删除节点时会自动断开并清理其所有连线。

## 11.开发者模式
**功能:** 切换开发者模式，该模式下参数编辑和连线规则更加宽松。
- **代码位置:** DiagramScene中的 set_developer_mode方法，并在 EdgeItem的样式计算中使用。
- 在开发者模式下，物理信号类型 (level, phase, differential) 之间允许连线，即使端口声明的信号不严格匹配。
- 某些模块参数的 free属性为 False的参数在开发者模式下可编辑。

## 12. 组合模块
**功能:** 预定义的一组子模块的集合，一键放置多个已连接的模块。
- **代码位置:** qt_module.py中的 CompositeModule基类及其子类 SINGenerator和 DigitalControlledOscillator，以及 composite_modules字典。
- 在 DiagramView的 dropEvent中识别并创建组合模块。

## 13. 信号路由与硬件映射
**功能:** 将图形化的节点连接映射到硬件端口地址，实现信号的实际路由。
- **代码位置:** qt_UI1.py中的 _resolve_port_number函数，以及 NodeSignals类的 connection_created和 connection_removed信号。
- 当连线创建或删除时，通过信号触发外部逻辑（如 module_signal_router），将节点名称和端口索引解析为具体的硬件端口号 (pn模块中定义的常量)。

## 14. 串口通信支持
**功能:** 为参数应用处理器提供通过串口写入硬件总线的能力。
- **代码位置:** qt_UI1.py开头的 _ensure_port_methods函数和 PortBus类。
- 通过 set_param_apply_handler设置全局参数应用处理器，当节点参数修改时，可调用 write_bus方法将参数写入硬件。

## 15. 模块实例管理
**功能:** 管理画布上每种类型模块的实例索引分配与回收，确保不超过最大实例数。
- **代码位置:** DiagramView中的 _used_indices字典、_alloc_index和 _free_index方法。

# 交互流程总结
- 添加模块：从右侧列表拖拽模块类型到左侧画布。
- 连接模块：点击输出端口，拖动到输入端口。
- 移动模块：在模块上按住拖动。
- 删除模块：将模块拖出画布到右侧组件栏区域。
- 删除连线：点击已有连线的输入端口。
- 设置参数：双击模块。
- 平移视图：在画布空白处按住拖动。
- 缩放视图：使用鼠标滚轮。

# 协作维护说明（简版）
为避免再次出现大文件耦合，建议按下面规则协作开发：

1. 入口文件保持稳定
- qt_UI1.py 只做启动，不写业务逻辑和绘制逻辑。

2. 变更就近归属
- 连接交互、拖拽、缩放、连线路径：改 qt_ui_graph.py。
- 同步设备、路由写入、参数下发、配置保存：改 qt_ui_mainwindow.py。
- 端口号映射、节点名映射、通用小函数：改 qt_ui_utils.py。
- 串口协议与硬件模块读写：改 qt_Port.py / qt_uart.py / qt_env.py。

3. 降低循环依赖
- graph 层不反向依赖 mainwindow 层。
- utils 层不依赖 graph 层。
- 若出现跨层复用需求，优先下沉到 utils。

4. 扩展新模块的最小修改面
- 新增模块类型时，优先按顺序修改：
  1) qt_module.py（模块类/参数）
  2) qt_ui_graph.py（模块工厂映射）
  3) qt_ui_utils.py（端口号映射）
  4) qt_ui_mainwindow.py（模块身份解析，如需下发参数）

5. 提交前检查建议
- 至少检查 qt_UI1.py、qt_ui_mainwindow.py、qt_ui_graph.py、qt_ui_utils.py 无语法错误。
- 手动验证 4 条关键流程：连接串口、同步下位机、拖拽连线、参数下发。
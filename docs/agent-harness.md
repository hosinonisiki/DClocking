# Agent 内核：DeepSeek Harness

## 启动和回退

正常安装 `python -m pip install -r requirements.txt` 后，
在项目根目录运行 `python -m FPGA_Agent.main` 启动。Windows 也可运行 `scripts/start-windows.ps1`。
Python 需为 3.10 或更新版本。Harness 使用固定版本的官方 Python SDK 及其匹配的
原生运行时，不要求开发者另装 Node.js 或 pnpm。

Agent 设置中的“执行引擎”默认为 **DeepSeek Harness**，也可以显式选择
**Native 原生兼容引擎**。两种引擎都经过同一个受控工具网关。Harness 安装、启动或
API 调用失败会显示错误，**不会自动改用另一个引擎**。设置变化会开启新模型会话，
但不清空画布、修改硬件配置或撤销已执行的操作。

API Endpoint、模型名和系统凭据存储沿用原有设置。Harness 使用官方
`dsh-llm-pi-ai` 的 OpenAI-compatible 适配器，保留 `/chat/completions` 协议，
不把现有 DeepSeek/OpenAI 配置自动改成另一种 API。密钥不写入公共配置文件。

仅安装基础功能、尚未安装 SDK 时，界面仍可启动并说明缺少的依赖；安装
`requirements-harness.txt` 或在设置中明确选择 Native 后再发送消息。

## 职责边界

```text
Qt 聊天面板（发送 / 停止 / 单次确认）
        │
RuntimeAgentCore（会话、事件、内核选择）
        ├── Harness 独立运行时：模型调用、工具迭代、会话
        └── Native 兼容循环
                    │ 结构化工具请求
          ToolGateway（校验、审批、取消、主线程调度）
                    │
          ToolExecutor → CanvasBridge → 原有 UI / 硬件控制
```

Harness 不是硬件控制器。它不直接触摸 Qt 对象、串口、FPGA 寄存器或 VHDL。
只开放现有的九个项目工具：创建模块、连线、模块查询、断开/删除、设参、模块信息、
代码生成、布局和清空画布。默认终端、任意文件编辑、网络检索和子 Agent 不开放。
内部工具桥只服务本次本地运行时，并使用随机认证令牌；它不是公开的 MCP 控制服务。
原有 `mcp_server.py` 仍然是只读目录/设计校验服务。

## 工具权限和状态

- 模块查询：只读，结果来自项目目录或 PC 画布，不等价于硬件读回。
- 离线画布配置：参数校验通过后更新本地配置，不宣称已下发到 FPGA。
- 在线硬件相关改动：界面显示具体工具和参数，由用户“允许一次”或“拒绝”。
- 删除模块、清空画布、代码生成：需要用户确认；模型提交 `confirm=true` 不能代替确认。
- 参数名、类型、范围、模块白名单由宿主校验；原图层连线与实例限制继续生效。

| 结果状态 | 含义 |
| --- | --- |
| `read_only` | 本地只读查询完成 |
| `local_staged` | 本地配置已更新，未验证硬件 |
| `hardware_unverified` | 已调用原硬件路径，但没有硬件读回证据 |
| `failed` | 校验或执行失败；检查具体错误，不自动重复不确定的副作用 |
| `denied` / `cancelled` | 用户拒绝或已取消，未开始的操作不会执行 |

任何写入成功都不能被解释为 PDH 已锁定。`pc_cmd` 是请求，不是观测到的状态。
需要实际测量/读回才能确认实验状态；当前工具不会伪造 `readback_verified=true`。

## 停止、会话及诊断

发送后箭头变为停止按钮。停止会打断模型运行并阻止尚未执行的工具，正在等待确认的
请求默认拒绝。已经执行的原子操作不回滚。UI 等待工作线程确实结束后才恢复发送，
避免旧响应覆盖新任务。工具卡按运行 ID 和调用 ID 更新，展示真实执行结果。

一般停止后可直接发送下一条消息。若运行时无响应而被强制终止，请打开 Agent 设置
并重新保存，开启新的模型会话；不用清空画布。执行超时会显示为错误而非“用户停止”，
同时释放待确认工具，避免窗口卡住。取消前已完成的工具回执会在必要时补充给下一轮。

Harness 的工作目录、配置和会话与全局 `~/.dsh` 隔离；关闭额外的 DeepSeek
session-log/package-inventory 上传。模型服务仍然会接收完成本次请求所必需的提示词
与工具返回数据；这不意味着完全离线。
隔离会话保存在本次运行的临时目录中，关闭/重置内核后清理，不是跨程序重启的长期记忆。

诊断时先检查工具卡的具体状态，再区分依赖/运行时启动错误、API 错误、参数错误和
硬件不可用。不要通过延长超时、自动放行审批或静默切换内核掩盖错误。

## 开发验证

```shell
python -m unittest tests.test_agent_cancellation tests.test_agent_runtime_core \
  tests.test_agent_harness_ui tests.test_tool_gateway tests.test_harness_runtime -v
python -m unittest discover -s tests -v
```

真实 SDK/进程及 Qt 链路测试需显式启用：

```shell
# macOS / Linux
DCLOCKING_TEST_HARNESS_RUNTIME=1 python -m unittest discover -s tests -v
# Windows PowerShell
$env:DCLOCKING_TEST_HARNESS_RUNTIME = '1'
python -m unittest discover -s tests -v
```

原生 macOS 视觉验证（只使用测试配置，不会读取/修改用户密钥或连接实验硬件）：

```shell
QT_QPA_PLATFORM=cocoa DCLOCKING_TEST_HARNESS_RUNTIME=1 \
DCLOCKING_HARNESS_SCREENSHOTS=/tmp/dclocking-harness-visual \
python -m unittest tests.test_harness_qt_e2e -v
```

测试需要覆盖：真实主线程派发、离线配置、在线操作确认、拒绝/取消后不执行、重复工具
卡区分、模型故障不自动回退、停止后重新发送、退出时清理运行时。真实 SDK 验证应使用
本机假模型服务，不消耗真实模型额度、不连接实验硬件。macOS 验证不能代替 Windows
原生运行结果，更不能代替 FPGA 在环验证。

上游为开发预览版本；升级时同时审查 SDK API、配置插件树、实际工具白名单和上述测试。
当前固定版本的取消原因使用不可变对象，避免底层网络库修改它后破坏会话记录；宿主
还会等待运行时 `whenIdle()` 的确认再接收下一轮。升级时必须保留“原子工具执行中停止，
随后立即发起下一轮”的重复测试，不能用延迟重试或加长超时替代这一收尾边界。
在 Python 3.14 测试中，上游 SDK 关闭时仍可能报告标准输出/错误管道的
`ResourceWarning`；测试已确认子进程退出，但没有通过屏蔽警告或修改 SDK 私有对象
掩盖这一上游资源清理问题。后续 SDK 升级需一并检查。

另发现原有 `code_generator.py` 的 `_gen_python_node(max_inst, ...)` 引用了未定义的
`max_instances`，可能导致 `generate_module` 失败。这是重构前已存在的代码生成器问题，
此次未改动该生成器；工具网关会保留并显示失败，不将授权通过或调用发出当作生成成功。
参考：[官方 SDK 文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/python-sdk.md)。

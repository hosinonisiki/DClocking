# DClocking 本地 MCP Server

DClocking 提供一个可在本机独立启动的 MCP Server，供 Codex、Claude Desktop、Cursor 等支持 MCP 的客户端读取项目模块目录并进行离线校验。

## 能力边界

首版 MCP Server 是**只读、离线**的设计辅助服务：

- 可以查询模块类型、端口和可配置参数；
- 可以校验参数值、模块连接关系和 MCP 候选模块图；
- 返回的是项目中的静态注册信息及离线校验结果，不代表 FPGA 当前的实时状态；
- 不读取 API 密钥或 `FPGA_Agent/config.json`；
- 不访问或修改 Qt 画布，不连接设备，也不向 FPGA 写入任何数据；
- 不提供清空画布、生成代码或设置硬件参数等有副作用的操作。

因此，MCP 返回“校验通过”只说明输入符合当前软件定义，不能作为硬件已经连接或参数已经写入 FPGA 的证明。

## 环境要求

- Python 3.10 或更高版本；
- macOS、Linux 或 Windows；
- 首次启动需要网络，以便在项目根目录的 `.venv` 中安装轻量的 `requirements-mcp.txt` 依赖。不会为了只读 MCP 服务下载 Qt、SciPy 等桌面端依赖；后续仅在 MCP 依赖文件变化时重新安装。

`requirements.txt` 与 `requirements-mcp.txt` 均固定使用 `mcp==2.2.0`，避免 MCP SDK 自动升级造成接口行为变化。

## 启动方式

### macOS / Linux

在仓库根目录执行：

```bash
./scripts/start-mcp-server.sh
```

如果脚本没有执行权限，也可以执行：

```bash
sh ./scripts/start-mcp-server.sh
```

### Windows PowerShell

在仓库根目录执行：

```powershell
.\scripts\start-mcp-server.ps1
```

如果当前 PowerShell 限制本地脚本，可只为本次进程放开限制：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-mcp-server.ps1
```

两个脚本都会创建或复用项目根目录的 `.venv`，只安装轻量 MCP 依赖，然后从仓库根目录运行：

```text
python -m FPGA_Agent.mcp_server
```

脚本后面的所有参数都会原样传给 MCP Server。

## 传输模式

### 本地 stdio（默认）

不提供额外参数时使用 stdio。这是本地 MCP 客户端推荐的启动方式，客户端负责启动和关闭子进程。stdio 模式不需要端口，也不需要 `DCLOCKING_MCP_TOKEN`。

不要直接在普通终端中向 stdio 进程输入自然语言；应由 MCP 客户端通过协议与进程通信。

### 本地 Streamable HTTP（可选）

HTTP 模式只允许绑定本机回环地址，并且必须先设置 `DCLOCKING_MCP_TOKEN`。令牌必须为 32–256 个可见 ASCII 字符，不能包含空白。不要把令牌写入仓库或配置示例。

这是本机预共享 Bearer Token 模式，不提供 OAuth 登录或自动取令牌。HTTP 客户端必须支持自定义请求头，并在每次请求中发送 `Authorization: Bearer <令牌>`。如果客户端不能配置该请求头，请使用默认的 stdio 模式。

macOS / Linux：

```bash
export DCLOCKING_MCP_TOKEN='替换为随机且足够长的本地令牌'
./scripts/start-mcp-server.sh --transport streamable-http --host 127.0.0.1 --port 8765
```

Windows PowerShell：

```powershell
$env:DCLOCKING_MCP_TOKEN = '替换为随机且足够长的本地令牌'
.\scripts\start-mcp-server.ps1 --transport streamable-http --host 127.0.0.1 --port 8765
```

默认 MCP 地址为：

```text
http://127.0.0.1:8765/mcp
```

首版拒绝 `0.0.0.0`、局域网地址和公网地址，避免把本地项目能力意外暴露给其他主机。客户端连接 HTTP 时需要按其 MCP 配置方式携带相同令牌。

## 本地客户端配置

下面示例使用 stdio，让客户端自动调用启动脚本。请把路径替换为你电脑上的仓库绝对路径；路径中包含空格时也必须保持为一个完整字符串。

### Codex

在 Codex MCP 配置中增加：

```toml
[mcp_servers.dclocking]
command = "/绝对路径/DClocking/scripts/start-mcp-server.sh"
args = []
```

Windows 示例：

```toml
[mcp_servers.dclocking]
command = "powershell"
args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\绝对路径\\DClocking\\scripts\\start-mcp-server.ps1"]
```

### Claude Desktop

在 Claude Desktop 的 MCP JSON 配置中增加 `dclocking`：

```json
{
  "mcpServers": {
    "dclocking": {
      "command": "/绝对路径/DClocking/scripts/start-mcp-server.sh",
      "args": []
    }
  }
}
```

### Cursor

在项目或用户级 MCP JSON 配置中增加：

```json
{
  "mcpServers": {
    "dclocking": {
      "command": "/绝对路径/DClocking/scripts/start-mcp-server.sh",
      "args": []
    }
  }
}
```

不同版本客户端的配置入口可能不同，但 stdio 配置的核心始终是一个 `command` 和参数数组。修改配置后请完全重启对应客户端，让它重新发现 MCP Server。

## 首版工具

客户端连接成功后可发现以下只读工具：

- `list_module_types`：列出可用 FPGA 模块类型；
- `get_module_spec`：读取指定模块的端口、参数、范围和说明；
- `validate_parameters`：离线验证一组模块参数；
- `validate_connection`：检查两个模块端口的连接兼容性；
- `validate_design`：验证 MCP 专用的候选模块图，不加载、不保存、不写硬件。它不是 Qt 的 `version/nodes/edges` 保存文件格式。

`validate_design` 使用独立的 `nodes/connections` 输入结构，并且只接受已经展开的基础模块；内置组合模块应先展开为其组成模块：

```json
{
  "design": {
    "nodes": [
      {"id": "trig", "module_type": "三角函数运算器", "parameters": {}},
      {"id": "mixer", "module_type": "混频器", "parameters": {}}
    ],
    "connections": [
      {
        "source": {"node": "trig", "port": "SIN"},
        "destination": {"node": "mixer", "port": "IN_A"}
      }
    ]
  }
}
```

校验会检查模块及参数、信号类型、自连接、输入端口重复占用和实例数量限制；校验通过仍不代表画布已经加载或 FPGA 已经写入。

`validate_parameters` 使用 Qt 模块的直接/间接参数定义，并叠加运行时中更严格的数值限制。对 schema 明确声明的无穷特殊值，请使用 JSON 字符串 `"inf"` 或 `"-inf"`；未在该字段 `special_values` 中声明的拼写会被拒绝。FIR/IIR 设计器的跨字段设计参数和专用方法参数不属于本版校验范围；底层系数字段仍会按原始定点范围校验。例如 FIR 的原始 `taps` 寄存器值只接受 15/31/63，分别代表设计器中的 16/32/64 抽头。

服务还提供项目说明、模块目录和单模块详情等只读资源。实际可用工具及输入结构应以客户端连接后发现的 schema 为准。

## 常见问题

### 首次连接较慢

首次运行会创建 `.venv` 并安装 `requirements-mcp.txt` 中的轻量 MCP 依赖，因此耗时会比后续启动长。依赖安装完成后，启动脚本会使用该文件的摘要避免重复安装。

### 修改依赖后没有生效

正常情况下启动脚本会自动检测 `requirements-mcp.txt` 的变化。如虚拟环境损坏，可关闭 DClocking 和 MCP 客户端后删除项目根目录的 `.venv`，再重新启动。

### 客户端显示 Server disconnected

先确认 Python 版本不少于 3.10，并检查客户端日志。stdio 模式下，服务日志只能写入标准错误；任何写到标准输出的调试文本都可能破坏 MCP 协议通信。

### 如何控制实时画布或 FPGA

首版不支持。实时控制需要在 Qt 主进程与 MCP 进程之间增加受控通信、线程切换、权限确认以及硬件写入结果回读，不能用离线校验结果代替。该能力应作为后续独立阶段开发和验收。

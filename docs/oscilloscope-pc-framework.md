# DClocking 示波器 PC 端框架

## 当前实现边界

本次实现面向 Windows 上位机，同时可在 macOS 开发机运行。示波器作为独立数据工作台接入现有浏览器式标签栏，可从左侧 `∿` 按钮打开、拖出为独立窗口并重新挂回。

控制面与数据面保持分离：

```text
现有模块参数与路由：Qt → Port/UART → FPGA
示波器波形数据：    FPGA → UDP → PC 环形缓存 → Qt 波形画布
```

示波器的网络状态不会改变主界面的串口“设备在线”状态，也不会调用现有模块参数写入逻辑。

当前可验证链路：

```text
四通道模拟器
  → 有界批量数据
  → 四通道环形缓存
  → Min/Max 峰值保持抽取
  → 约 30 FPS 的 Qt 绘图

Windows 标准 UDP socket
  → 后台接收线程
  → Legacy UDP V0 协议适配器
  → 有界数据报队列与批量入环形缓存
  → CH1 临时显示
```

## Windows 启动

在 PowerShell 中进入仓库后执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1
```

脚本会创建本地 `.venv`、首次安装 `requirements.txt` 中的依赖并启动集成 Agent 界面。后续仅在依赖文件摘要变化时重新安装，也可显式使用 `-SkipInstall` 跳过检查。依赖已经加入 Windows/macOS 双平台 CI。

UDP 使用普通 IPv4 socket，不依赖 Npcap，也不需要管理员权限。首次监听端口时，Windows 防火墙可能要求用户确认网络访问范围。默认数据源为“内置仿真”，应用启动时不会自动监听端口。

## Legacy UDP V0 已实现适配

当前 HDL 暂定：

- FPGA IP：`192.168.0.2`
- FPGA MAC：`00:0A:35:01:FE:C0`
- FPGA UDP 端口：`8080`
- PC 必须监听本地 UDP `8080` 才能接收固定目的端口回包
- 请求为 19 字节，大端：`header + command + FPGA MAC + channel mask + sample count`
- 查询命令：`0x00010001`
- 数据命令：`0x00010002`
- 查询应答为 27 字节
- 采样数据报为 1029 字节，其中前 5 字节为应答头和命令，随后为 512 个大端 16 位样本

适配器当前强制采样点数为 512 的整数倍。原因有两个：`eth_cmd.v` 对采样数低字节的读取状态不可达；发送侧又只在完整的 512 点 FIFO 数据可用时发包。前端拒绝不可靠的数值，不会静默取整。

Legacy 模式在界面中固定监听 8080，并只允许 CH1。每批数据一次性写入环形缓存；接收线程退出、响应超时或 PC 队列丢包时，采集会停止并明确标记为失败/不完整，不会无限停留在“运行中”。设备信息应答中的 IP/MAC、有符号格式、有效位数、2 字节容器、单通道、采样率和深度都必须通过边界校验；单次等待还有 30 秒硬上限，故障能力帧不能把界面挂住数小时。

每次采集请求前会原子切换 PC 收包队列，避免请求前已到达的旧数据直接完成新一轮采集。由于 Legacy 包仍没有 acquisition ID，请求发出后延迟到达的上一轮包无法从协议层可靠区分，真实实验仍需新版协议补齐采集编号。

该协议没有采集编号、包序号或 CRC，所以这些保护只能判断 PC 本地队列和超时，不能证明 FPGA 到 PC 的端到端完整性。即使界面收到数据，仍应视为“Legacy 未验证采集”。32 MS/s 连续无间隙采集还需要 FPGA 侧降采样/聚合或新版流协议，当前框架不做虚假吞吐承诺。

## 不能伪装成已完成的硬件能力

仓库中的波形采集 HDL 目前尚未进入正式 `Top.vhdl`，且存在需要 FPGA 负责人修复或确认的接口问题：

1. `oscilloscope.v` 是四路 16 位输入、64 位数据输出，但 Ethernet/DDR 路径目前按 16 位接入，仅能解释为 CH1 临时流。
2. `eth_cmd.v` 默认查询应答宣称 1 通道、8 个有效位、2 字节容器，与四通道 16 位采集核心不一致。
3. UDP 数据包没有采集编号、包序号、总包数、通道掩码、有效末包长度和触发点。普通 UDP socket 因而无法可靠判断 FPGA 侧丢包和乱序。
4. 请求中的 `ch_sel` 尚未接到采集路径。
5. 触发、降采样、采集长度等 512 位参数总线在外层被截断，且没有可由现有 UART `ModuleBase` 使用的模块 ID/寄存器映射。
6. DDR/FIFO 等生成 IP 配置未提交，现有源码仍有实例名、端口名、位宽和状态信号问题。

因此工作台把触发模式、触发类型、触发通道、阈值、降采样比和持续计数显示为“待硬件确认、仅暂存”，不会显示虚假的“已写入 FPGA”。DDR Buffer 地址属于内部实现参数，不向普通用户暴露。

## FPGA 侧回填清单

联调前请硬件负责人提供或确认：

| 类别 | 必须确认的字段 |
| --- | --- |
| 网络 | FPGA IP/MAC、UDP 端口、是否固定 PC 目的端口、最大 MTU |
| 样本 | 通道数、有效位数、容器字节数、有符号、字节序、四通道排列顺序 |
| 采集 | 采样率、最大深度、采集点单位、末包有效点数 |
| 触发 | 模式/type/channel/level/sustain/downsample 的编码、范围和提交时机 |
| 完整性 | protocol version、acquisition ID、packet sequence、packet count、CRC |
| 控制面 | UART 模块 ID、寄存器地址/位宽、读回、启动/停止/完成语义 |

建议下一版 UDP 头至少包含：

```text
magic, protocol_version, message_type,
acquisition_id, packet_sequence, packet_count,
channel_mask, sample_format, valid_frame_count,
sample_rate_hz, trigger_index, payload_crc32
```

这些字段加入后，只需新增协议适配器；接收线程、缓存、绘图和工作台无需重写。

## Windows 实验记录兼容层

实验记录工作台在 Windows 使用独立的 Win32 句柄存储后端：

- 使用 `CreateFileW` 逐级打开并持有不共享写入/删除的目录句柄，禁止目录在校验与访问之间被替换或改造成 junction；
- 每一级都以 `FILE_FLAG_OPEN_REPARSE_POINT` 检查，拒绝 symlink、junction 和其他 reparse point；
- 使用 `ReplaceFileW`（不传其文档明确不支持的 WRITE_THROUGH 标志）的备份条目执行原位更新，并核对文件 ID、大小、时间与 SHA-256；
- 对 `ERROR_UNABLE_TO_MOVE_REPLACEMENT_2` 等部分完成状态单独恢复：优先恢复原路径，同时把本地编辑保留成可见恢复副本，不会继续删除唯一副本；
- 若外部编辑发生在提交边界，自动回滚外部版本，并把本地编辑另存为冲突副本；
- 新文件使用原子 create-if-absent 发布，不会覆盖同名抢先创建的文件；
- 在自动访问前拒绝 UNC、设备命名空间和映射网络盘，仓库仅允许本机磁盘；
- 保留原 macOS descriptor + `renameatx_np` 强化后端，不改变已有行为；其他平台的 path-based portable 后端仅允许测试显式启用，不作为生产默认保存路径。

主窗口还将实验工作台改成延迟导入，所以单个可选工作台出现平台问题时，不会阻断主控制台启动。

Agent 的 API Key 不再写入仓库内的 `config.json`。Windows 使用 Credential Manager，macOS 使用 Keychain（由 `keyring` 调用）；配置文件只保存 endpoint、model 等非秘密字段。系统凭据按规范化 API origin 隔离，切换 DeepSeek/OpenAI 等服务时不会复用上一服务的 key。旧版明文 key 会在首次可用启动时迁移并从 JSON 移除；Windows 若 Credential Manager 不可用或去密后的公开配置写盘失败，则禁用旧明文密钥，而不是把 `chmod` 误当成 ACL。

受管环境临时注入密钥时必须成对设置，例如：

```powershell
$env:DCLOCKING_LLM_API_ENDPOINT = "https://api.deepseek.com/v1"
$env:DCLOCKING_LLM_API_KEY = "<从安全注入系统取得的密钥>"
```

只有 `DCLOCKING_LLM_API_ENDPOINT` 与当前规范化 Endpoint 完全一致时，程序才会采用 `DCLOCKING_LLM_API_KEY`；缺少绑定或服务地址不匹配时会忽略该密钥并提示，防止把一个服务商的 key 发给另一个服务商。历史 Git 提交里出现过的旧 key 必须在服务商后台撤销，代码迁移不能替代密钥轮换。

运行中修改设置已被禁用；保存后通过一个原子配置快照同时切换 endpoint、model 和 key，且统一补齐 `/chat/completions`，避免后台请求读到“新地址 + 旧密钥”的混合状态。

## 验证等级

- 模拟器、协议编解码、缓存回绕、峰值保持、标签页集成与线程生命周期可以在开发机和 CI 自动验证。
- UDP 回环测试验证 PC 接收链路，不代表已完成 FPGA 真实板卡联调。
- Windows 专属测试覆盖 Win32 原子替换边界、同名抢占、junction 与 UNC 拒绝；只有远程 Windows CI 跑通后才能标记为 Windows 实机验证。
- FPGA 数据位宽、通道排列、触发参数写回和丢包检测，只有在 HDL 修复并拿到真实数据抓包后才能标记为硬件已验证。

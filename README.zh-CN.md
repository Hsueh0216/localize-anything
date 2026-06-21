# Localize Anything · 本地化基础设施

<p align="center">
  <strong>面向真实源码项目的智能体原生本地化基础设施。</strong><br>
  <em>大模型可以生成译文。Localize Anything 让本地化真正可交付。</em>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#localize-anything--本地化基础设施">简体中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT">
  <img src="https://github.com/Hsueh0216/localize-anything/actions/workflows/ci.yml/badge.svg" alt="CI">
  <a href="https://github.com/Hsueh0216/localize-anything/releases/tag/v0.2.3"><img src="https://img.shields.io/badge/release-v0.2.3-blue" alt="Release: v0.2.3"></a>
  <img src="https://img.shields.io/badge/QA-deterministic-green" alt="QA: deterministic">
  <img src="https://img.shields.io/badge/apply-staged%20first-blueviolet" alt="Apply: staged first">
</p>

Localize Anything 把模型或人工生成的译文变成安全、可审查、可复现的交付流程。
它负责提取可翻译内容，通过智能体或服务商生成目标语言草稿，以确定性规则验证结构，
将结果安全暂存，并且只在明确审核和 run ID 确认后应用变更。

## 当前状态

**当前发布版：** [v0.2.3 — Android Resource Reliability Fixes](https://github.com/Hsueh0216/localize-anything/releases/tag/v0.2.3)

已验证的工程证据：

- v0.2.1 模式系统基准：通过
- v0.2.3 Android 资源可靠性回归：通过
- AntennaPod DeepSeek 实测：2 个目标语言各 869 段，确定性 QA 问题为 0，两个版本均编译成功

这些结果证明的是流程与结构正确性，并不代表母语级译文质量。

## 为什么需要它

大模型可以生成看似合理的字符串，但真实项目的本地化交付还必须保护占位符与标记、
保留已审核内容、记录证据、暴露冲突，并避免破坏源码项目。

Localize Anything 是源码项目、LLM 或人工译者与最终交付物之间缺失的工程层。
Runtime 负责确定性工作，智能体与服务商负责语义工作。

## Localize Anything 做什么

**提取 → 生成 → QA → 暂存 → 审核 → 应用**

- 从真实项目格式中提取可翻译内容
- 根据运行模式规划哪些内容需要生成、哪些需要保留
- 通过宿主智能体或直接服务商生成草稿，并提供限定范围的上下文
- 用程序检查占位符、标记、转义、键与文件结构
- 在源码项目之外暂存输出，等待审核
- 打包清单、QA 证据、审核状态与应用计划
- 仅在明确确认 run ID 后应用，并在覆盖前备份

<p align="center">
  <img src="docs/assets/workflow-dark.svg" alt="Localize Anything 工作流：从项目 Agent 到备份后应用的 9 个步骤" width="900">
</p>

## 核心保证

| 保证 | 实现方式 |
|------|----------|
| **暂存优先** | 生成文件写入隔离的 staging 目录，而不是源码项目。 |
| **确定性 QA** | 用代码检查占位符一致性、标记完整性、转义、键与格式规则。 |
| **禁止静默覆盖** | 冲突会阻断应用，直到问题得到解决。 |
| **确认后应用** | 应用要求匹配的 `--confirm-run-id`，被替换的文件会先备份。 |
| **源码变更检测** | SHA-256 检查会发现运行期间的意外变化。 |
| **维护模式保留** | 已审核且未变化的译文与仅目标侧键会被保留。 |
| **参考内容隔离** | 盲测不会让已有译文进入面向生成的工件。 |
| **交付可审查** | 清单、QA 结果、签字范围与文件操作始终可检查。 |

完整安全架构见 [安全文档](docs/security.md)。

## 快速开始

### 从源码安装

```bash
git clone https://github.com/Hsueh0216/localize-anything.git
cd localize-anything
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[yaml]"
python -m unittest discover -s tests -v
```

### 运行回归基准

```bash
python benchmarks/v022-android-resource-reliability/run.py
python benchmarks/v022-android-resource-reliability/source_sets.py
python benchmarks/v022-android-resource-reliability/risk_classification.py
python benchmarks/v021-mode-system/run.py
```

### 检查真实项目

```bash
localize-anything inspect /path/to/project
```

## 示例工作流

使用合成草稿，从 Android 源语言文件创建日语维护交付；整个过程不会调用外部模型：

```bash
localize-anything localize-run /path/to/project \
  --source-locale en-US \
  --target-locale ja \
  --source-file app/src/main/res/values/strings.xml \
  --operating-mode existing_locale_maintenance \
  --reference-policy preserve_existing \
  --run-id maintenance-001 \
  --synthetic-draft
```

运行只会生成暂存文件和交付证据。写入项目是独立操作：必须先生成 dry-run 计划，
再明确确认对应的 run ID。

## 当前支持

### 稳定

- Android `strings.xml`：字符串、数组、复数、source set 与语言区域限定符
- JSON 语言文件
- YAML 与 TOML
- CSV、TSV 与 XLSX
- Markdown 与 HTML
- SRT 与 WebVTT
- XLIFF 1.2 与 2.x
- GNU gettext PO/POT

### 实验性

- iOS `.strings` 与 `.stringsdict`
- Xcode `.xcstrings` String Catalog

适配器 ID、保留规则与完整格式边界见 [Adapter Contract](docs/adapters.md)。

## 工程证据

### v0.2.1 模式系统基准

| 模式 | 参考策略 | 结果 |
|------|----------|------|
| `blind_benchmark` | `blind` | 通过——生成工件无已有译文泄漏 |
| `greenfield_localization` | `style_only` | 通过 |
| `existing_locale_maintenance` | `preserve_existing` | 通过——保留 10 段，生成 2 段 |
| `rewrite_or_harmonization` | `tm_assisted` | 通过 |

合成 Android fixture 包含 12 个源语言段和 10 个已有 `zh-CN` 译文。
基准还验证了仅目标侧键保护和源码哈希不变性。运行命令：
`python benchmarks/v021-mode-system/run.py`。

### v0.2.3 Android 资源可靠性

Android 适配器覆盖：

- `string`、`string-array` 与 `plurals`
- 占位符、转义百分号与 Android 转义符
- 支持的内联标记、简单链接、CDATA 与 XML 注释
- 相互独立的 Android source set 与规范的语言区域限定符顺序
- 仅目标侧资源保护与失败时关闭的路由策略
- 带真实结构证据的确定性审核风险元数据

支持结构、已知限制与明确的非目标见
[v0.2.3 Android 支持边界](docs/android-v0.2.3-support.md)。

### AntennaPod DeepSeek 实测

<p align="center">
  <img src="docs/assets/benchmark-antennapod.svg" alt="AntennaPod 英语到日语和韩语 DeepSeek 基准：869 段、0 个 QA 问题、编译成功" width="640">
</p>

| 指标 | 日语（`ja`） | 韩语（`ko`） |
|------|---------------|---------------|
| 源项目 | AntennaPod `develop` 分支 | 同 |
| 段数 | 869 | 869 |
| 批次 | 29 | 29 |
| 模型 | `deepseek-chat` | `deepseek-chat` |
| 确定性 QA | 0 blocking，0 warnings | 0 blocking，0 warnings |
| 编译 | `:app:assembleFreeDebug` ✓ | `:app:assembleFreeDebug` ✓ |

完整流程：extract → batch → DeepSeek API → collect → stage → QA → deliver。

## 核心概念

### 运行模式

| 模式 | 适用场景 | 参考策略 |
|------|----------|----------|
| `greenfield_localization` | 新增语言 | `style_only` |
| `existing_locale_maintenance` | 维护已审核译文 | `preserve_existing` |
| `rewrite_or_harmonization` | 明确重写或统一风格 | `tm_assisted` |
| `blind_benchmark` | 在无译文泄漏条件下评估 | `blind` |

### 项目记忆

Localize Anything 在 `.localize-anything/` 下保存已批准的翻译记忆、会话历史和项目配置。
在维护模式中，源文本哈希未变化的已审核译文会跨运行保留，不会重复翻译或产生无意义改动。

### 审核与交付

```text
审核 Agent → 限定范围签字 → 交付决策 → 应用计划 → 备份后应用
```

人工验收精确到内容段。应用计划会在写入任何源码文件前，列出每个新建、替换、
不变或冲突操作。

<p align="center">
  <img src="docs/assets/architecture-layers.svg" alt="架构分层：协议、Runtime、Agent、适配器、源码与交付" width="640">
</p>

## 它不是什么

Localize Anything 不是：

- prompt 合集
- 通用机器翻译包装器
- APK 或 IPA 重打包工具
- 专业人工审校的替代品
- 会静默改写源码项目的工具
- “LLM 输出无需证据即可投产”的承诺

## 仓库结构

```text
protocol/         可移植 schema 与生命周期规范
runtime/          Python 参考 Runtime
adapters/         适配器清单与入口
benchmarks/       公开基准 fixture 与 runner
tests/            Runtime 单元测试与集成测试
docs/             公开文档
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

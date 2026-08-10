# 跨资产交易晨报｜生产管线

## 当前生产模型

网页 ChatGPT 的 08:00 定时任务仍是生产系统。GitHub 不负责独立定时运行；GitHub 负责保存运行规则、共享数据规则、固定 HTML 母版、渲染/校验工具、研究账本和历史成品。

每日任务唯一入口：

`config/cross_asset/runtime_manifest.yaml`

不得根据 README、旧聊天记忆、`format_baseline.yaml`、`report.yaml` 或历史任务提示词自行推断当前流程。

## 每日任务实际读取

以 `runtime_manifest.yaml.required_config_reads` 为准。跨资产专属规则已集中到：

`config/cross_asset/runtime_bundle.yaml`

共享数据层仍分别读取 `data_contract / sources / routing / quality_rules / instruments / report_calendar`，因为这些规则也服务其他晨报，不应复制进跨资产专属配置。

## HTML 不再自由生成

正式母版：

`templates/cross_asset/cross_asset_v4_2026_08_08.html`

该母版从用户确认正确的 2026-08-08 成品提取固定页面骨架、CSS、JS、导航和三种阅读模式。

模型只能生成：

`report_payload.json`

结构合同：

`config/cross_asset/report_payload.schema.json`

渲染器：

`scripts/cross_asset/render_report.py`

校验器：

`scripts/cross_asset/validate_report.py`

禁止在 renderer 失败后让模型重新手写一份 HTML。这样会重新引入版式漂移。

## 正式执行顺序

1. 读取 `runtime_manifest.yaml`。
2. 读取当前 required configs 并核对 runtime bundle ID。
3. 判定交易日和发布模式。
4. 研究、取数、交叉核验。
5. 生成结构化 payload，只负责内容。
6. 使用固定 template + renderer 生成唯一一次本地 HTML。
7. 用 validator 校验模板 ID、CSS/JS fingerprint、阅读模式、section 顺序、三条市场主线、文件名/title/H1、外部依赖和禁用词。
8. validator 未通过：不得归档错误 HTML，不得声称正式 HTML 完成。
9. validator 通过：同一个本地 HTML 文件同时用于聊天附件和 GitHub 归档。
10. GitHub 归档成功不等于聊天附件成功；计划任务必须生成真实可下载附件才算完整交付。

## 当前运行权威

每日运行权威优先级：

1. `runtime_manifest.yaml`
2. `runtime_bundle.yaml`
3. shared data configs
4. `research_ledger.yaml`
5. template / payload schema / renderer / validator

下列文件暂时保留作历史设计/维护参考，但不参与每日 required reads：

- `config/cross_asset/format_baseline.yaml`
- `config/cross_asset/report.yaml`
- `docs/DATA_PROTOCOL.md`

它们不得覆盖上述运行权威。

## 自动任务管理

系统只允许一个启用中的跨资产 08:00 任务，并仅由《跨资产交易晨报｜每日生产》管理。规则中枢修改 GitHub 后不得重建任务。现有任务只需要保持短提示：先读取 `runtime_manifest.yaml`，再执行当前 pipeline。

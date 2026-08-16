# 统一交易晨报（Unified Morning Brief）

> 独立实验项目。该目录是 `wuxingyuenan5-lgtm/market-brief-data-hub` 中《统一交易晨报》的唯一入口目录。

## 项目标识

- REPORT_NAME: `统一交易晨报`
- PROMPT_VERSION: `unified_morning_experiment_v1`
- PIPELINE_ID: `unified_morning_brief_experiment_v1`
- TIMEZONE: `Asia/Shanghai`
- DEFAULT_REPORT_TIME: `08:00`
- GitHub repository: `wuxingyuenan5-lgtm/market-brief-data-hub`
- Canonical root: `unified_morning/`

## 隔离原则

本目录与以下既有系统完全隔离，后者仅作为只读上游知识：

- `config/cross_asset/**`
- `reports/cross_asset/**`
- `config/domestic/**`
- `reports/domestic/**`

不得因《统一交易晨报》修改原跨资产晨报、国内晨报、收盘晚报的规则、模板、runtime manifest、research ledger 或自动任务。

## 本地读取入口

本地 Dashboard / Agent 优先读取：

1. `unified_morning/current.json` —— 当前版本、最新报告和文件路径索引；
2. `unified_morning/config/production_rules.md` —— 完整生产规则；
3. `unified_morning/config/report_schema.json` —— 结构化 payload 契约；
4. `unified_morning/config/quality_rules.yaml` —— 真实性与完整性门槛；
5. `unified_morning/reports/YYYY/MM/` —— HTML/PDF正式成品归档。

## 生产职责

生产端负责：研究、数据核验、事实层、跨资产传导、三条统一主线、HTML/PDF成品。

本地 A 股 Dashboard（`wuxingyuenan5-lgtm/Astock_study`）定位为**消费端**：读取、展示、历史浏览和下载，不负责重新研究或重写晨报。

## 成品规则

每天正式成品默认同时交付：

- `统一交易晨报_YYYY-MM-DD.html`
- `统一交易晨报_YYYY-MM-DD.pdf`

HTML 与 PDF 必须来自同一份冻结正文 / payload，PDF不得另行改写。

## 当前状态

本目录初始固化于 2026-08-16。当前规则已进入 GitHub；后续每日正式成品按 `unified_morning/reports/YYYY/MM/` 归档。
# market-brief-data-hub

“跨资产交易晨报 V4”与“纯国内交易晨报”共用的数据口径、源路由、质量控制和版本锁定仓库。

## 目标

1. 统一两份晨报的数据字段、时点、单位、状态和缺失值表达。
2. 尽可能复用以下两个公开项目的分层取数与容错方式：
   - `simonlin1212/global-stock-data`
   - `simonlin1212/a-stock-data`
3. 固定上游 commit，避免上游更新后晨报口径无提示变化。
4. 主源失败时切换独立备源；主备均失败时明确报缺，不用旧值或估算值冒充最新值。
5. 把公共配置与两份晨报的独立配置分开维护。

## 目录

```text
config/
  shared/              # 两份晨报共用的数据契约、源清单、路由和质量规则
  cross_asset/         # 跨资产交易晨报专属配置
  domestic/            # 纯国内交易晨报专属配置
docs/                  # 数据协议与运维说明
vendor/                # 上游仓库版本锁定，不存储密钥
scripts/               # 上游版本检查与配置校验
.github/workflows/      # 定期检查上游变化，只提醒，不自动升级
```

## 使用原则

- 每次生成晨报前，先读取：
  1. `vendor/upstreams.lock.yaml`
  2. `config/shared/data_contract.yaml`
  3. `config/shared/sources.yaml`
  4. `config/shared/routing.yaml`
  5. `config/shared/quality_rules.yaml`
  6. 对应晨报的 `report.yaml`
- 关键数据优先采用官方、交易所或监管来源；行情类数据按配置使用多源交叉验证。
- HTTP 200、非空数组不等于数据有效，必须执行交易日、标的、成交量、价格范围、新鲜度和静默失败检查。
- 任何“最新值”必须带市场时点和抓取时点。
- 若无法取得可靠同点数据，统一写：`未取得同一时点可核验数据`。
- 本仓库不保存真实密钥、Cookie、个人邮箱或代理地址。

## 上游版本策略

上游版本固定在 `vendor/upstreams.lock.yaml`。定时工作流只检查是否有新 commit，并创建 Issue 提醒人工评估；不会自动修改锁定版本。

## 数据状态

正式输出使用以下状态：

- `official_verified`：官方或交易所数据已核验
- `cross_source_consistent`：两个独立来源在允许误差内一致
- `single_source_pending`：仅单源，等待复核
- `time_mismatch`：来源时点不同，不适合直接横向比较
- `suspected_stale`：疑似陈旧或定格报价
- `unavailable`：未取得可靠数据

## 安全

仓库目前为公开仓库。真实配置请使用运行环境变量或 GitHub Actions Secrets，不要提交到代码库。`.env.example` 只列变量名和说明。
# operations — 运维能力

## 职责

运行期非功能性能力：出站网络与 Cloudflare 清关、数据备份与恢复、调用日志、内容过滤。

| 文件 | 职责 |
|------|------|
| `services/proxy_service.py` | 代理归一化、运行时档案、FlareSolverr / Cloudflare clearance 获取与测试、连通性测试 |
| `services/backup_service.py` | 打包配置/日志/任务为 tar、openssl 加密、Cloudflare R2 上传与轮转、后台定时线程 |
| `services/log_service.py` | `data/logs.jsonl` 追加与查询、`LoggedCall` 统一调用记录与错误响应 |
| `services/content_filter.py` | 敏感词与 AI 审核前置检查、请求文本提取 |
| `scripts/init_proxy_config.py`、`scripts/privoxy-warp.conf` | WARP 方案下的代理初始化与 Privoxy 配置 |

## 行为规范

- 代理优先级：账号自身代理 > 稳定代理运行时（`proxy_runtime`）> 显式代理 > 旧版全局代理；辅助链路（账号邮箱、CPA）默认不被稳定代理接管。
- `proxy_runtime` 支持 `single_proxy` 等出口模式与 clearance 模式（`flaresolverr` / cookie 注入），可按状态码重置会话。
- 备份目标为 Cloudflare R2（含 account_id、bucket、prefix、轮转保留数、可选加密口令），定时周期由 `interval_minutes` 控制；包含项可逐项开关。
- 所有对外调用应经 `LoggedCall` 记录到日志服务，保持统一的调用审计与错误响应格式。
- 内容过滤在请求进入上游前执行（敏感词 + 可选 AI 审核），命中时直接返回拒绝响应，不消耗账号额度。
- 备份与日志路径都在 `data/` 下，随存储持久化；`config.json` 中相关凭据字段不得写入知识库或版本库。

## 依赖关系

```
api/system.py ──> proxy_service, backup_service, log_service
openai_backend_api ──> proxy_service（出站代理 / clearance）
protocol/* ──> content_filter（前置检查）, log_service（记录）
```

## 接口定义

- 代理：`POST /api/proxy/test`、`GET|POST /api/proxy/runtime`、`POST /api/proxy/clearance/test`。
- 备份：`POST /api/backup/test`、`GET /api/backups`、`POST /api/backups/run`、`POST /api/backups/delete`、`GET /api/backups/detail`、`GET /api/backups/download`。
- 日志：`GET /api/logs`、`POST /api/logs/delete`。
- 存储与图片对象存储：`GET /api/storage/info`、`POST /api/image-storage/test`、`POST /api/image-storage/sync`。

## 测试

`test/test_proxy_service.py`、`test/test_proxy_runtime_api.py`、`test/test_proxy_runtime_config.py`、`test/test_init_proxy_config.py`。

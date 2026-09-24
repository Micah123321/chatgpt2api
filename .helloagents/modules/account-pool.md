# account-pool — 账号池与密钥

## 职责

管理 ChatGPT 账号池的生命周期（导入、刷新、限流标记、失效剔除、并发槽位）与调用方 API Key 的认证授权。

| 文件 | 职责 |
|------|------|
| `services/account_service.py` | 账号 CRUD、额度与限流标记、批量刷新、refresh_token 保活、并发槽位分配 |
| `services/auth_service.py` | API Key 哈希存储、角色（admin/user）、增删改查与 `authenticate` |
| `services/cpa_service.py` | 远端 CLIProxyAPI 文件浏览与 token 导入 |
| `services/sub2api_service.py` | 远端 sub2api 服务器/分组/账号浏览与 OAuth 账号导入 |
| `services/oauth_login_service.py`、`services/openai_oauth.py`、`utils/pkce.py` | ChatGPT OAuth 授权码流程 |

## 行为规范

- Sub2API 每个连接支持 `auto_sync_enabled`（默认关闭）、`auto_sync_time`（HH:MM，默认 03:00），固定北京时间 UTC+8。FastAPI lifespan 启动调度线程，每 30 秒检查一次，到点按已保存 `group_id` 导入全量 OpenAI OAuth 账号。
- 日期和任务在网络请求前持久化，同日不重复；当天错过时间且未执行则补跑一次。手动与自动任务互斥，已有 token 复用账号服务去重，导出按 100 个账号分批。自动执行失败记录 `auto_sync_last_error`，次日再执行；磁盘写入失败不会留下无工作线程的 pending 任务。
- 最近执行时间 `auto_sync_last_run_at` 和错误为只读状态；配置随现有 Sub2API 配置持久化。编辑连接不会把正在运行的任务标为失败。当前调度沿项目现有单进程后台线程方式。

- 账号导入方式：本地 CPA JSON、远程 CPA 服务器、sub2api 服务器、`access_token` 直填；另支持密码重新登录与 OAuth 登录（`README.md` 号池章节、`api/accounts.py`）。
- 刷新策略：默认每 5 分钟刷新账号（`config.json: refresh_account_interval_minute`），刷新过程为异步任务并可通过 progress 接口查询进度。
- 失效处理：上游返回 Token 失效类错误时剔除账号；限流账号按恢复时间定时重试；`auto_remove_invalid_accounts` 默认开启，`auto_remove_rate_limited_accounts` 默认关闭（`config.json`）。
- 图片生成并发受账号维度并发数约束（`config.json: image_account_concurrency`，默认 3），具体槽位分配由 `services/account_service.py` 提供。
- 上游请求失败分类由 `services/openai_backend_api.py` 的异常类型表达，号池据此决定标记、剔除或重试（见 [upstream-api.md](./upstream-api.md)）。
- 账号数据落盘位置随存储后端变化（`data/accounts.json` / `data/accounts.db` / 数据库 / Git 仓库），见 [config-storage.md](./config-storage.md)。

## 依赖关系

```
api/accounts.py ──> account_service, auth_service, cpa_service, sub2api_service, oauth_login_service
account_service ──> services/config.py, services/storage/, services/openai_backend_api.py
auth_service ──> services/storage/
cpa_service / sub2api_service / oauth_login_service ──> curl-cffi, services/config.py
```

## 接口定义（HTTP，鉴权要求见 [api.md](./api.md)）

- `/api/auth/users`：密钥列表与创建；`/api/auth/users/{key_id}`：删除。
- `/api/accounts`：列表、新增、删除；`/api/accounts/refresh`（含 `/progress/{progress_id}`）、`/api/accounts/re-login`、`/api/accounts/export`、`/api/accounts/update`。
- `/api/accounts/oauth/start`、`/api/accounts/oauth/finish`：OAuth 授权码流程。
- `/api/cpa/pools*`：CPA 池管理与文件导入；`/api/sub2api/servers*`：sub2api 服务器、分组、账号与导入。

## 测试

`test/test_account_export.py`、`test/test_account_image_capabilities.py`、`test/test_config.py`。

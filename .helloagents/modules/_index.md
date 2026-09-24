# 模块索引

> 通过此文件快速定位模块文档

## 模块清单

| 模块 | 职责 | 状态 | 文档 |
|------|------|------|------|
| api | FastAPI 应用装配、路由注册、鉴权、错误信封、SPA 兜底 | ✅ | [api.md](./api.md) |
| account-pool | 账号池生命周期、密钥管理、CPA / sub2api / OAuth 导入 | ✅ | [account-pool.md](./account-pool.md) |
| upstream-api | ChatGPT / Codex 上游逆向请求、签名求解、SSE 解析 | ✅ | [upstream-api.md](./upstream-api.md) |
| protocol-compat | OpenAI / Anthropic 兼容协议转换与图片生成编排 | ✅ | [protocol-compat.md](./protocol-compat.md) |
| image-pipeline | 图片异步任务、图库管理、对象存储、PPT/PSD 产物 | ✅ | [image-pipeline.md](./image-pipeline.md) |
| config-storage | 配置中心与 JSON/SQLite/Postgres/Git 存储后端 | ✅ | [config-storage.md](./config-storage.md) |
| operations | 代理运行时、备份、日志、内容过滤 | ✅ | [operations.md](./operations.md) |
| web-panel | Next.js 静态导出管理台 | ✅ | [web-panel.md](./web-panel.md) |
| testing | Python 测试与运维脚本 | 🚧 | [testing.md](./testing.md) |

## 模块依赖关系

```
web/ (Next.js 管理台)
  └── HTTP ──> api/ (路由 + 鉴权)
                 ├── api/ai.py ──> services/protocol/ ──> services/openai_backend_api.py ──> utils/ (pow/sentinel/turnstile/helper)
                 ├── api/accounts.py ──> services/account_service.py ──> services/storage/
                 │                        └──> services/cpa_service.py, services/sub2api_service.py, services/oauth_login_service.py
                 ├── api/image_tasks.py ──> services/image_task_service.py ──> services/protocol/conversation.py
                 └── api/system.py ──> services/{image,proxy,backup,log,auth}_service.py

services/* ──> services/config.py ──> services/storage/
services/openai_backend_api.py ──> services/proxy_service.py (出站代理 / clearance)
```

## 状态说明
- ✅ 稳定
- 🚧 开发中
- 📝 规划中

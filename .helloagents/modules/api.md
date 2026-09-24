# api — HTTP 应用层

## 职责

FastAPI 应用装配与对外 HTTP 契约：创建应用、注册全部路由、统一鉴权、错误信封与前端静态兜底。

| 文件 | 职责 | 关键入口 |
|------|------|---------|
| `api/app.py` | 应用工厂：CORS、异常处理、路由挂载、SPA 兜底 | `create_app()` |
| `api/ai.py` | OpenAI / Anthropic 兼容端点，分发到 `services/protocol` | `create_router()` |
| `api/accounts.py` | 用户密钥、账号 CRUD/刷新/导出、CPA 池、sub2api、OAuth 登录 | `create_router()` |
| `api/image_tasks.py` | 异步图片任务的提交、查询与续轮询 | `create_router()` |
| `api/system.py` | 登录/版本/健康检查、设置、图片管理、日志、代理、备份、存储统计 | `create_router(app_version)` |
| `api/support.py` | Bearer 解析、admin/user 鉴权、脱敏、base_url 解析、号池后台巡检、静态资源解析 | 各 `*_dependency` / `resolve_*` |
| `api/image_inputs.py` | 表单/JSON 图片与 mask 解析（URL、base64、UploadFile），单文件 50MB 上限 | `parse_image_edit_request` |
| `api/errors.py` | 按路径区分 OpenAI / Anthropic 错误响应格式 | 异常处理器 |

## 行为规范

- 启动入口固定为 `main.py` 中的 `create_app()` + `uvicorn.run(app, access_log=False, log_level="info")`（`main.py:3-9`）。
- 鉴权：`Authorization: Bearer <auth-key>`；`config.json` 的 `auth-key` 等价于 admin 身份，其余密钥走 `auth_keys` 存储，区分 admin / user 角色（`api/support.py`、`services/auth_service.py`）。
- 前端静态资源由后端兜底：按 `web_dist` 目录提供文件，未命中路径回落到 SPA 页面（`api/app.py`、`api/support.py`）。
- 错误响应格式随调用路径切换（`/v1/messages` 走 Anthropic 信封，其余走 OpenAI 信封），避免客户端解析失败（`api/errors.py`）。
- 请求体中的图片统一经 `api/image_inputs.py` 解析，避免各端点重复实现 multipart / JSON / URL 三态解析。
- 不得在路由层直接实现上游调用逻辑；业务实现属于 `services/`。

## 依赖关系

```
api/* ──> services/*（业务）
api/app.py ──> api/{ai,accounts,image_tasks,system}.py
api/* ──> api/support.py（鉴权与上下文）
api/* ──> api/errors.py, api/image_inputs.py
```

## 接口定义（路由总览，详见各模块文档）

- AI 兼容：`GET /v1/models`、`POST /v1/images/generations`、`POST /v1/images/edits`、`POST /v1/chat/completions`、`POST /v1/responses`、`POST /v1/messages`、`POST /v1/search`、`POST /v1/ppt/generations`、`POST /v1/psd/generations`、`GET /v1/editable-file-tasks`、`GET /files/{file_path}`。
- 图片任务：`GET /api/image-tasks`、`POST /api/image-tasks/generations`、`POST /api/image-tasks/edits`、`POST /api/image-tasks/{task_id}/resume-poll`。
- 账号与密钥：`/api/auth/users*`、`/api/accounts*`（含 refresh / re-login / export / update）、`/api/accounts/oauth/*`、`/api/cpa/*`、`/api/sub2api/*`。
- 系统：`POST /auth/login`、`GET /version`、`GET /health`、`/api/settings`、`/api/image-models*`、`/api/images*`、`/api/logs*`、`/api/proxy/*`、`/api/backup*`、`/api/storage/info`。

## 测试

`test/test_v1_*.py`、`test/test_image_tasks_api.py`、`test/test_proxy_runtime_api.py` 覆盖该层行为；部分用例需运行中的服务（见 [testing.md](./testing.md)）。

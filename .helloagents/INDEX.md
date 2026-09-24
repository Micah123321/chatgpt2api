# chatgpt2api 知识库

> 本文件是知识库的入口点。由 `~init` 于 2026-09-24 18:14 建立。

## 快速导航

| 需要了解 | 读取文件 |
|---------|---------|
| 项目概况、技术栈、开发约定 | [context.md](context.md) |
| 模块索引与依赖关系 | [modules/_index.md](modules/_index.md) |
| HTTP 应用层与鉴权 | [modules/api.md](modules/api.md) |
| 账号池、密钥与导入集成 | [modules/account-pool.md](modules/account-pool.md) |
| 上游逆向请求与反爬签名 | [modules/upstream-api.md](modules/upstream-api.md) |
| OpenAI / Anthropic 兼容协议 | [modules/protocol-compat.md](modules/protocol-compat.md) |
| 图片任务、图库与可编辑文件 | [modules/image-pipeline.md](modules/image-pipeline.md) |
| 配置中心与存储后端 | [modules/config-storage.md](modules/config-storage.md) |
| 代理、备份、日志、内容过滤 | [modules/operations.md](modules/operations.md) |
| Web 管理台（Next.js） | [modules/web-panel.md](modules/web-panel.md) |
| 测试与运维脚本 | [modules/testing.md](modules/testing.md) |
| 项目变更历史 | [CHANGELOG.md](CHANGELOG.md) |
| 当前待执行的方案 | 暂无，方案目录在首次创建方案时生成 |

## 模块关键词索引

> AI 读取此表即可判断哪些模块与当前需求相关，按需深读。

| 模块 | 关键词 | 摘要 |
|------|--------|------|
| api | FastAPI 工厂, 路由, Bearer 鉴权, CORS, SPA 兜底 | 应用装配、请求鉴权与错误信封，注册全部 HTTP 路由 |
| account-pool | 账号池, refresh_token, CPA, sub2api, OAuth 登录, 并发槽位 | 号池生命周期、批量刷新与三种账号导入链路 |
| upstream-api | openai_backend_api, Sentinel, PoW, Turnstile, SSE, Codex 画图 | 对 ChatGPT / Codex 官网上游接口的逆向调用实现 |
| protocol-compat | /v1/chat/completions, /v1/responses, /v1/messages, images, 缓存 | 兼容协议请求整形、流式响应与图片并发生成编排 |
| image-pipeline | image_task, 图库, 缩略图, 标签, WebDAV, PPT/PSD | 图片异步任务、存储与产物管理 |
| config-storage | config.json, data/, JSON, SQLite, Postgres, Git 后端 | 配置读写归一化与可插拔存储后端 |
| operations | 代理, FlareSolverr, 备份, Cloudflare R2, 日志, 敏感词 | 运行期运维能力：网络、备份、审计与内容审核 |
| web-panel | Next.js, 静态导出, 画图工作台, 设置页, IndexedDB | 自托管管理台前端 |
| testing | unittest, test/, scripts/ | Python 测试与运维脚本入口 |

## 知识库状态

```yaml
kb_version: 1
最后更新: 2026-09-24 18:14
模块数量: 9
待执行方案: 0
```

## 读取指引

```yaml
启动任务:
  1. 读取本文件获取导航
  2. 读取 context.md 获取项目上下文
  3. 检查 plan/ 是否有进行中方案包
任务相关:
  - 涉及特定模块: 读取 modules/{模块名}.md
  - 涉及启动/部署: 读取 README.md、docs/deployment.md
  - 涉及测试: 读取 modules/testing.md
  - 需要历史决策: 搜索 CHANGELOG.md
```

> 本知识库未创建 project.yaml / runbook.yaml / secrets.local.yaml，如需服务器与部署信息请执行 `~ssh`。

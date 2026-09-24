# 项目上下文

## 1. 基本信息

```yaml
名称: chatgpt2api
描述: 将 ChatGPT 官网（含 Codex 画图）的生图、图片编辑与文本/搜索能力逆向封装为 OpenAI / Anthropic 兼容 API，并附带号池管理与在线画图面板的自托管服务
类型: 自托管 Web 服务 + OpenAI/Anthropic 兼容 API 代理
状态: 活跃维护中（VERSION 1.9.3，CHANGELOG 持续更新）
```

> 版权与免责：README.md 顶部声明本项目仅供个人学习、技术研究与技术交流，禁止商业或规模化滥用。

## 2. 技术上下文

```yaml
语言: Python 3.13+（后端）、TypeScript / React 19（前端）
框架: FastAPI + uvicorn（后端）、Next.js 16 静态导出（前端）
包管理器: uv（Python）、bun（web/ 前端）
构建工具: uv sync / next build；Docker 多阶段构建（Dockerfile，目标 app）
```

### 主要依赖
| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi / uvicorn | >=0.136 / >=0.44 | HTTP 服务与 ASGI 运行时 |
| curl-cffi | >=0.15 | 模拟浏览器指纹访问上游与第三方服务 |
| sqlalchemy / psycopg2-binary | >=2.0 / >=2.9 | SQLite 与 PostgreSQL 存储后端 |
| gitpython | >=3.1 | Git 私有仓库存储后端 |
| pillow | >=12.2 | 图片缩略图、压缩与 mask 合成 |
| tiktoken | >=0.12 | token 计数 |
| pybase64 / python-multipart | >=1.4 / >=0.0.26 | 图片 base64 与 multipart 上传解析 |
| httpx | >=0.28（dev） | 测试辅助 |
| next / react / zustand / radix-ui | 见 web/package.json | 管理台前端 |

### 运行方式（证据：README.md、main.py、docker-compose.yml）

```yaml
本地后端: uv sync && uv run main.py（uvicorn 默认 127.0.0.1:8000，入口 main.py:5 create_app()）
本地前端: cd web && bun install && bun run dev
容器: docker compose up -d（容器内 80 端口，宿主映射 3000）
WARP 方案: docker compose -f docker-compose.warp.yml up -d --build
前端产物: next.config.ts 设置 output: 'export'，构建后由后端经 web_dist 静态目录兜底服务
```

## 3. 项目概述

### 核心功能
- OpenAI 兼容图片接口：`/v1/images/generations`、`/v1/images/edits`、`/v1/chat/completions`、`/v1/responses`、`/v1/models`，以及 Anthropic `/v1/messages` 与 `/v1/search`。
- 号池管理：账号导入（本地 CPA JSON、远程 CPA、sub2api、access_token、密码重登、OAuth）、额度与限流刷新、失效账号剔除。
- 在线画图工作台：生成、图片编辑、多图组图编辑、会话历史与浏览器端图片缓存。
- 运维能力：全局代理与稳定代理运行时（WARP / Privoxy / FlareSolverr）、备份到 Cloudflare R2、日志查询、内容过滤、图片对象存储（本地 / WebDAV）。
- 存储后端可切换：JSON（默认）、SQLite、PostgreSQL、Git 私有仓库。

### 项目边界
```yaml
范围内:
  - 对 ChatGPT 官网能力的逆向封装与兼容协议转换
  - 号池、图片、任务、配置、备份的本地自托管运维
范围外:
  - 不提供完整通用 Chat/Responses 代理（仅面向图片、搜索与文本场景的兼容子集）
  - 不提供多租户商业服务与规模化调用能力
```

## 4. 开发约定

### 代码规范
```yaml
命名风格: Python 模块与函数 snake_case；类 PascalCase；前端 TypeScript 组件 PascalCase
文件命名: Python 小写下划线；后端单例在模块底部实例化（如 config = ConfigStore(CONFIG_FILE)）
目录组织: api/ HTTP 层、services/ 业务层、services/protocol/ 协议转换、services/storage/ 存储后端、utils/ 通用工具、web/ 前端、test/ 测试
注释与文档: 模块顶部 docstring 说明职责；面向用户文档在 README.md 与 docs/
```

### 错误处理
```yaml
错误信封: 按请求路径区分 OpenAI / Anthropic 格式（api/errors.py）
日志: services/log_service.py 统一记录 LoggedCall，写入 data/logs.jsonl；日志级别由 config.json 的 log_levels 控制
上游异常: services/openai_backend_api.py 定义专用异常类型（账号异常、限流、token 失效等），供号池标记与剔除
```

### 测试要求
```yaml
测试框架: Python unittest（test/ 目录，36 个文件）
测试入口: python -m unittest test.test_xxx 或 python test/test_xxx.py（多数文件含 __main__ 入口）
外部依赖: 部分用例通过 test/utils.py 访问运行中的服务 http://127.0.0.1:8000，属集成型用例
前端测试: web/test/ 下的 .cjs 脚本
覆盖率要求: 未在仓库中声明
```

### Git 规范
```yaml
分支策略: 主干 main（当前分支）
提交格式: Conventional Commits 英文前缀，如 fix: / feat:（见最近提交记录）
版本号: VERSION 文件 + CHANGELOG.md 双写
```

## 5. 当前约束（源自历史决策）

> 项目此前未使用 HelloAGENTS 知识库，以下约束由本次初始化从代码核实得出，尚无方案包编号。

| 约束 | 原因 | 决策来源 |
|------|------|---------|
| 必须配置 auth-key 才能启动，可用 CHATGPT2API_AUTH_KEY 覆盖 | 缺失时服务启动即抛错（services/config.py） | 初始知识库识别 |
| 所有 AI 接口要求 `Authorization: Bearer <auth-key>` | README.md API 章节 | 初始知识库识别 |
| 运行时数据统一写入 `data/` 目录 | services/config.py 启动时创建 | 初始知识库识别 |
| 前端采用静态导出并由后端 web_dist 兜底服务 | web/next.config.ts、api/app.py | 初始知识库识别 |
| 图片生成 `n` 取值限制 1-4，默认模型 gpt-image-2 | README.md、config.json default_image_model | 初始知识库识别 |
| 存储后端由 STORAGE_BACKEND 决定（json/sqlite/postgres/git） | services/storage/factory.py | 初始知识库识别 |
| config.json 与 .env、data/ 不纳入版本库 | .gitignore | 初始知识库识别 |

## 6. 已知技术债务

| 债务描述 | 优先级 | 来源 | 建议处理时机 |
|---------|--------|------|-------------|
| pyproject.toml 缺少有效 description，web/package.json 仍为模板名 next-starter | P2 | 本次初始化核实 | 下次触碰打包配置时 |
| test/ 混合 unittest 与需要真实服务/账号的手工脚本，无统一测试命令与 CI 测试流水线（CI 仅构建 Docker 镜像） | P1 | .github/workflows/docker-publish.yml、test/utils.py | 需要回归保障时 |
| config.json 含示例默认值（如代理、备份凭据字段为空），部署前需人工核对 | P1 | config.json、docs/deployment.md | 部署前 |
| docs/feature-status.en.md 为英文，与中文文档并存 | P2 | docs/ | 文档整理时 |

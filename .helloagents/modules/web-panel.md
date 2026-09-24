# web-panel — 管理台前端

## 职责

自托管管理台：号池管理、在线画图工作台、图库、日志与设置页。构建产物为静态导出，由后端 `web_dist` 兜底服务。

| 路径 | 职责 |
|------|------|
| `web/src/app/accounts` | 号池管理页（导入、刷新、导出、编辑） |
| `web/src/app/image` | 在线画图工作台（生成、图片编辑、多图组图、会话历史） |
| `web/src/app/image-manager` | 图库管理页 |
| `web/src/app/logs` | 日志查询页 |
| `web/src/app/settings` | 设置页（配置、代理、备份、模型等） |
| `web/src/app/debug` | 调试面板 |
| `web/src/app/login` | 登录页 |
| `web/src/lib/api.ts`、`request.ts` | 接口封装与请求基座 |
| `web/src/lib/image-cache.ts` | IndexedDB 图片 Blob 缓存（内存 + 持久层，合并并发请求） |
| `web/src/lib/auth-session.ts`、`use-auth-guard.ts` | 会话与路由鉴权 |
| `web/src/lib/release.ts` | 版本信息 |
| `web/test/*.cjs` | 前端回归脚本（图片缓存、遮罩渲染等） |

## 行为规范

- 构建方式：`next build`（`output: 'export'`），产物 `web/out` 在 Dockerfile 中被复制为容器内 `/app/web_dist`；不得引入依赖服务端运行时的特性（SSR、动态 API 路由、server actions）。
- 请求统一经 `web/src/lib/request.ts`，携带 Bearer 凭证并复用统一错误处理。
- 图片展示优先命中内存与 IndexedDB 缓存，未命中才请求服务器；删除结果 / 会话 / 历史时同步清理对应缓存（CHANGELOG 1.8.0–1.9.0）。
- 页面与接口默认值必须与后端配置保持一致（同一份持久化配置），避免界面显示与实际生效配置不一致。
- 交互约定见 `PRODUCT.md`：配置状态需可见、草稿与已保存状态需区分、校验提示靠近字段、保持信息密度与无障碍（WCAG 2.1 AA、键盘可达、状态不只靠颜色）。
- 本地开发：`cd web && bun install && bun run dev`；后端需同时运行。

## 依赖关系

```
web/src/app/* ──> web/src/lib/api.ts ──> web/src/lib/request.ts ──> 后端 HTTP (api/)
web/src/lib/image-cache.ts ──> IndexedDB（浏览器）
```

## 接口定义

消费后端 `/v1/*` 与 `/api/*` 全部管理接口；前端不直接访问上游 ChatGPT 服务。

# upstream-api — 上游逆向请求层

## 职责

直接对接 ChatGPT / Codex 官网接口：反爬签名求解、会话与 SSE 通信、图片上传生成与轮询、可编辑文件导出。是全部 AI 能力的真实执行层。

| 文件 | 职责 |
|------|------|
| `services/openai_backend_api.py` | 上游请求主实现（约 2.9k 行）：requirements(PoW) 获取、conversation SSE、图片上传/生成/轮询、Codex 画图、文件导出；定义上游异常类型 |
| `utils/pow.py` | Proof-of-Work 计算 |
| `utils/sentinel.py` | ChatGPT Sentinel 挑战求解 |
| `utils/turnstile.py` | Turnstile / 挑战处理 |
| `utils/helper.py` | SSE 事件解析（`iter_sse_payloads`）、响应校验、SSE 流封装、图片落盘 |
| `services/proxy_service.py` | 出站代理与 Cloudflare clearance（上游请求的必经依赖） |

## 行为规范

- 上游调用统一经 `curl-cffi` 发送以模拟浏览器指纹；禁止改用 requests / httpx 直接请求官网接口，否则签名与指纹不匹配。
- 反爬链路：先取 requirements 并求解 PoW / Sentinel / Turnstile，再发起 conversation 与图片请求；签名逻辑集中在 `utils/`，不得散落到业务层。
- 流式解析统一走 `utils/helper.py` 的 SSE 解析函数，保持对上游事件格式变化的单点适配。
- Codex 画图链路使用别名 `codex-gpt-image-2`，仅 Plus / Team / Pro 订阅可用，与官网 `gpt-image-2` 额度相互独立（`README.md`）。
- 上游错误必须转换为 `services/openai_backend_api.py` 内的异常类型，由调用方决定账号剔除、重试或对外错误码；不得在协议层直接抛原始网络异常。
- 请求需遵守统一截止时间约束，避免上游异常等待（CHANGELOG 1.8.0 记录了对图片、文本、搜索与 PPT 请求截止时间的统一处理）。
- 代理优先级：账号自身配置代理 > 稳定代理运行时 > 显式代理 > 旧版全局代理（`README.md`）。

## 依赖关系

```
services/protocol/* ──> openai_backend_api ──> utils/{pow,sentinel,turnstile,helper}
openai_backend_api ──> proxy_service（代理与 clearance）
openai_backend_api ──> config（base_url、超时、模型等）
```

## 接口定义（公共调用面）

- `OpenAIBackendAPI`：账号绑定后的上游会话对象，供 `services/protocol/` 调用完成文本、搜索与图片请求。
- 异常类型：账号异常 / 限流 / token 失效 / 请求失败等，供号池与协议层分支处理。

## 已知风险

- 该层实现依赖对官网私有接口的逆向，上游协议变更会直接导致功能失效；`docs/upstream-sse-conversation.md` 记录了 SSE 会话协议细节。

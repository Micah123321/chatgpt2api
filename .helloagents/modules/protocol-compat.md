# protocol-compat — 兼容协议转换

## 职责

把 OpenAI / Anthropic 兼容请求整形为上游调用，并把上游结果（含流式）转换为客户端期望的响应格式；负责图片生成的并发编排与缓存。

| 文件 | 端点 |
|------|------|
| `services/protocol/openai_v1_image_generations.py` | `POST /v1/images/generations` |
| `services/protocol/openai_v1_image_edit.py` | `POST /v1/images/edits` |
| `services/protocol/openai_v1_chat_complete.py` | `POST /v1/chat/completions` |
| `services/protocol/openai_v1_response.py` | `POST /v1/responses` |
| `services/protocol/anthropic_v1_messages.py` | `POST /v1/messages` |
| `services/protocol/openai_search.py` | `POST /v1/search` |
| `services/protocol/openai_v1_models.py` | `GET /v1/models` |
| `services/protocol/conversation.py` | 会话编排：消息归一化、token 计数、SSE 解析、文本/图片流式生成、图片并发池与去重 |
| `services/protocol/chat_completion_cache.py` | 文本 chat 结果 TTL 缓存与 in-flight 去重 |
| `services/protocol/web_search_tool.py` | 内置 web search 工具调用与结果整理 |
| `services/protocol/error_response.py` | 协议错误信封构造 |

## 行为规范

- `gpt-image-2.5` 为公开别名，上游请求统一映射到 `gpt-image-2.5-flare`；兼容旧模型目录缓存，前端和 `/v1/models` 均可列出该别名。直接使用 flare / sunburst 的路由保持原样。

- 每个端点模块暴露统一 `handle(body)` 风格入口，由 `api/ai.py` 分发；新增兼容端点应沿用该模式。
- 模型能力以 `/v1/models` 返回值与 `config.json: default_image_model` 为准，不硬编码模型名到业务分支。
- 图片生成数量 `n` 限制 1–4（`README.md`）；多图可选并行执行（`config.json: image_parallel_generation`，默认开启），并发上限来自账号并发配置。
- 流式响应必须支持超时与硬上限中断，防止上游长时间无响应占满连接（CHANGELOG 1.8.0）。
- 文本 chat 缓存由 `chat_completion_cache` 配置控制（TTL、条目上限、in-flight 去重、流式缓存、消息归一化等）。
- 搜索意图在文本请求中由 `tools`（web_search 系列）或 `web_search_options` 触发，转交 `web_search_tool` 执行。
- PPT / PSD 生成走可编辑文件任务链路（见 [image-pipeline.md](./image-pipeline.md)），不在协议层直接拼接产物。

## 依赖关系

```
api/ai.py ──> protocol/{各端点}.handle
protocol/* ──> conversation ──> openai_backend_api
protocol/* ──> chat_completion_cache, web_search_tool, image_service
```

## 测试

`test/test_v1_images_generations.py`、`test/test_v1_images_edits*.py`、`test/test_v1_chat_completions.py`、`test/test_v1_responses.py`、`test/test_v1_messages.py`、`test/test_v1_models.py`、`test/test_chat_completion_cache.py`、`test/test_gpt_search.py`、`test/test_request_deadlines.py`。

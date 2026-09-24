# image-pipeline — 图片任务与产物

## 职责

图片从提交到落盘、展示与清理的完整链路，以及 PPT/PSD 可编辑文件的异步生成与下载。

| 文件 | 职责 |
|------|------|
| `services/image_task_service.py` | 基于 `client_task_id` 的幂等任务持久化、后台线程执行、断点恢复与清理 |
| `services/image_service.py` | 本地图片列举/删除/打包下载/缩略图/存储统计/压缩与定期清理调度 |
| `services/editable_file_task_service.py` | PPT/PSD 生成任务与产物下载（产物根目录 `EDITABLE_FILE_ROOT`） |
| `services/image_storage_service.py` | 本地 / WebDAV 双模对象存储、索引与同步 |
| `services/image_tags_service.py` | 图片标签持久化 |
| `services/image_model_service.py` | 图片模型目录缓存与刷新（供 `/v1/models` 与设置页使用） |
| `api/image_tasks.py`、`api/image_inputs.py` | 异步任务 HTTP 接口与图片入参解析 |

## 行为规范

- 异步任务以 `client_task_id` 做幂等键，重复提交不得产生重复生成。
- 生成完成后写入 `data/` 下图片目录，保留期由 `config.json: image_retention_days`（默认 15 天）控制，清理由后台调度线程执行。
- 轮询参数：`image_poll_timeout_secs`（默认 120）、`image_poll_interval_secs`（默认 10）、`image_poll_initial_wait_secs`（默认 10）；超时后客户端可调 `resume-poll` 继续等待。
- 磁盘保护：剩余空间低于 `image_min_free_mb`（默认 500MB）时不应继续写入新图片。
- 对象存储可选开启（`image_storage.enabled`，模式 `local` / WebDAV），开启后图片索引与远端同步由 `image_storage_service` 负责；`public_base_url` 决定对外图片地址。
- 缩略图、打包下载与压缩统一经 `image_service`，避免各端点重复实现 Pillow 逻辑。
- Web 端图片缓存（IndexedDB）属前端职责，见 [web-panel.md](./web-panel.md)。

## 依赖关系

```
api/image_tasks.py ──> image_task_service ──> protocol/conversation ──> openai_backend_api
image_task_service / image_service ──> config, log_service
image_storage_service ──> curl-cffi（WebDAV）, config
editable_file_task_service ──> openai_backend_api
```

## 接口定义

- `GET /api/image-tasks?ids=`、`POST /api/image-tasks/generations`、`POST /api/image-tasks/edits`、`POST /api/image-tasks/{task_id}/resume-poll`。
- 图库：`GET /api/images`、`GET /images/{path}`、`GET /image-thumbnails/{path}`、`POST /api/images/delete`、`POST /api/images/download`、`GET /api/images/download/{path}`、`GET|POST /api/images/tags`、`DELETE /api/images/tags/{tag}`、`GET /api/images/storage`、`POST /api/images/storage/compress`、`POST /api/images/storage/cleanup-to-target`。
- 可编辑文件：`POST /v1/ppt/generations`、`POST /v1/psd/generations`、`GET /v1/editable-file-tasks`、`GET /files/{file_path}`。

## 测试

`test/test_image_task_service.py`、`test/test_image_tasks_api.py`、`test/test_image_storage_service.py`、`test/test_image_mask_composite.py`、`test/test_image_base_url_api.py`、`test/test_multi_image_results.py`、`test/test_gpt_ppt.py`、`test/test_gpt_psd.py`、`test/test_image_tokens.py`、`test/test_image_output_tokens.py`。

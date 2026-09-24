# config-storage — 配置与存储

## 职责

集中管理 `config.json` 的读写、默认值与归一化，并为账号、密钥等数据提供可切换的持久化后端。

| 文件 | 职责 |
|------|------|
| `services/config.py` | `ConfigStore`：配置读写、默认值、`data/` 路径、启动校验、存储后端单例 |
| `services/storage/base.py` | `StorageBackend` 抽象接口 |
| `services/storage/json_storage.py` | 本地 JSON 文件后端（默认） |
| `services/storage/database_storage.py` | SQLite / PostgreSQL 后端（SQLAlchemy） |
| `services/storage/git_storage.py` | Git 私有仓库后端 |
| `services/storage/factory.py` | 按 `STORAGE_BACKEND` 选择实现 |
| `scripts/migrate_storage.py`、`scripts/test_storage.py` | 存储迁移与自测 |

## 行为规范

- 配置文件固定为项目根 `config.json`；`auth-key` 必填，缺失时启动即报错，可被环境变量 `CHATGPT2API_AUTH_KEY` 覆盖。
- 读取配置时 `auth-key` 不随普通 `get()` 返回，避免密钥经接口泄露。
- 运行时数据统一写入 `<项目根>/data/`，启动时自动创建；已知文件包括 `data/accounts.json`、`data/auth_keys.json`、`data/accounts.db`、`data/logs.jsonl`、`data/git_cache/` 与图片/任务目录。
- 存储后端由环境变量 `STORAGE_BACKEND` 选择：`json`（默认）、`sqlite`、`postgres`（需 `DATABASE_URL`）、`git`（需 `GIT_REPO_URL`、`GIT_TOKEN`，可选 `GIT_BRANCH`、`GIT_FILE_PATH`）。
- 切换存储后端需先确认数据迁移路径，禁止直接修改后端类型而丢失既有账号数据；迁移使用 `scripts/migrate_storage.py`。
- 新增配置项必须提供默认值并在归一化逻辑中处理缺省，保证旧 `config.json` 可平滑升级。
- `config.json`、`.env`、`data/` 均在 `.gitignore` 中，不得提交；`config.json` 内含代理、备份、AI 审核等可含凭据的字段。

## 依赖关系

```
services/config.py ──> services/storage/factory.py ──> {json,database,git}_storage
几乎全部 services/* ──> services/config.py
api/support.py ──> services/config.py（base_url、auth-key 校验）
```

## 接口定义

- 配置读写：`ConfigStore` 的读取、设置与归一化方法，配置单例在 `services/config.py` 模块底部创建。
- 存储抽象：`StorageBackend` 的读取 / 写入 / 删除接口，由三个实现类分别提供。
- HTTP 面：`GET|POST /api/settings`、`GET /api/storage/info`、`GET|POST /api/image-models`。

## 测试

`test/test_config.py`、`test/test_default_image_model.py`、`test/test_image_model_service.py`、`test/test_init_proxy_config.py`、`test/test_proxy_runtime_config.py`。

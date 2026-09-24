# testing — 测试与脚本

## 职责

Python 测试套件（`test/`，36 个文件）、前端回归脚本（`web/test/`）与运维脚本（`scripts/`）。

| 范围 | 说明 |
|------|------|
| `test/test_v1_*.py` | 兼容端点为单位的协议与接口测试 |
| `test/test_image*.py`、`test/test_multi_image_results.py` | 图片任务、mask 合成、token 与存储 |
| `test/test_account*.py`、`test/test_config.py` | 账号导出、账号图片能力、配置 |
| `test/test_proxy*.py`、`test/test_init_proxy_config.py` | 代理服务与运行时配置 |
| `test/utils.py` | 测试辅助：读取 `config.json` 的 auth-key、向 `http://127.0.0.1:8000` 发请求（属集成型依赖） |
| `scripts/migrate_storage.py`、`scripts/test_storage.py` | 存储迁移与自测 |
| `scripts/verify_oauth_refresh.py`、`scripts/test_outlook_token_mailbox.py` | OAuth 刷新与邮箱链路验证 |
| `web/test/*.cjs` | 前端缓存、遮罩等回归脚本 |

## 行为规范

- 测试框架为 `unittest`，多数文件带 `if __name__ == "__main__": unittest.main()` 入口，可单文件执行，也可 `python -m unittest test.test_xxx`。
- 涉及真实上游 / 账号的用例属于手工或集成验证，不应作为默认回归前置条件；依赖运行中服务的用例需先启动后端并确保 `config.json` 存在。
- 仓库当前无 CI 测试流水线，`.github/workflows/docker-publish.yml` 只在打 `v*` 标签或手动触发时构建并推送多架构镜像。
- 新增功能应补充对应 `test/test_*.py`；纯前端行为补充 `web/test/*.cjs`。

## 依赖关系

```
test/* ──> 被测模块（services/, api/）, test/utils.py
scripts/* ──> services/*（直接调用）
```

## 接口定义（常用命令）

```bash
# 单文件测试
python test/test_v1_images_generations.py
# 模块化执行
python -m unittest test.test_v1_chat_completions
# 存储自测
python scripts/test_storage.py
```

## 待定项

- 未在仓库中核实到统一的“全量测试”命令或覆盖率配置，使用前请先确认目标用例是否需要真实账号与网络。

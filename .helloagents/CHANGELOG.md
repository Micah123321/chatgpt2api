# 变更日志

## [Unreleased]

- **[版本检测]**: 检测 VERSION、CHANGELOG 与 GitHub 更新链接统一指向 Micah123321/chatgpt2api；本次发布版本 1.10.0。

- **[发布]**: Compose 默认镜像切换为 `ghcr.io/micah123321/chatgpt2api:latest`（可通过 `CHATGPT2API_IMAGE` 覆盖），Actions 主分支手动构建支持发布 latest。

- **[协议转换]**: 新增 `gpt-image-2.5` → `gpt-image-2.5-flare` 别名，兼容旧缓存并同步前端列表；28 项相关回归通过。
- **[账号池]**: Sub2API 新增按连接设置的每日自动导入（北京时间）、持久化防重复、任务互斥、批次导出、失败状态及设置界面；17 项后端回归、前端构建与浏览器模拟接口交互验证通过。

### 快速修改
- **【知识库】**: 执行 `~init` 初始化项目知识库，建立 INDEX.md、context.md、CHANGELOG.md 与 9 个模块文档
  - 类型: 快速修改（无方案包）
  - 文件: .helloagents/INDEX.md, .helloagents/context.md, .helloagents/CHANGELOG.md, .helloagents/modules/
  - 说明: 未修改任何源码；结论均来自本次对仓库代码、配置与文档的只读核实

## 初始状态 - 2026-09-24

- 项目基线版本 VERSION 1.9.3，当前分支 main。

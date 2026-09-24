# ChatGPT2API

把 ChatGPT 的画图能力接到自己的工作流里。

你可以直接打开网页画图、上传参考图改图，也可以通过 OpenAI 兼容接口接入 Cherry Studio、New API 或自己的脚本。账号导入、额度查看、生成记录和代理设置，都放在同一个后台里。

项目主要围绕生图和图片编辑维护，也提供文本、网页搜索、Anthropic Messages 兼容接口，以及可编辑 PPT / PSD 生成。上游用的是 ChatGPT 网页接口，能否成功调用仍取决于账号权限、额度和网络状态。

[快速开始](#快速开始) · [模型怎么选](#模型怎么选) · [API 示例](#api) · [部署与升级](docs/deployment.md) · [更新日志](CHANGELOG.md)

## 最近更新

当前版本 **1.10.0**。最近几版主要补了这些日常用得上的东西：

- **Image 2.5 可以直接选了。** `gpt-image-2.5` 是项目提供的别名，生成和编辑请求会转到 `gpt-image-2.5-flare`；也可以明确选择 `flare` 或 `sunburst`。
- **Sub2API 可以每天自动导入。** 每个连接单独设置时间和分组，按北京时间运行；不用一直开着浏览器。
- **模型列表可以从上游刷新。** 设置页能查看来源和更新时间，拉取失败会保留已有目录。默认模型需要点保存才生效。
- **改图可以直接涂范围。** 支持画布标注、透明 mask 和草图参考；标注预览用浅灰遮罩与双轮廓，重复涂抹不会越涂越黑。
- **看过的图会留在浏览器缓存里。** 缩略图、灯箱、下载和引用共用缓存，回看历史时能少下载几次。
- **镜像和更新入口已对齐当前仓库。** 默认镜像为 `ghcr.io/micah123321/chatgpt2api:latest`，提供 amd64 / arm64 架构。

逐版改动见 [CHANGELOG](CHANGELOG.md)。

> [!WARNING]
> 免责声明：
>
> 本项目涉及对 ChatGPT 官网文本生成、图片生成与图片编辑等相关接口的逆向研究，仅供个人学习、技术研究与非商业性技术交流使用。
>
> - 严禁将本项目用于任何商业用途、盈利性使用、批量操作、自动化滥用或规模化调用。
> - 严禁将本项目用于破坏市场秩序、恶意竞争、套利倒卖、二次售卖相关服务，以及任何违反 OpenAI 服务条款或当地法律法规的行为。
> - 严禁将本项目用于生成、传播或协助生成违法、暴力、色情、未成年人相关内容，或用于诈骗、欺诈、骚扰等非法或不当用途。
> - 使用者应自行承担全部风险，包括但不限于账号被限制、临时封禁或永久封禁以及因违规使用等所导致的法律责任。
> - 使用本项目即视为你已充分理解并同意本免责声明全部内容；如因滥用、违规或违法使用造成任何后果，均由使用者自行承担。
> - 本项目基于对 ChatGPT 官网相关能力的逆向研究实现，存在账号受限、临时封禁或永久封禁的风险。请勿使用你自己的重要账号、常用账号或高价值账号进行测试。

## 快速开始

### 用 Docker 跑起来

先安装 Docker 和 Docker Compose v2，然后拉取仓库：

```bash
git clone https://github.com/Micah123321/chatgpt2api.git
cd chatgpt2api
```

**先配密钥，再启动。** 在项目根目录创建 `config.json`；如果已经有这个文件，只修改需要的字段，保留原来的配置。最小内容如下，把占位文字换成你自己设置的长随机密钥：

```json
{
  "auth-key": "请替换成你自己的长随机密钥"
}
```

也可以在 [docker-compose.yml](docker-compose.yml) 的 `environment` 中设置 `CHATGPT2API_AUTH_KEY`，它会覆盖文件里的值。Compose 挂载了 `config.json`，所以即使用环境变量，也要先创建这个文件（可写入 `{}`），避免 Docker 把它当目录创建。

```bash
docker compose up -d
```

- 管理面板：`http://localhost:3000`
- API Base URL：`http://localhost:3000/v1`
- 运行数据：`./data`
- 默认镜像：`ghcr.io/micah123321/chatgpt2api:latest`，可用 `CHATGPT2API_IMAGE` 替换。

### 出第一张图

1. 打开面板，用刚设置的 `auth-key` 登录。
2. 到账号页导入账号，刷新一次，确认账号状态和可用额度。
3. 打开画图页，选一个模型，输入提示词，先生成一张试试。
4. 要改图时，上传参考图，或直接对已有结果点「引用」「编辑」。需要只改局部，就在画布上标出范围。

如果要接第三方客户端，填上面的 API Base URL 和自己的密钥即可。模型名建议先从下方清单选，不要照抄旧版截图里的列表。

### 更新已有部署

先备份 `config.json`、`.env`（如有）和 `data/`，再在 Compose 所在目录执行：

```bash
docker compose pull
docker compose up -d
```

这组命令适用于上面的普通镜像部署。WARP 方案和从源码构建的更新方式见 [部署与升级指南](docs/deployment.md)。

## 模型怎么选

当前内置生图目录如下。有已缓存目录时，实际列表以设置页显示为准；刷新模型目录会合并内置项与上游发现的模型。

| 模型名 | 在本项目中的用途 |
| --- | --- |
| `gpt-image-2.5` | 便于客户端使用的别名，实际路由到 `gpt-image-2.5-flare` |
| `gpt-image-2.5-flare` | 直接使用 flare 型号 |
| `gpt-image-2.5-sunburst` | 直接使用 sunburst 型号 |
| `gpt-image-2` | 保留的兼容名称，也是初始默认模型；上游路由为 `gpt-5-5-thinking` |
| `gpt-5-5-thinking` | 通过主线模型的图片生成链路调用 |
| `gpt-5-5` | 通过主线模型的图片生成链路调用 |
| `gpt-5-3` | 通过主线模型的图片生成链路调用 |

**Codex 画图走单独的账号来源。** 号池有对应的 Plus / Team / Pro Codex 账号时，`GET /v1/models` 会补充 `codex-gpt-image-2`，以及匹配账号类型的 `plus-codex-gpt-image-2`、`team-codex-gpt-image-2`、`pro-codex-gpt-image-2`。当前这条链路的图片工具仍使用 `gpt-image-2`。

设置页可以刷新生图目录、选择全局默认模型并保存；画图页还可以为单个对话选择模型，后续生成沿用该对话的选择。Image 2.5 在页面上有 `xhigh` / `max` 质量选项，最终质量与尺寸仍以返回结果为准。

模型出现在列表里，表示项目会识别这个名字；不代表每个账号都能用。遇到失败时，先看日志里的权限、额度或网络错误。

## 平时可以怎么用

### 画图和改图

网页工作台支持文生图、上传参考图、多图编辑、局部标注和草图输入。结果可以继续引用、编辑或下载，会话历史保存在浏览器本地。生成过程中能看进度，部分超时任务可以继续等待，不必马上重提一次。

图片结果会缓存在浏览器的 IndexedDB 中，缩略图、灯箱和下载共用这份缓存；删除结果或清空历史时，也会清理对应缓存。图库页提供服务端图片管理，两者用途不同：浏览器历史方便接着画，服务端图库方便管理已保存的图片。

### 管理账号

账号页可以查看邮箱、类型、额度和恢复时间，也能搜索、筛选、刷新、导出和清理账号。支持本地 CPA JSON、远程 CPA、Sub2API 和 access_token 导入，并提供 OAuth 登录与异常账号重新登录入口。

生成时会从号池选择可用账号。失效 token 的清理、限流账号的处理、刷新后是否重新登录，都可以按需要在设置里调整。

### Sub2API 每日自动导入

在「设置 → Sub2API → 添加/编辑连接」里开启「每日自动导入」，选好时间和分组后保存。默认关闭，预填时间为 **03:00，北京时间（UTC+8）**。

- 每个连接独立设置，分组留空时导入全部 OpenAI OAuth 账号。
- 重复 token 会跳过并刷新账号状态，连接卡片会显示执行结果和失败信息。
- 后台每 30 秒检查一次，浏览器可以关掉，但服务要保持运行。
- 每天最多自动执行一次，同日重启不会重复执行；错过时间且当天还没执行时，会补跑一次。
- 同一个连接已有导入任务时，自动任务会等它结束。失败后可以手动导入，也可以等次日任务。

### 接口与其他能力

除了图片接口，还提供 Chat Completions、Responses、Anthropic Messages、网页搜索以及可编辑 PPT / PSD 生成。兼容范围以当前实现为准，尤其是工具调用和流式输出，接入前建议用自己的请求样例试一下。

| 接口 | 用途 |
| --- | --- |
| `GET /v1/models` | 查看对外暴露的模型 |
| `POST /v1/images/generations` | 文生图 |
| `POST /v1/images/edits` | 参考图编辑、mask 编辑 |
| `POST /v1/chat/completions` | 文本、搜索和图片场景 |
| `POST /v1/responses` | Responses 兼容请求 |
| `POST /v1/messages` | Anthropic Messages 兼容请求 |
| `POST /v1/search` | 网页搜索 |
| `POST /v1/ppt/generations` | 创建可编辑 PPT 生成任务 |
| `POST /v1/psd/generations` | 创建可编辑 PSD 生成任务 |

其他功能状态见 [功能清单](docs/feature-status.en.md)。

## 网络、存储与本地开发

### 经常遇到 Cloudflare 拦截

仓库带了一套 WARP + Privoxy + FlareSolverr 组合。确实需要这条代理链路时，再按下面的方式启动；它不是所有网络问题的通用解法。

```bash
cp .env.example .env
# 编辑 .env，确认密钥、端口和代理参数
docker compose -f docker-compose.warp.yml up -d --build
```

它会启动 `warp-proxy`（SOCKS5 出口）、`privoxy`（转成 HTTP 代理）、`flaresolverr`（刷新 clearance）、`init-config`（写入代理运行时默认配置）和主服务。

默认只接管上游 OpenAI / ChatGPT 请求，邮箱和 CPA 等辅助请求不会被强制接管。代理优先级为：账号代理 → 稳定代理运行时 → 显式代理 → 旧版全局代理。设置页可以保存配置、测试代理和测试 clearance。

### 存储怎么选

一般自托管先用默认 JSON 即可。需要换后端时，通过 `STORAGE_BACKEND` 配置：

| 值 | 存储方式 | 额外配置 |
| --- | --- | --- |
| `json` | 本地 JSON，默认 | 无 |
| `sqlite` | 本地 SQLite | 可配置 `DATABASE_URL` |
| `postgres` | PostgreSQL | `DATABASE_URL` |
| `git` | Git 私有仓库 | `GIT_REPO_URL`、`GIT_TOKEN` |

例如 PostgreSQL：

```yaml
environment:
  - STORAGE_BACKEND=postgres
  - DATABASE_URL=postgresql://user:password@host:5432/dbname
```

切换存储前请先备份并安排数据迁移，修改环境变量不会自动搬走旧数据。图片另有本地 / WebDAV 存储选项，备份功能支持 Cloudflare R2。

### 本地开发

需要 Python 3.13+、uv 和 Bun。先克隆仓库，并按快速开始配置好 `config.json`。在项目根目录启动后端：

```bash
uv sync
uv run main.py
```

再开一个终端，从项目根目录启动前端：

```bash
cd web
bun install
bun run dev
```

后端默认在 `http://127.0.0.1:8000`，前端地址以终端输出为准（通常是 `http://localhost:3000`）。开发模式的前端请求固定指向 `127.0.0.1:8000`，请先在同一台机器的浏览器里访问。

## 常见问题

**页面里没看到新模型？**

先确认已经更新到新镜像，再到设置页刷新生图目录。刷新失败会保留已有列表，页面会显示来源和更新时间。选完全局默认模型后记得保存。

**用了 `gpt-image-2.5`，为什么日志里是 flare？**

这是当前版本的别名映射。想用 sunburst，就明确传 `gpt-image-2.5-sunburst`。

**账号已经导入，为什么还是出不了图？**

先刷新账号状态，再看日志里的错误。账号额度、订阅权限、token 是否过期，以及服务器能否访问上游，都会影响结果；换个模型名不会解决所有问题。

**换浏览器后，之前的对话怎么没了？**

画图会话历史和图片缓存保存在当前浏览器，不会自动跨设备同步。服务端保存的图片可以到图库页查看，重要结果建议及时下载。



## 效果展示

<table width="100%">
  <tr>
    <td width="50%"><img src="https://i.ibb.co/Jj8nfwwP/image.png" alt="image" border="0"></td>
    <td width="50%"><img src="https://i.ibb.co/pqf235v/image-edit.png" alt="image edit" border="0"></td>
  </tr>
  <tr>
    <td width="50%"><img src="https://i.ibb.co/tPcqtVfd/chery-studio.png" alt="chery studio" border="0"></td>
    <td width="50%"><img src="https://i.ibb.co/PsT9YHBV/account-pool.png" alt="account pool" border="0"></td>
  </tr>
  <tr>
    <td width="50%"><img src="https://i.ibb.co/rRWLG08q/new-api.png" alt="new api" border="0"></td>
  </tr>
</table>

## API

下面的例子按 Docker 默认端口 `3000` 编写；本地开发请换成 `8000`。把 `<auth-key>` 换成自己的密钥。

OpenAI 兼容接口使用以下请求头：

```http
Authorization: Bearer <auth-key>
```

<details>
<summary><code>GET /v1/models</code></summary>
<br>

返回上游模型目录与本项目补充的模型，同时带上 `default_image_model`。完整返回值可能包含文本模型；生图目录可在设置页查看，或通过 `GET /api/image-models` 获取。

```bash
curl http://localhost:3000/v1/models \
  -H "Authorization: Bearer <auth-key>"
```

<details>
<summary>说明</summary>
<br>

| 字段   | 说明                                                                                                         |
|:-----|:-----------------------------------------------------------------------------------------------------------|
| 返回模型 | 随上游目录、已缓存生图目录和账号类型变化，见上方「模型怎么选」 |
| 接入场景 | 可接入 Cherry Studio、New API 等上游或客户端                                                                          |

<br>
</details>
</details>

<details>
<summary><code>POST /v1/images/generations</code></summary>
<br>

OpenAI 兼容图片生成接口，用于文生图。

```bash
curl http://localhost:3000/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <auth-key>" \
  -d '{
    "model": "gpt-image-2.5",
    "prompt": "一只漂浮在太空里的猫",
    "n": 1,
    "response_format": "b64_json"
  }'
```

<details>
<summary>字段说明</summary>
<br>

| 字段                | 说明                                                 |
|:------------------|:---------------------------------------------------|
| `model`           | 生图模型，例如 `gpt-image-2.5`；省略时使用设置页保存的默认模型 |
| `prompt`          | 图片生成提示词                                            |
| `n`               | 生成数量，当前后端限制为 `1-4`                                 |
| `size`            | 请求尺寸，例如 `1024x1024`；最终尺寸以返回图片为准 |
| `quality`         | 默认 `auto`；画图页面为 Image 2.5 提供 `xhigh`、`max` 选项 |
| `response_format` | 返回格式，默认 `b64_json`，也可使用 `url` |

<br>
</details>
</details>

<details>
<summary><code>POST /v1/images/edits</code></summary>
<br>

OpenAI 兼容图片编辑接口，可上传图片文件，也可按官方 JSON 格式传入图片链接并生成编辑结果。

```bash
curl http://localhost:3000/v1/images/edits \
  -H "Authorization: Bearer <auth-key>" \
  -F "model=gpt-image-2.5" \
  -F "prompt=把这张图改成赛博朋克夜景风格" \
  -F "n=1" \
  -F "image=@./input.png"
```

也可以直接传图片 URL：

```bash
curl http://localhost:3000/v1/images/edits \
  -H "Authorization: Bearer <auth-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2.5",
    "prompt": "把这张图改成赛博朋克夜景风格",
    "images": [
      {"image_url": "https://example.com/input.png"}
    ]
  }'
```

<details>
<summary>字段说明</summary>
<br>

| 字段          | 说明                                            |
|:------------|:----------------------------------------------|
| `model`     | 生图模型，例如 `gpt-image-2.5`、`gpt-image-2.5-sunburst` |
| `prompt`    | 图片编辑提示词                                       |
| `n`         | 生成数量，当前后端限制为 `1-4`                            |
| `image`     | 需要编辑的图片文件，使用 multipart/form-data 上传           |
| `images`    | JSON 图片引用数组，支持 `{"image_url": "https://..."}` |
| `image_url` | 表单模式下也可直接传图片链接，支持重复字段传多张图                     |
| `mask` | 可选编辑遮罩；透明区域表示需要重绘的范围 |

<br>
</details>
</details>

<details>
<summary><code>POST /v1/chat/completions</code></summary>
<br>

面向文本、网页搜索与图片场景的 Chat Completions 兼容接口，不是完整通用聊天代理。

```bash
curl http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <auth-key>" \
  -d '{
    "model": "gpt-image-2.5",
    "messages": [
      {
        "role": "user",
        "content": "生成一张雨夜东京街头的赛博朋克猫"
      }
    ],
    "n": 1
  }'
```

<details>
<summary>字段说明</summary>
<br>

| 字段                   | 说明                                                                           |
|:---------------------|:-----------------------------------------------------------------------------|
| `model`              | 文本、搜索或图片模型；搜索模型会触发网页搜索兼容逻辑                                                   |
| `messages`           | 消息数组，支持文本、搜索和图片请求内容                                                          |
| `n`                  | 图片生成数量，按当前实现解析为图片数量                                                          |
| `stream`             | 文本、搜索和图片场景均支持，仍在测试                                                           |
| `tools`              | 文本场景支持 `web_search` / `web_search_preview` / `web_search_preview_2025_03_11` |
| `web_search_options` | 传入时会触发网页搜索兼容逻辑                                                               |

<br>
</details>
</details>

<details>
<summary><code>POST /v1/responses</code></summary>
<br>

面向文本、网页搜索和图片生成工具调用的 Responses API 兼容接口，不是完整通用 Responses API 代理。

```bash
curl http://localhost:3000/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <auth-key>" \
  -d '{
    "model": "gpt-image-2.5",
    "input": "生成一张未来感城市天际线图片",
    "tools": [
      {
        "type": "image_generation"
      }
    ]
  }'
```

<details>
<summary>字段说明</summary>
<br>

| 字段       | 说明                                                                                      |
|:---------|:----------------------------------------------------------------------------------------|
| `model`  | 响应中会回显该模型字段，搜索和图片生成会走对应兼容逻辑                                                             |
| `input`  | 输入内容；搜索使用最后一条用户文本，图片生成需能解析出提示词                                                          |
| `tools`  | 支持 `image_generation`、`web_search`、`web_search_preview`、`web_search_preview_2025_03_11` |
| `stream` | 已实现，但仍在测试                                                                               |

<br>
</details>
</details>

## 社区支持

交流社区：[LinuxDO](https://linux.do)

## Contributors

感谢所有为本项目做出贡献的开发者：

<a href="https://github.com/basketikun/chatgpt2api/graphs/contributors">
  <img alt="Contributors" src="https://contrib.rocks/image?repo=basketikun/chatgpt2api" />
</a>

## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=basketikun/chatgpt2api&type=date&legend=top-left)](https://www.star-history.com/?repos=basketikun%2Fchatgpt2api&type=date&legend=top-left)

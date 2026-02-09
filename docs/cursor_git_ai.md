# 单文件夹多项目git与ai管理
_Exported on 2/9/2026 at 16:46:28 GMT+8 from Cursor (2.4.32)_

---

**User**

/create-skill  Help me create this skill for Cursor: 如何把两个项目放在一个文件夹，然后后续分别git，注意方便我后续用AI管理 @c:\Users\leclee\.cursor\projects\d-programs-JetBrains-pyproject-lecfaka\agent-transcripts\380d5e2e-c4ed-47c2-b384-0b63c295b2ca.txt 

---

**Cursor**

我先读取技能创建指南和相关的 agent transcript 来理解上下文。

transcript 文件很大，让我搜索关键内容来理解上下文。

让我继续搜索 transcript 中关于项目结构和 git 管理的关键讨论。

让我读取 transcript 中关于独立仓库和项目结构设置的关键部分。

让我检查一下项目当前的结构，确认两个项目的布局。

现在我有了完整的上下文理解。让我创建这个技能。根据 transcript，你的场景是：

- `lecfaka`（主项目，前端+后端）和 `lecfaka-store`（插件商店/授权服务器）两个独立 Git 仓库
- 两个项目放在同一父目录下作为兄弟目录
- 需要用 Cursor AI 方便地管理两个项目

让我先确认技能存储位置。

好的，创建个人级别的技能。

技能文件已创建。让我验证一下内容和格式。

技能已创建完成，共 223 行，符合 500 行限制。让我总结一下创建的内容。

---

技能 **`multi-repo-workspace`** 已创建在 `C:\Users\leclee\.cursor\skills\multi-repo-workspace\SKILL.md`。

### 技能覆盖的内容

| 部分 | 说明 |
|------|------|
| **目录结构** | 父目录下放多个独立 Git 仓库项目的标准布局 |
| **方案一：Multi-Root Workspace** | 推荐方案，通过 `.code-workspace` 文件让 Cursor 同时打开多个项目，AI 可跨项目搜索和编辑 |
| **方案二：直接打开父目录** | 轻量方案，快速浏览用 |
| **Git 操作规范** | AI 执行 git 命令时必须指定 `working_directory`，避免在父目录操作，分别管理远程仓库 |
| **AI 管理最佳实践** | 5 条核心规范：明确路径前缀、分批提交、API 边界文档化、共享配置提取、Docker Compose 协同 |
| **快速设置清单** | 新建多项目工作区的 7 步检查清单 |

### 触发场景

当你提到以下关键词时，AI 会自动应用这个技能：
- 设置多项目工作区
- 两个项目放一个文件夹
- 配置 multi-root workspace
- AI 需要跨多个 Git 仓库工作

这个技能基于你之前 `lecfaka` + `lecfaka-store` 的实际场景提炼而来，适用于任何类似的多仓库协作场景。

---

**User**

如何创建.code-workspace，如何通过 .code-workspace 文件让 Cursor 同时打开多个项目，AI 可跨项目搜索和编辑，详细解释一下，之前我只会放在父目录中，然后打开

---

**Cursor**

## `.code-workspace` 文件详解

### 它是什么

`.code-workspace` 是 VS Code / Cursor 的**多根工作区**配置文件。本质上就是一个 JSON 文件，告诉 Cursor："请同时打开这几个文件夹，把它们当作一个整体工作区"。

### 和"直接打开父目录"的区别

| | 直接打开父目录 | `.code-workspace` |
|---|---|---|
| **Git 面板** | 可能混乱，不知道该跟踪谁 | 每个项目独立的 Source Control 分栏 |
| **终端默认目录** | 父目录（需要手动 cd） | 可以选择在哪个项目根目录打开终端 |
| **AI 上下文** | 看到所有文件但不知道项目边界 | 知道每个项目的根目录在哪 |
| **搜索** | 搜索整个父目录（可能包含无关文件） | 只搜索你指定的项目文件夹 |
| **项目设置** | 只能有一套 settings | 可以给每个项目单独配置 settings |

---

### 创建步骤

以你的项目为例，`lecfaka` 和 `lecfaka-store` 都在 `d:\programs\JetBrains\pyproject\` 下。

**第一步**：在父目录下创建文件，文件名随意但后缀必须是 `.code-workspace`：

```
d:\programs\JetBrains\pyproject\lecfaka-workspace.code-workspace
```

**第二步**：写入以下内容：

```json
{
  "folders": [
    {
      "path": "lecfaka",
      "name": "LecFaka (主项目)"
    },
    {
      "path": "lecfaka-store",
      "name": "LecFaka Store (插件商店)"
    }
  ],
  "settings": {
    "files.exclude": {
      "**/node_modules": true,
      "**/__pycache__": true,
      "**/.venv": true,
      "**/*.pyc": true
    }
  }
}
```

各字段解释：

- `folders` — 要包含的项目列表
  - `path` — 相对于 `.code-workspace` 文件的路径（也可以用绝对路径）
  - `name` — 在 Cursor 侧边栏里显示的名字（可选，不写就用文件夹名）
- `settings` — 工作区级别的设置，会覆盖全局设置

**第三步**：在 Cursor 中打开它，有三种方式：

```
方式 1：菜单
File -> Open Workspace from File -> 选择 .code-workspace 文件

方式 2：命令行
cursor "d:\programs\JetBrains\pyproject\lecfaka-workspace.code-workspace"

方式 3：双击
直接在文件管理器中双击 .code-workspace 文件
```

---

### 打开后你会看到

Cursor 的文件浏览器侧边栏会变成这样：

```
EXPLORER
├── LECFAKA (主项目)          ← 第一个根目录
│   ├── backend/
│   ├── frontend/
│   ├── docker-compose.yml
│   └── ...
└── LECFAKA STORE (插件商店)   ← 第二个根目录
    ├── app/
    ├── Dockerfile
    └── ...
```

**Git Source Control 面板**也会分开显示：

```
SOURCE CONTROL
├── LecFaka (主项目)           ← 独立的 git 状态
│   ├── M backend/app/config.py
│   └── ...
└── LecFaka Store (插件商店)    ← 独立的 git 状态
    └── (clean)
```

**终端**：新建终端时，Cursor 会问你在哪个项目根目录打开。

---

### AI 跨项目工作的效果

打开 workspace 后，AI 可以：

1. **同时看到两个项目的文件** — 你说"改一下 store 的授权验证 API"，它能直接找到 `lecfaka-store/app/api/v1/license.py`
2. **跨项目搜索** — 搜索 `STORE_URL` 会同时在两个项目中找到引用
3. **跨项目修改** — 比如改了 store 的 API 响应格式，AI 知道要同步改 lecfaka 里的 `license_client.py`
4. **Git 操作自动区分** — AI 用 Shell 工具时，会根据文件路径自动在正确的项目目录下执行 git 命令

---

要我现在帮你创建这个 `.code-workspace` 文件吗？

---

**User**

太棒了，请创建，这样的话，是不是我后续还能创建不同的.code-workspace,，自由组合不同项目，跨项目协作

---

**Cursor**

没错，完全正确！你可以创建任意多个 `.code-workspace` 文件，自由组合不同项目。比如：

- `lecfaka-workspace.code-workspace` — lecfaka + lecfaka-store
- `all-projects.code-workspace` — 所有项目
- `frontend-only.code-workspace` — 只放前端相关的项目

每个 workspace 就像一个"项目组合快捷方式"，随时切换。

现在来创建你的 workspace 文件。

两个项目都确认存在，创建 workspace 文件。

已创建 `d:\programs\JetBrains\pyproject\lecfaka-workspace.code-workspace`。

### 打开方式

在 Cursor 中：**File → Open Workspace from File** → 选择这个文件。或者直接在文件管理器里双击它。

打开后你会看到侧边栏出现两个独立的项目根目录，Git 面板也会分别显示各自的状态，后续 AI 在这个 workspace 里就能同时操作两个项目了。

你说得对，以后任何新项目只要放到 `pyproject` 目录下，再创建一个新的 `.code-workspace` 文件把它加进去就行，自由组合，互不影响。


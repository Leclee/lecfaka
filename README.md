# LecFaka - 现代化自动发卡系统

基于 **FastAPI** + **React** 构建的现代化自动发卡系统，支持 Docker 一键部署，域名自动检测。

## 特性

- **高性能后端** - FastAPI 异步框架 + SQLAlchemy 2.0 异步 ORM
- **现代化前端** - React 18 + TypeScript + Ant Design 5
- **多支付方式** - 易支付、USDT/TRC20、余额支付（插件化管理）
- **安全可靠** - JWT 认证、密码加密、支付签名验证
- **响应式设计** - 完美支持 PC 和移动端
- **域名自动检测** - 无需手动配置域名，Nginx 反代自动识别
- **插件系统** - 支付方式、通知等均可通过插件扩展
- **完整电商功能** - 商品管理、卡密管理、订单系统、优惠券
- **分销系统** - 推广返佣
- **分站系统** - 支持商户开店

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 18 / Redis 7 |
| 前端 | React 18 / TypeScript / Vite 5 / Ant Design 5 / Tailwind CSS |
| 部署 | Docker Compose / Nginx / Certbot |

## 项目结构

```
lecfaka/
├── backend/                # 后端
│   ├── app/
│   │   ├── api/v1/        # API 路由
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   ├── plugins/       # 插件系统
│   │   ├── payments/      # 支付模块
│   │   ├── utils/         # 工具函数
│   │   └── core/          # 核心模块
│   └── requirements.txt
├── frontend/               # 前端
│   ├── src/
│   │   ├── api/           # API 封装
│   │   ├── pages/         # 页面组件
│   │   └── store/         # 状态管理
│   └── package.json
├── docker/                 # Docker 配置
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docs/                   # 文档
│   └── Docker部署指南.md
├── docker-compose.yml      # Docker Compose（dev/prod 统一）
└── .env.example            # 环境变量模板
```

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Leclee/lecfaka.git
cd lecfaka

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改 SECRET_KEY、JWT_SECRET_KEY、DB_PASSWORD

# 3. 一键启动
docker compose --profile prod up -d

# 4. 访问
# 前端: http://你的IP
# 默认管理员: admin / admin123
```

> 详细部署说明请参阅 [Docker 部署指南](docs/Docker部署指南.md)

### 方式二：本地开发

```bash
# 1. 启动基础设施（PostgreSQL + Redis + Adminer）
docker compose --profile dev up -d

# 2. 启动后端
cd backend
cp ../.env.example .env   # 或使用已有的 .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 6666

# 3. 启动前端
cd frontend
npm install
npm run dev
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:8888 |
| 后端 API | http://localhost:6666 |
| API 文档 | http://localhost:6666/docs |
| Adminer | http://localhost:8080 |
| 默认管理员 | admin / admin123 |

## 环境变量

项目只需一个 `.env` 文件（从 `.env.example` 复制），核心配置项：

| 变量 | 说明 | 必须修改 |
|------|------|---------|
| `SECRET_KEY` | 应用加密密钥（加密 session 等） | 是 |
| `JWT_SECRET_KEY` | JWT 签名密钥（用户登录 token） | 是 |
| `DB_PASSWORD` | 数据库密码 | 是 |
| `ADMIN_USERNAME` | 默认管理员用户名 | 否（默认 admin） |
| `ADMIN_PASSWORD` | 默认管理员密码 | 建议修改 |

> 支付配置、邮件配置、短信配置等均在**管理后台网页中设置**，无需写入环境变量。

## 域名配置

系统采用**自动检测方案**，从 Nginx 转发的 HTTP 请求头自动获取域名和协议。

- **换域名**：只需修改 Nginx 的 `server_name` + DNS 解析，后端零修改
- **加 HTTPS**：Nginx 配置 SSL 证书即可，后端通过 `X-Forwarded-Proto` 自动感知

支持 Nginx + Certbot、Cloudflare 等方式，详见 [部署指南](docs/Docker部署指南.md#域名与-https-配置)。

## 许可证

MIT License

## 致谢

- [acg-faka](https://github.com/lizhipay/acg-faka) - 原始 PHP 版本参考
- [FastAPI](https://fastapi.tiangolo.com/)
- [Ant Design](https://ant.design/)

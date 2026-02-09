# LecFaka Docker 部署指南

## 架构说明

LecFaka 包含两个**完全独立**的项目：

| 项目 | 部署方 | 说明 |
|------|--------|------|
| **lecfaka**（主项目） | 每个用户自行部署 | 发卡网本体，含前端+后端+DB+Redis |
| **lecfaka-store**（插件商店） | 官方统一部署 | 插件分发、授权验证、版本更新检查 |

所有用户的发卡网通过 `STORE_URL`（默认 `https://store.lecfaka.com`）远程连接官方插件商店。两个项目各自拥有独立的数据库、Docker 配置和部署流程，互不干扰。

```
用户 A 的服务器                    用户 B 的服务器
┌─────────────────┐               ┌─────────────────┐
│ lecfaka         │               │ lecfaka         │
│ ├─ Frontend :80 │               │ ├─ Frontend :80 │
│ ├─ Backend      │               │ ├─ Backend      │
│ ├─ PostgreSQL   │               │ ├─ PostgreSQL   │
│ └─ Redis        │               │ └─ Redis        │
└────────┬────────┘               └────────┬────────┘
         │ HTTPS                           │ HTTPS
         └──────────────┬──────────────────┘
                        ▼
              官方插件商店服务器
              ┌─────────────────┐
              │ lecfaka-store   │
              │ ├─ Store API    │
              │ │   :8001       │
              │ └─ PostgreSQL   │
              └─────────────────┘
```

---

## 一、主项目部署（用户操作）

### 环境要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Ubuntu 20.04+ / Debian 11+ / CentOS 8+ |
| Docker | 20.10+ |
| Docker Compose | v2.0+ |
| 内存 | 1GB+ |
| 磁盘 | 10GB+ |

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker && sudo systemctl start docker
docker --version && docker compose version
```

### 1. 获取代码

```bash
cd /opt
git clone <主项目仓库地址> lecfaka
cd lecfaka
```

### 2. 配置环境变量

```bash
cp .env.example .env
nano .env
```

**必须修改：**

```bash
SECRET_KEY=随机字符串       # openssl rand -hex 32
JWT_SECRET_KEY=另一个随机串  # openssl rand -hex 32
DB_PASSWORD=数据库强密码
ADMIN_PASSWORD=管理员密码
```

### 3. 一键启动

```bash
docker compose --profile prod up -d
```

首次启动自动完成：创建数据库表、创建管理员账号、加载内置插件。

### 4. 验证

```bash
docker compose --profile prod ps      # 全部 healthy
docker compose logs backend -f        # 查看后端日志
curl http://localhost/health           # 测试
```

访问 `http://服务器IP`，管理后台默认账号 `admin` / `你设置的密码`。

### 服务端口

| 服务 | 内部端口 | 对外端口 | 说明 |
|------|---------|---------|------|
| PostgreSQL 18 | 5432 | 127.0.0.1:5432 | 仅本机可访问 |
| Redis 7 | 6379 | 127.0.0.1:6379 | 仅本机可访问 |
| Backend | 8000 | 不暴露 | 由 Nginx 反代 |
| Frontend | 80 | **80** | 唯一对外端口 |

> 生产环境仅暴露 80 端口（或自定义 `HTTP_PORT`），DB 和 Redis 绑定 `127.0.0.1` 不对外。

### 环境变量完整列表

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `SECRET_KEY` | **是** | - | 应用加密密钥 |
| `JWT_SECRET_KEY` | **是** | - | JWT 签名密钥 |
| `DB_USER` | 否 | `lecfaka` | 数据库用户名 |
| `DB_PASSWORD` | **是** | `lecfaka123` | 数据库密码 |
| `DB_NAME` | 否 | `lecfaka` | 数据库名 |
| `ADMIN_USERNAME` | 否 | `admin` | 管理员用户名 |
| `ADMIN_PASSWORD` | **是** | `admin123` | 管理员密码 |
| `ADMIN_EMAIL` | 否 | `admin@lecfaka.com` | 管理员邮箱 |
| `HTTP_PORT` | 否 | `80` | 前端 HTTP 端口 |
| `STORE_URL` | 否 | `https://store.lecfaka.com` | 插件商店地址 |
| `SITE_URL` | 否 | 自动检测 | 站点地址 |
| `CALLBACK_URL` | 否 | 自动检测 | 支付回调地址 |

> 支付方式（易支付、USDT 等）在**管理后台网页**中配置，不需要写入 `.env`。

---

## 二、插件商店部署（官方操作）

### 1. 获取代码

```bash
cd /opt
git clone <商店仓库地址> lecfaka-store
cd lecfaka-store
```

### 2. 配置

```bash
cp .env.example .env
nano .env
```

```bash
SECRET_KEY=商店密钥
DB_PASSWORD=商店数据库密码
```

### 3. 启动

```bash
docker compose up -d
```

### 4. 验证

```bash
docker compose ps
curl http://localhost:8001/health
```

### 商店服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL 18 | 127.0.0.1:5433 | 商店数据库（5433 避免与其他 PG 冲突） |
| Store API | 8001 | 需要通过 Nginx 反代并配置 HTTPS |

### 商店 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/store/plugins` | GET | 插件列表 |
| `/api/v1/store/plugins/{id}` | GET | 插件详情 |
| `/api/v1/store/check-updates` | POST | 批量检查更新（插件+主程序版本） |
| `/api/v1/store/download/{id}` | GET | 下载插件 zip |
| `/api/v1/license/verify` | POST | 验证授权码 |
| `/api/v1/license/bind` | POST | 绑定域名 |
| `/health` | GET | 健康检查 |

### 商店域名配置

```bash
# Nginx 反代（宿主机）
sudo nano /etc/nginx/sites-available/store
```

```nginx
server {
    listen 80;
    server_name store.lecfaka.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/store /etc/nginx/sites-enabled/
sudo certbot --nginx -d store.lecfaka.com
```

---

## 三、域名与 HTTPS（主项目）

### 方案一：Nginx + Certbot（推荐）

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

如果宿主机 Nginx 和 Docker 前端都用 80 端口，需要把 Docker 端口改掉：

```bash
# .env
HTTP_PORT=8888
```

```nginx
# /etc/nginx/sites-available/lecfaka
server {
    listen 80;
    server_name shop.example.com;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        client_max_body_size 50M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/lecfaka /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d shop.example.com
```

> **域名自动检测**：后端自动从 `X-Forwarded-Host` 识别域名，换域名只改 Nginx + DNS，后端零配置。

### 方案二：Cloudflare（最简单）

1. Cloudflare 添加 A 记录 → 服务器 IP
2. 开启代理（橙色云朵）
3. SSL 设为 "Full"
4. Docker 直接暴露 80 端口即可

---

## 四、数据备份与恢复

### 备份

```bash
cd /opt/lecfaka
docker compose exec -T db pg_dump -U lecfaka lecfaka > backup_$(date +%Y%m%d).sql
```

### 恢复

```bash
docker compose exec -T db psql -U lecfaka lecfaka < backup_20260209.sql
```

### 定时备份

```bash
# crontab -e
0 3 * * * cd /opt/lecfaka && docker compose exec -T db pg_dump -U lecfaka lecfaka > /opt/backups/lecfaka_$(date +\%Y\%m\%d).sql
```

---

## 五、更新升级

### 版本检查

管理后台会自动检查插件和主程序更新（通过 `GET /api/v1/admin/plugins/check-updates`）。

### 更新主项目

```bash
cd /opt/lecfaka
git pull
docker compose --profile prod build
docker compose --profile prod up -d
docker compose logs backend -f
```

### 仅更新后端 / 前端

```bash
docker compose build backend && docker compose up -d backend
docker compose build frontend && docker compose up -d frontend
```

---

## 六、常见问题

### 端口被占用

```bash
sudo lsof -i :80
# 解决：在 .env 设置 HTTP_PORT=8080
```

### 数据库连接失败

```bash
docker compose ps db && docker compose logs db
# 首次部署如果数据卷损坏：
docker compose down && docker volume rm lecfaka_postgres_data
docker compose --profile prod up -d
```

### 插件商店连不上

```bash
# 检查网络连通性
curl -s https://store.lecfaka.com/health
# 如果不通，检查：DNS 解析、防火墙、STORE_URL 配置
```

### USDT 支付不工作

```bash
docker compose exec redis redis-cli ping                           # Redis 正常？
docker compose exec backend curl -s https://apilist.tronscanapi.com # 能访问 TronScan？
docker compose logs backend -f 2>&1 | grep epusdt                  # 查看监听日志
```

### 支付回调不生效

- 域名已解析到服务器
- Nginx 配置了 `X-Forwarded-Proto` + `X-Forwarded-Host` 转发
- 防火墙开放 80/443

### 完全清除重新部署

```bash
# ⚠️ 会删除所有数据！请先备份
docker compose --profile prod down -v
docker compose --profile prod up -d --build
```

### 开发环境

```bash
docker compose --profile dev up -d          # DB + Redis + Adminer
cd backend && python -m app.main            # 后端 :6666
cd frontend && npm run dev                  # 前端 :5173
# Adminer: http://localhost:8080
```

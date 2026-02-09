# LecFaka Docker 部署指南

## 目录

- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [详细配置](#详细配置)
- [域名与 HTTPS 配置](#域名与-https-配置)
- [数据备份与恢复](#数据备份与恢复)
- [更新升级](#更新升级)
- [常见问题](#常见问题)

---

## 环境要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Ubuntu 20.04+ / CentOS 8+ / Debian 11+ |
| Docker | 20.10+ |
| Docker Compose | v2.0+ |
| 内存 | 1GB+ |
| 磁盘 | 10GB+ |

### 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 验证安装
docker --version
docker compose version
```

---

## 快速部署

### 1. 获取项目代码

```bash
# 克隆项目（或上传项目文件到服务器）
cd /opt
git clone <你的仓库地址> lecfaka
cd lecfaka
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置（必须修改！）
nano .env
```

`.env` 文件必须修改的配置项：

```bash
# 数据库密码（务必修改为强密码）
DB_PASSWORD=你的数据库密码

# 安全密钥（务必修改为随机字符串）
SECRET_KEY=一个随机的长字符串
JWT_SECRET_KEY=另一个随机的长字符串

# 关闭调试模式
DEBUG=false

# 易支付配置（如需使用）
EPAY_URL=https://你的易支付地址
EPAY_PID=你的商户ID
EPAY_KEY=你的商户密钥
```

> **注意**：`SITE_URL` 和 `CALLBACK_URL` 已改为自动检测，**不需要配置**。系统会自动从 Nginx 转发的请求头中获取当前域名和协议。

### 3. 一键启动

```bash
# 生产环境（全部服务）
docker compose --profile prod up -d

# 开发环境（仅 DB + Redis + Adminer）
# docker compose --profile dev up -d
```

启动后会运行以下 4 个服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL 18 | 5432（内部） | 数据库 |
| Redis 7 | 6379（内部） | 缓存 |
| Backend | 8000（内部） | FastAPI 后端 |
| Frontend | 80 | Nginx + 前端 |

### 4. 验证部署

```bash
# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs backend -f

# 测试健康检查
curl http://localhost/health
```

访问 `http://你的服务器IP` 即可看到前端页面。

---

## 详细配置

### 完整环境变量说明

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_USER` | 否 | `lecfaka` | 数据库用户名 |
| `DB_PASSWORD` | **是** | `lecfaka123` | 数据库密码 |
| `DB_NAME` | 否 | `lecfaka` | 数据库名 |
| `SECRET_KEY` | **是** | - | 应用密钥 |
| `JWT_SECRET_KEY` | **是** | - | JWT 密钥 |
| `DEBUG` | 否 | `false` | 调试模式 |
| `EPAY_URL` | 否 | - | 易支付接口地址 |
| `EPAY_PID` | 否 | - | 易支付商户 ID |
| `EPAY_KEY` | 否 | - | 易支付商户密钥 |
| `SITE_URL` | 否 | 自动检测 | 前端地址（一般不需设置） |
| `CALLBACK_URL` | 否 | 自动检测 | 支付回调地址（一般不需设置） |

### 修改端口

如果 80 端口被占用，修改 `docker-compose.yml`：

```yaml
frontend:
  ports:
    - "8080:80"  # 改为 8080 端口
```

### 生产环境安全建议

```bash
# 不要暴露数据库和 Redis 端口到外部
# 在 docker-compose.yml 中移除 db 和 redis 的 ports 配置
# 或者绑定到 127.0.0.1：
ports:
  - "127.0.0.1:5432:5432"
```

---

## 域名与 HTTPS 配置

### 方案一：Nginx + Certbot（推荐）

适用于直接在服务器上部署的场景。

#### 1. 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt install certbot python3-certbot-nginx -y
```

#### 2. 修改 Nginx 配置

在服务器上创建 Nginx 配置文件（注意这是**宿主机的 Nginx**，不是 Docker 内的）：

```bash
sudo nano /etc/nginx/sites-available/lecfaka
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name shop.example.com;  # 改成你的域名

    location / {
        proxy_pass http://127.0.0.1:80;  # 指向 Docker 前端服务
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_cache_bypass $http_upgrade;

        # 上传文件大小限制
        client_max_body_size 50M;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/lecfaka /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. 申请 SSL 证书

```bash
sudo certbot --nginx -d shop.example.com
```

Certbot 会自动修改 Nginx 配置，添加 HTTPS 支持和证书自动续期。

#### 4. 验证

访问 `https://shop.example.com` 即可。

> **域名自动检测原理**：当用户通过 `https://shop.example.com` 访问时，Nginx 会将 `X-Forwarded-Proto: https` 和 `X-Forwarded-Host: shop.example.com` 转发给后端，后端自动识别并使用该域名构建回调 URL、邀请链接等。**换域名时只需修改 Nginx 配置和 DNS 解析**，后端无需任何改动。

### 方案二：Cloudflare 代理（最简单）

适用于域名在 Cloudflare 管理的场景。

1. 在 Cloudflare 添加 A 记录，指向你的服务器 IP
2. 开启代理（橙色云朵）
3. SSL/TLS 设置为 "Flexible" 或 "Full"
4. Docker 容器直接暴露 80 端口即可

Cloudflare 会自动处理 HTTPS，并在请求头中附带 `X-Forwarded-Proto: https`。

### 方案三：Docker 内直接用 Nginx + Certbot

如果不想在宿主机安装 Nginx，可以修改 Docker 内的 Nginx。

修改 `docker-compose.yml` 的 frontend 部分：

```yaml
frontend:
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./certbot/conf:/etc/letsencrypt
    - ./certbot/www:/var/www/certbot
```

修改 `docker/nginx.conf`：

```nginx
server {
    listen 80;
    server_name shop.example.com;

    # Certbot 验证
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 其他请求跳转 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name shop.example.com;

    ssl_certificate /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    # API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

然后用 Certbot Docker 镜像申请证书：

```bash
docker run --rm -v ./certbot/conf:/etc/letsencrypt -v ./certbot/www:/var/www/certbot \
    certbot/certbot certonly --webroot -w /var/www/certbot -d shop.example.com
```

---

## 数据备份与恢复

### 备份数据库

```bash
# 创建备份
docker compose exec db pg_dump -U lecfaka lecfaka > backup_$(date +%Y%m%d_%H%M%S).sql

# 定时备份（添加到 crontab）
# 每天凌晨 3 点备份
0 3 * * * cd /opt/lecfaka && docker compose exec -T db pg_dump -U lecfaka lecfaka > /opt/backups/lecfaka_$(date +\%Y\%m\%d).sql
```

### 恢复数据库

```bash
# 恢复备份
docker compose exec -T db psql -U lecfaka lecfaka < backup_20260209.sql
```

### 备份 Redis 数据

```bash
# Redis 数据自动持久化到 Docker volume
# 查看 volume
docker volume ls | grep lecfaka
```

### 完整备份（数据库 + Redis + 配置）

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据库
docker compose exec -T db pg_dump -U lecfaka lecfaka > $BACKUP_DIR/db.sql

# 备份配置文件
cp .env $BACKUP_DIR/.env
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml

echo "备份完成: $BACKUP_DIR"
```

---

## 更新升级

### 更新代码并重新构建

```bash
cd /opt/lecfaka

# 拉取最新代码
git pull

# 重新构建并启动
docker compose build
docker compose up -d

# 查看日志确认启动成功
docker compose logs backend -f
```

### 仅更新后端

```bash
docker compose build backend
docker compose up -d backend
```

### 仅更新前端

```bash
docker compose build frontend
docker compose up -d frontend
```

---

## 常见问题

### 1. 端口被占用

```bash
# 查看占用端口的进程
sudo lsof -i :80
sudo lsof -i :5432

# 停止占用进程或修改 docker-compose.yml 中的端口映射
```

### 2. 数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps db
docker compose logs db

# 如果是 PostgreSQL 版本升级导致，需要清理旧数据卷
docker compose down -v  # ⚠️ 这会删除所有数据！请先备份
docker compose up -d
```

### 3. 支付回调不生效

确认以下几点：

- 域名已正确解析到服务器 IP
- Nginx 配置了 `X-Forwarded-Proto` 和 `X-Forwarded-Host` 头转发
- 防火墙开放了 80/443 端口
- 如果使用 Cloudflare，确保没有开启"仅 DNS"模式

可以通过管理后台接口验证域名检测是否正常：

```bash
curl -H "Host: shop.example.com" http://localhost:8000/api/v1/admin/settings/detect-domain
```

### 4. 查看实时日志

```bash
# 查看所有服务日志
docker compose logs -f

# 只看后端日志
docker compose logs backend -f --tail 100

# 只看 Nginx 日志
docker compose logs frontend -f
```

### 5. 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend
```

### 6. 完全清除重新部署

```bash
# ⚠️ 这会删除所有数据！请先备份
docker compose down -v
docker compose up -d --build
```

---

## 架构图

```
                    用户浏览器
                        │
                        ▼
               ┌────────────────┐
               │   Nginx/CDN    │  ← 域名解析 + HTTPS
               │ (宿主机或CF)    │
               └───────┬────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
    ┌───────────────┐    ┌───────────────┐
    │   Frontend    │    │   Backend     │
    │  (Nginx:80)   │    │  (uvicorn)    │
    │  静态文件 +    │    │  :8000        │
    │  /api 反代    ──────▶              │
    └───────────────┘    └──────┬────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌───────────────┐    ┌───────────────┐
            │ PostgreSQL 18 │    │   Redis 7     │
            │    :5432      │    │    :6379      │
            └───────────────┘    └───────────────┘
```

所有服务运行在同一个 Docker 网络 (`lecfaka-network`) 中，通过服务名互相访问。

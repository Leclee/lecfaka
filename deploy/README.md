# 服务器部署操作手册

> 服务器: 83.229.127.33（宝塔面板）
> 域名: shop.leclee.top + plugins.leclee.top

## 架构说明

LecFaka 包含两个**完全独立**的项目：

| 项目 | 说明 |
|------|------|
| **lecfaka**（主项目） | 发卡网本体，含前端+后端+DB+Redis |
| **lecfaka-store**（插件商店） | 插件分发、授权验证、版本更新 |

```
服务器
├─ lecfaka (Docker Compose)
│  ├─ Frontend :8888 (Nginx 反代)
│  ├─ Backend  :8000 (内部)
│  ├─ PostgreSQL :5432 (仅本机)
│  └─ Redis    :6379 (仅本机)
│
├─ lecfaka-store (Docker Compose)
│  ├─ Store API :8001 (Nginx 反代)
│  └─ PostgreSQL :5433 (仅本机)
│
└─ 宝塔 Nginx :80/443
   ├─ shop.leclee.top    → 127.0.0.1:8888
   └─ plugins.leclee.top → 127.0.0.1:8001
```

## 部署顺序

1. 先部署插件商店（plugins.leclee.top）
2. 再部署主项目（shop.leclee.top）
3. 最后配置宝塔 Nginx

---

## 第一步：SSH 到服务器

```bash
ssh root@83.229.127.33
```

## 第二步：检查 Docker

```bash
docker --version
docker compose version
# 如果没装：curl -fsSL https://get.docker.com | sh
```

## 第三步：部署插件商店

```bash
cd /opt

# 克隆商店代码
git clone https://github.com/Leclee/lecfaka-store.git lecfaka-store
cd lecfaka-store

# 创建 .env
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://lecfaka:你的密码@db:5432/lecfaka_store
SECRET_KEY=用 openssl rand -hex 32 生成
DB_USER=lecfaka
DB_PASSWORD=你的密码
DEBUG=false
HTTP_PORT=8001
EOF

# 启动
docker compose up -d --build

# 验证
curl http://127.0.0.1:8001/health
# 应返回 {"status":"ok","service":"lecfaka-store"}
```

## 第四步：部署主项目

```bash
cd /opt

# 克隆主项目
git clone https://github.com/Leclee/lecfaka.git lecfaka
cd lecfaka

# 创建 .env
SECRET=$(openssl rand -hex 32)
JWT=$(openssl rand -hex 32)
DBPASS=$(openssl rand -hex 16)

cat > .env << EOF
SECRET_KEY=${SECRET}
JWT_SECRET_KEY=${JWT}
DB_USER=lecfaka
DB_PASSWORD=${DBPASS}
DB_NAME=lecfaka
HTTP_PORT=8888
STORE_URL=https://plugins.leclee.top
EOF

echo "数据库密码: ${DBPASS}  (请保存)"

# 启动
docker compose --profile prod up -d --build

# 验证（等待约 30 秒让所有服务 healthy）
curl http://127.0.0.1:8888/health
# 应返回 {"status":"ok","app":"LecFaka"}
```

> **管理员账号**：首次访问 `http://IP:8888/install` 通过安装向导创建，无需在 `.env` 中配置。

## 第五步：配置宝塔 Nginx

### 方法 A：通过宝塔面板网页操作

1. 登录宝塔面板
2. 网站 → 添加站点 → 域名填 `shop.leclee.top`
3. 进入站点设置 → 配置文件 → 清空，粘贴 `deploy/nginx-shop.leclee.top.conf` 的内容
4. 同样添加 `plugins.leclee.top`，粘贴 `deploy/nginx-plugins.leclee.top.conf` 的内容
5. 分别给两个站点配置 SSL 证书

### 方法 B：命令行直接操作

```bash
# 复制 Nginx 配置
cp /opt/lecfaka/deploy/nginx-shop.leclee.top.conf \
   /www/server/panel/vhost/nginx/shop.leclee.top.conf

cp /opt/lecfaka/deploy/nginx-plugins.leclee.top.conf \
   /www/server/panel/vhost/nginx/plugins.leclee.top.conf

# 创建日志文件
touch /www/wwwlogs/shop.leclee.top.log
touch /www/wwwlogs/shop.leclee.top.error.log
touch /www/wwwlogs/plugins.leclee.top.log
touch /www/wwwlogs/plugins.leclee.top.error.log

# 测试并重载
nginx -t
nginx -s reload
```

### SSL 证书

在宝塔面板中操作：网站 → 对应站点 → SSL → 申请或上传证书。

## 第六步：验证完整部署

```bash
# 测试主站
curl -I https://shop.leclee.top
curl https://shop.leclee.top/health

# 测试商店
curl -I https://plugins.leclee.top
curl https://plugins.leclee.top/health

# 测试主站到商店的连通
curl https://plugins.leclee.top/api/v1/store/plugins
```

浏览器访问 https://shop.leclee.top/install 完成安装向导（创建管理员账号）。

---

## 环境变量参考

### 主项目 (.env)

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `SECRET_KEY` | **是** | - | 应用加密密钥 |
| `JWT_SECRET_KEY` | **是** | - | JWT 签名密钥 |
| `DB_USER` | 否 | `lecfaka` | 数据库用户名 |
| `DB_PASSWORD` | **是** | `lecfaka123` | 数据库密码 |
| `DB_NAME` | 否 | `lecfaka` | 数据库名 |
| `HTTP_PORT` | 否 | `80` | 前端 HTTP 端口 |
| `STORE_URL` | 否 | `https://plugins.leclee.top` | 插件商店地址 |

> 管理员账号通过安装向导创建。支付方式在管理后台网页中配置。

### 插件商店 (.env)

| 变量 | 必须 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | **是** | - | 数据库连接串 |
| `SECRET_KEY` | **是** | - | JWT 密钥 |
| `DB_USER` | 否 | `lecfaka` | 数据库用户名 |
| `DB_PASSWORD` | **是** | - | 数据库密码 |
| `DEBUG` | 否 | `true` | 调试模式 |
| `EPAY_URL` / `EPAY_PID` / `EPAY_KEY` | 否 | - | 易支付配置 |

---

## 端口占用表

| 端口 | 服务 | 谁监听 |
|------|------|--------|
| 80/443 | 宝塔 Nginx | 宿主机 |
| 8888 | lecfaka 前端 | Docker → 127.0.0.1 |
| 8000 | lecfaka 后端 | Docker 内部 |
| 5432 | lecfaka PG | Docker → 127.0.0.1 |
| 6379 | lecfaka Redis | Docker → 127.0.0.1 |
| 8001 | 插件商店 API | Docker → 0.0.0.0 |
| 5433 | 商店 PG | Docker → 127.0.0.1 |

## 常用命令

```bash
# 查看服务状态
cd /opt/lecfaka && docker compose --profile prod ps
cd /opt/lecfaka-store && docker compose ps

# 查看日志
cd /opt/lecfaka && docker compose logs backend -f
cd /opt/lecfaka-store && docker compose logs store -f

# 重启
cd /opt/lecfaka && docker compose --profile prod restart
cd /opt/lecfaka-store && docker compose restart

# 更新
cd /opt/lecfaka && git pull && docker compose --profile prod build && docker compose --profile prod up -d
cd /opt/lecfaka-store && git pull && docker compose build && docker compose up -d

# 备份
cd /opt/lecfaka && docker compose exec -T db pg_dump -U lecfaka lecfaka > ~/backup_main_$(date +%Y%m%d).sql
cd /opt/lecfaka-store && docker compose exec -T db pg_dump -U lecfaka lecfaka_store > ~/backup_store_$(date +%Y%m%d).sql

# 完全清除重新部署（⚠️ 会删除所有数据！请先备份）
cd /opt/lecfaka && docker compose --profile prod down -v && docker compose --profile prod up -d --build
```

## 域名配置

系统采用**自动检测方案**，从 Nginx 转发的 HTTP 请求头自动获取域名和协议。

- **换域名**：只需修改 Nginx 的 `server_name` + DNS 解析，后端零修改
- **加 HTTPS**：Nginx 配置 SSL 证书即可，后端通过 `X-Forwarded-Proto` 自动感知

### Cloudflare 方案

1. Cloudflare 添加 A 记录 → 服务器 IP
2. 开启代理（橙色云朵）
3. SSL 设为 "Full"
4. Docker 直接暴露 80 端口即可

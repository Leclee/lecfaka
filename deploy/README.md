# 服务器部署操作手册

> 服务器: 83.229.127.33（宝塔面板）
> 域名: shop.leclee.top + plugins.leclee.top

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

## 第五步：配置宝塔 Nginx

### 方法 A：通过宝塔面板网页操作

1. 登录宝塔面板
2. 网站 → 添加站点 → 域名填 `shop.leclee.top`
3. 进入站点设置 → 配置文件 → 清空，粘贴 `deploy/nginx-shop.leclee.top.conf` 的内容
4. 同样添加 `plugins.leclee.top`，粘贴 `deploy/nginx-plugins.leclee.top.conf` 的内容
5. 分别给两个站点配置 SSL 证书

### 方法 B：命令行直接操作

```bash
# 复制 Nginx 配置（假设已将 deploy/ 目录上传到服务器）
cp /opt/lecfaka/deploy/nginx-shop.leclee.top.conf \
   /www/server/panel/vhost/nginx/shop.leclee.top.conf

cp /opt/lecfaka/deploy/nginx-plugins.leclee.top.conf \
   /www/server/panel/vhost/nginx/plugins.leclee.top.conf

# 创建证书验证目录的 well-known 配置（如果不存在）
touch /www/server/panel/vhost/nginx/well-known/shop.leclee.top.conf
touch /www/server/panel/vhost/nginx/well-known/plugins.leclee.top.conf

# 创建日志目录
touch /www/wwwlogs/shop.leclee.top.log
touch /www/wwwlogs/shop.leclee.top.error.log
touch /www/wwwlogs/plugins.leclee.top.log
touch /www/wwwlogs/plugins.leclee.top.error.log

# 测试 Nginx 配置
nginx -t

# 重载
nginx -s reload
```

### SSL 证书

如果证书路径与配置文件中不一致，需要修改 Nginx 配置中的路径。
宝塔面板的证书一般存放在 `/www/server/panel/vhost/cert/域名/` 目录下。

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
```

#!/bin/bash
# ============================================================
# LecFaka 主项目 - 一键部署脚本
# 
# 使用方法：
#   1. SSH 到服务器
#   2. 将此脚本上传或粘贴到服务器
#   3. chmod +x deploy-main.sh && ./deploy-main.sh
#
# 前提条件：
#   - 已安装 Docker 和 Docker Compose
#   - 宝塔面板 Nginx 已运行在 80/443
# ============================================================

set -e

echo "=========================================="
echo "  LecFaka 主项目部署"
echo "=========================================="

# ---------- 配置区域（按需修改） ----------
INSTALL_DIR="/opt/lecfaka"
GIT_REPO="https://github.com/Leclee/lecfaka.git"
DOMAIN="shop.leclee.top"
DOCKER_PORT=8888               # Docker 前端端口（宝塔 Nginx 反代到此端口）
DB_PASSWORD="$(openssl rand -hex 16)"
SECRET_KEY="$(openssl rand -hex 32)"
JWT_SECRET="$(openssl rand -hex 32)"
ADMIN_USER="admin"
ADMIN_PASS="$(openssl rand -base64 12)"
STORE_URL="https://plugins.leclee.top"
# ------------------------------------------

echo ""
echo "[1/5] 获取代码..."
if [ -d "$INSTALL_DIR" ]; then
    echo "  目录已存在，跳过克隆（如需重新部署请先删除 $INSTALL_DIR）"
    cd "$INSTALL_DIR"
    git pull || true
else
    git clone "$GIT_REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "[2/5] 生成 .env 配置..."
cat > .env << EOF
# LecFaka 环境变量 - 自动生成于 $(date)
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
DB_USER=lecfaka
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=lecfaka
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}
ADMIN_EMAIL=admin@leclee.top
HTTP_PORT=${DOCKER_PORT}
STORE_URL=${STORE_URL}
EOF

echo "  .env 已生成"

echo ""
echo "[3/5] 构建并启动 Docker 服务..."
docker compose --profile prod up -d --build

echo ""
echo "[4/5] 等待服务启动..."
sleep 10

# 检查健康状态
for i in {1..30}; do
    if curl -sf http://127.0.0.1:${DOCKER_PORT}/health > /dev/null 2>&1; then
        echo "  服务已就绪 ✓"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 3
done

echo ""
echo "[5/5] 部署完成！"
echo ""
echo "=========================================="
echo "  部署信息"
echo "=========================================="
echo "  站点域名:    https://${DOMAIN}"
echo "  Docker 端口:  127.0.0.1:${DOCKER_PORT}"
echo "  管理员账号:   ${ADMIN_USER}"
echo "  管理员密码:   ${ADMIN_PASS}"
echo "  数据库密码:   ${DB_PASSWORD}"
echo "  插件商店:     ${STORE_URL}"
echo ""
echo "  ⚠️  请保存以上信息并立即修改管理员密码！"
echo "  ⚠️  还需要配置宝塔 Nginx 反向代理（见下方说明）"
echo ""
echo "  宝塔 Nginx 配置要点："
echo "  域名: ${DOMAIN}"
echo "  反代地址: http://127.0.0.1:${DOCKER_PORT}"
echo "=========================================="

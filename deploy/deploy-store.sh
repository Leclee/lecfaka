#!/bin/bash
# ============================================================
# LecFaka Store 插件商店 - 一键部署脚本
#
# 使用方法：
#   1. SSH 到服务器
#   2. chmod +x deploy-store.sh && ./deploy-store.sh
# ============================================================

set -e

echo "=========================================="
echo "  LecFaka 插件商店部署"
echo "=========================================="

# ---------- 配置区域 ----------
INSTALL_DIR="/opt/lecfaka-store"
GIT_REPO="https://github.com/Leclee/lecfaka-store.git"
DOMAIN="plugins.leclee.top"
STORE_PORT=8001
DB_PASSWORD="$(openssl rand -hex 16)"
SECRET_KEY="$(openssl rand -hex 32)"
# ------------------------------

echo ""
echo "[1/4] 获取代码..."
if [ -d "$INSTALL_DIR" ]; then
    echo "  目录已存在，跳过克隆"
    cd "$INSTALL_DIR"
    git pull || true
else
    git clone "$GIT_REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "[2/4] 生成 .env 配置..."
cat > .env << EOF
# LecFaka Store - 自动生成于 $(date)
DATABASE_URL=postgresql+asyncpg://lecfaka:${DB_PASSWORD}@db:5432/lecfaka_store
SECRET_KEY=${SECRET_KEY}
DB_USER=lecfaka
DB_PASSWORD=${DB_PASSWORD}
DEBUG=false
HTTP_PORT=${STORE_PORT}
EOF

echo "  .env 已生成"

echo ""
echo "[3/4] 构建并启动..."
docker compose up -d --build

echo ""
echo "[4/4] 等待服务启动..."
sleep 8

for i in {1..20}; do
    if curl -sf http://127.0.0.1:${STORE_PORT}/health > /dev/null 2>&1; then
        echo "  服务已就绪 ✓"
        break
    fi
    echo "  等待中... ($i/20)"
    sleep 3
done

echo ""
echo "=========================================="
echo "  插件商店部署完成"
echo "=========================================="
echo "  域名:        https://${DOMAIN}"
echo "  API 端口:    127.0.0.1:${STORE_PORT}"
echo "  数据库密码:  ${DB_PASSWORD}"
echo ""
echo "  ⚠️  还需要配置宝塔 Nginx 反代（见下方）"
echo "  域名: ${DOMAIN}"
echo "  反代地址: http://127.0.0.1:${STORE_PORT}"
echo "=========================================="

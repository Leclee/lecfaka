#!/bin/bash
# ============================================================
# LecFaka 主项目 - 一键部署脚本
# 
# 使用方法：
#   1. SSH 到服务器
#   2. chmod +x deploy-main.sh && ./deploy-main.sh
#
# 前提条件：
#   - 已安装 Docker 和 Docker Compose
#   - 宝塔面板 Nginx 已运行在 80/443
#
# 管理员账号通过 Web 安装向导创建，部署完成后访问 /install
# ============================================================

set -e

echo "=========================================="
echo "  LecFaka 主项目部署"
echo "=========================================="

# ---------- 配置区域（按需修改） ----------
INSTALL_DIR="/opt/lecfaka"
GIT_REPO="https://github.com/Leclee/lecfaka.git"
DOCKER_PORT=8888               # Docker 前端端口（宝塔 Nginx 反代到此端口）
DB_PASSWORD="$(openssl rand -hex 16)"
SECRET_KEY="$(openssl rand -hex 32)"
JWT_SECRET="$(openssl rand -hex 32)"
STORE_URL="https://plugins.leclee.top"
# ------------------------------------------

echo ""
echo "[1/4] 获取代码..."
if [ -d "$INSTALL_DIR" ]; then
    echo "  目录已存在，执行 git pull"
    cd "$INSTALL_DIR"
    git pull || true
else
    git clone "$GIT_REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "[2/4] 生成 .env 配置..."
cat > .env << EOF
# LecFaka - 自动生成于 $(date)
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
DB_USER=lecfaka
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=lecfaka
HTTP_PORT=${DOCKER_PORT}
STORE_URL=${STORE_URL}
EOF

echo "  .env 已生成"

echo ""
echo "[3/4] 构建并启动 Docker 服务..."
docker compose --profile prod up -d --build

echo ""
echo "[4/4] 等待服务启动..."
sleep 10

for i in {1..30}; do
    if curl -sf http://127.0.0.1:${DOCKER_PORT}/health > /dev/null 2>&1; then
        echo "  服务已就绪"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 3
done

echo ""
echo "=========================================="
echo "  部署完成"
echo "=========================================="
echo ""
echo "  Docker 端口: 127.0.0.1:${DOCKER_PORT}"
echo "  数据库密码:  ${DB_PASSWORD}"
echo ""
echo "  下一步操作："
echo "  1. 配置宝塔 Nginx 反向代理"
echo "     反代地址: http://127.0.0.1:${DOCKER_PORT}"
echo "  2. 访问你的域名/install 完成安装"
echo "     在网页上创建管理员账号"
echo ""
echo "=========================================="

"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db, close_db, async_session_maker
from .core.exceptions import AppException
from .api.v1 import api_router
from .plugins import plugin_manager
from .plugins.sdk.hooks import hooks, Events


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print(f"[Starting] {settings.app_name}...")
    
    # 自动创建数据库表（生产和开发模式都执行，确保首次部署表结构存在）
    try:
        await init_db()
        print("[OK] Database tables ready")
    except Exception as e:
        print(f"[WARN] Database init error: {e}")
    
    # 管理员由 Web 安装向导创建，不再从环境变量自动创建
    try:
        async with async_session_maker() as db:
            from sqlalchemy import select
            from .models.user import User
            result = await db.execute(
                select(User.id).where(User.is_admin == True).limit(1)
            )
            if result.scalar_one_or_none():
                print("[OK] System installed")
            else:
                print("[OK] Awaiting installation via /install")
    except Exception as e:
        print(f"[WARN] Install check error: {e}")
    
    # 加载插件系统
    try:
        async with async_session_maker() as db:
            await plugin_manager.scan_and_load(db)
        print("[OK] Plugin system loaded")
    except Exception as e:
        print(f"[WARN] Plugin system load error: {e}")
    
    # 触发应用启动事件
    await hooks.emit(Events.APP_STARTUP, {"app": app})
    
    # 启动定时授权验证后台任务（每 24 小时）
    import asyncio
    
    async def _license_verify_loop():
        while True:
            await asyncio.sleep(86400)  # 24 小时
            try:
                await plugin_manager.verify_all_licenses()
                print("[OK] Scheduled license verification completed")
            except Exception as e:
                print(f"[WARN] License verification error: {e}")
    
    license_task = asyncio.create_task(_license_verify_loop())
    
    yield
    
    # 取消后台任务
    license_task.cancel()
    
    # 触发关闭事件
    await hooks.emit(Events.APP_SHUTDOWN)
    
    # 关闭时
    await close_db()
    print(f"[Shutdown] {settings.app_name} complete")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title=settings.app_name,
        description="现代化自动发卡系统 API",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # CORS配置
    # 由 Nginx 反向代理统一处理域名，后端始终允许所有来源
    # 生产环境安全性由 Nginx 的 server_name 保证
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 全局异常处理
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        import traceback
        import sys
        error_detail = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc()
        print(f"[ERROR] {request.method} {request.url.path}: {error_detail}", file=sys.stderr, flush=True)
        print(tb, file=sys.stderr, flush=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": error_detail if settings.debug else "服务器内部错误",
                "detail": tb if settings.debug else None,
                "data": None
            }
        )
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "app": settings.app_name}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=6666,
        reload=settings.debug
    )

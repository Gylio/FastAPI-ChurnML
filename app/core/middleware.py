from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.services.session_service import get_user_from_session
from app.core.logging import setup_logging

# 初始化日志器
logger = setup_logging("app")

async def auth_middleware(request: Request, call_next):
    """
    认证中间件，验证用户是否登录
    """
    # 不需要登录的路径
    exempt_paths = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/logout",
        "/api/auth/me",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
        "/favicon.ico",
        "/.well-known",
    ]
    
    # 检查当前路径是否需要登录
    path = request.url.path
    for exempt_path in exempt_paths:
        if path.startswith(exempt_path):
            response = await call_next(request)
            return response
    
    # 从cookie中获取会话ID
    session_id = None
    cookies = request.cookies
    if "session_id" in cookies:
        session_id = cookies["session_id"]
    
    # 验证会话
    user = None
    if session_id:
        user = get_user_from_session(session_id)
    
    # 如果没有登录：
    # - 前端页面：重定向到登录页
    # - API 请求：返回 401 JSON（避免 fetch 跟随重定向拿到 HTML）
    if not user:
        logger.info(f"未登录用户尝试访问受保护资源: {path}")
        if path.startswith("/api"):
            return JSONResponse(status_code=401, content={"detail": {"error_message": "未登录", "error_code": 401}})
        return RedirectResponse(url="/api/auth/login")
    
    # 将用户信息添加到请求中
    request.state.user = user
    logger.info(f"用户 {user['username']} 访问: {path}")
    
    response = await call_next(request)
    return response

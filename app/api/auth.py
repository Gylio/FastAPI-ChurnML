from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.schemas.schemas import AuthResponse
from app.services.auth_service import register, login
from app.services.session_service import create_session, delete_session, get_user_from_session
from app.core.logging import setup_logging
from pathlib import Path
import time
import uuid
from typing import Any, Dict, Optional, Tuple

# 初始化日志器
logger = setup_logging("app")

# 创建路由器
router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# 获取应用根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 初始化模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

async def _extract_credentials(request: Request) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从请求中提取 username/email/password。
    兼容 JSON 与表单，但不依赖 FastAPI 的 Body/Form 参数解析，避免冲突导致字段为 None。
    """
    content_type = (request.headers.get("content-type") or "").lower()
    data: Dict[str, Any] = {}

    if "application/json" in content_type:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                data = payload
        except Exception:
            data = {}
    else:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}

    username = (data.get("username") or None)
    email = (data.get("email") or None)
    password = (data.get("password") or None)
    if isinstance(username, str):
        username = username.strip()
    if isinstance(email, str):
        email = email.strip()
    return username, email, password


@router.post("/register", response_model=AuthResponse, summary="用户注册")
async def register_user(request: Request):
    """
    用户注册
    
    - **username**: 用户名
    - **email**: 邮箱
    - **password**: 密码
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        username, email, password = await _extract_credentials(request)
        logger.info(f"收到注册请求，请求ID: {request_id}, 用户名: {username}, 邮箱: {email}")
        
        # 验证请求数据
        if not username or not email or not password:
            logger.warning(f"注册请求数据不完整，请求ID: {request_id}")
            return AuthResponse(
                success=False,
                message="请求数据不完整"
            )
        
        result = register(username, email, password)
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        if result["success"]:
            logger.info(f"用户注册成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 用户名: {username}")
            return AuthResponse(
                success=True,
                message=result["message"]
            )
        else:
            logger.warning(f"用户注册失败，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 用户名: {username}, 原因: {result['message']}")
            return AuthResponse(
                success=False,
                message=result["message"]
            )
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.error(f"用户注册异常，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 错误: {e}")
        return AuthResponse(
            success=False,
            message="注册失败"
        )

@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login_user(request: Request):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        username, _, password = await _extract_credentials(request)
        if not username or not password:
            logger.warning(f"登录请求数据不完整，请求ID: {request_id}")
            return AuthResponse(success=False, message="请求数据不完整")

        result = login(username, password)
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        if result["success"]:
            logger.info(f"用户登录成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 用户名: {username}")
            # 创建会话
            session_id = create_session(result.get("user_id"), result.get("username"))
            auth_response = AuthResponse(
                success=True,
                message=result["message"],
                user_id=result.get("user_id"),
                username=result.get("username"),
                session_id=session_id
            )
            # 同时在服务端写入 cookie，避免仅依赖前端 JS 写 cookie
            json_response = JSONResponse(content=auth_response.dict())
            json_response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=3600,
                expires=3600,
                path="/",
                samesite="lax",
                httponly=True,
            )
            return json_response
        else:
            logger.warning(f"用户登录失败，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 用户名: {username}, 原因: {result['message']}")
            return AuthResponse(
                success=False,
                message=result["message"]
            )
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.error(f"用户登录异常，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 错误: {e}")
        return AuthResponse(
            success=False,
            message="登录失败"
        )


@router.post("/logout", response_model=AuthResponse, summary="用户退出登录")
async def logout_user(request: Request):
    """
    用户退出登录
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        session_id = request.cookies.get("session_id")
        if session_id:
            delete_session(session_id)

        response_time = time.time() - start_time
        logger.info(f"用户退出登录，请求ID: {request_id}, 响应时间: {response_time:.4f}秒")

        auth_response = AuthResponse(success=True, message="已退出登录")
        json_response = JSONResponse(content=auth_response.dict())
        json_response.delete_cookie(key="session_id", path="/")
        return json_response
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"用户退出登录异常，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 错误: {e}")
        return AuthResponse(success=False, message="退出登录失败")


@router.get("/me", summary="获取当前登录用户")
async def me(request: Request):
    session_id = request.cookies.get("session_id")
    user = get_user_from_session(session_id) if session_id else None
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return {"user_id": user.get("user_id"), "username": user.get("username")}

# 前端页面路由
@router.get("/login", response_class=HTMLResponse, summary="登录页面")
async def login_page(request: Request):
    """
    登录页面
    """
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse, summary="注册页面")
async def register_page(request: Request):
    """
    注册页面
    """
    return templates.TemplateResponse("register.html", {"request": request})

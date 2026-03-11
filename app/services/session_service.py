from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.logging import setup_logging
import uuid
import os

# 初始化会话服务专用日志器
logger = setup_logging("app")

class SessionService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=1)
    
    def create_session(self, user_id: int, username: str) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "username": username,
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        }
        logger.info(f"创建新会话，用户: {username}, 会话ID: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # 检查会话是否过期
        if datetime.now() - session["last_accessed"] > self.session_timeout:
            del self.sessions[session_id]
            logger.info(f"会话已过期，会话ID: {session_id}")
            return None
        
        # 更新最后访问时间
        session["last_accessed"] = datetime.now()
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"会话已删除，会话ID: {session_id}")
            return True
        return False
    
    def get_user_from_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从会话中获取用户信息"""
        session = self.get_session(session_id)
        if session:
            return {
                "user_id": session["user_id"],
                "username": session["username"]
            }
        return None

# 全局会话服务实例
session_service = SessionService()

def get_session_service():
    """获取会话服务实例"""
    return session_service

def create_session(user_id: int, username: str) -> str:
    """创建新会话"""
    return session_service.create_session(user_id, username)

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话信息"""
    return session_service.get_session(session_id)

def delete_session(session_id: str) -> bool:
    """删除会话"""
    return session_service.delete_session(session_id)

def get_user_from_session(session_id: str) -> Optional[Dict[str, Any]]:
    """从会话中获取用户信息"""
    return session_service.get_user_from_session(session_id)

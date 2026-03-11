from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.logging import setup_logging
import sqlite3
import hashlib
import os

# 初始化认证服务专用日志器
logger = setup_logging("app")

class AuthService:
    def __init__(self):
        from pathlib import Path
        self.db_path = str(Path(__file__).resolve().parent.parent / "auth.db")
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("用户数据库初始化成功")
    
    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + key.hex()
    
    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """验证密码"""
        salt = bytes.fromhex(stored_password[:64])
        stored_key = stored_password[64:]
        key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return key.hex() == stored_key
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """注册新用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "message": "用户名已存在"}
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return {"success": False, "message": "邮箱已存在"}
            
            # 哈希密码
            hashed_password = self._hash_password(password)
            
            # 插入新用户
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户注册成功: {username}")
            return {"success": True, "message": "注册成功"}
        except Exception as e:
            logger.error(f"注册失败: {e}")
            return {"success": False, "message": "注册失败"}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            conn.close()
            
            if not user:
                return {"success": False, "message": "用户名或密码错误"}
            
            # 验证密码
            if not self._verify_password(user[2], password):
                return {"success": False, "message": "用户名或密码错误"}
            
            logger.info(f"用户登录成功: {username}")
            return {"success": True, "message": "登录成功", "user_id": user[0], "username": user[1]}
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return {"success": False, "message": "登录失败"}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            conn.close()
            
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "created_at": user[3]
                }
            return None
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

# 全局认证服务实例
auth_service = AuthService()

def get_auth_service():
    """获取认证服务实例"""
    return auth_service

def register(username: str, email: str, password: str) -> Dict[str, Any]:
    """注册新用户"""
    return auth_service.register(username, email, password)

def login(username: str, password: str) -> Dict[str, Any]:
    """用户登录"""
    return auth_service.login(username, password)

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取用户信息"""
    return auth_service.get_user_by_id(user_id)

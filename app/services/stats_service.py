from typing import Dict, Any, Optional
from datetime import datetime
from app.core.logging import setup_logging
import json
import os

# 初始化统计服务专用日志器
logger = setup_logging("app")

class StatsService:
    def __init__(self):
        self.stats_file = "stats.json"
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'accuracy': 0.85,  # 默认准确率为85%
            'average_response_time': 0.0,
            'response_times': [],
            'last_update': datetime.now().isoformat()
        }
        self._load_stats()
    
    def _load_stats(self):
        """加载统计数据"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
                logger.info("统计数据加载成功")
            except Exception as e:
                logger.error(f"加载统计数据失败: {e}")
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            logger.info("统计数据保存成功")
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def record_request(self, request_type: str, successful: bool, response_time: float, request_id: str):
        """记录请求
        
        Args:
            request_type: 请求类型 (single, batch, model)
            successful: 是否成功
            response_time: 响应时间（秒）
            request_id: 请求ID
        """
        self.stats['total_requests'] += 1
        if successful:
            self.stats['successful_requests'] += 1
            self.stats['response_times'].append(response_time)
            # 更新平均响应时间
            if self.stats['response_times']:
                self.stats['average_response_time'] = sum(self.stats['response_times']) / len(self.stats['response_times'])
        else:
            self.stats['failed_requests'] += 1
        
        self.stats['last_update'] = datetime.now().isoformat()
        self._save_stats()
    
    def update_accuracy(self, accuracy: float):
        """更新模型准确率
        
        Args:
            accuracy: 准确率
        """
        self.stats['accuracy'] = accuracy
        self.stats['last_update'] = datetime.now().isoformat()
        self._save_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            统计数据
        """
        return self.stats
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'accuracy': 0.85,  # 默认准确率为85%
            'average_response_time': 0.0,
            'response_times': [],
            'last_update': datetime.now().isoformat()
        }
        self._save_stats()
        logger.info("统计数据已重置")

# 全局统计服务实例
stats_service = StatsService()

def get_stats_service():
    """获取统计服务实例"""
    return stats_service

def record_request(request_type: str, successful: bool, response_time: float, request_id: str):
    """记录请求"""
    stats_service.record_request(request_type, successful, response_time, request_id)

def update_accuracy(accuracy: float):
    """更新模型准确率"""
    stats_service.update_accuracy(accuracy)

def get_stats() -> Dict[str, Any]:
    """获取统计数据"""
    return stats_service.get_stats()

def reset_stats():
    """重置统计数据"""
    stats_service.reset_stats()

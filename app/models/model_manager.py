import os
import joblib
from pathlib import Path
from app.core.config import MODEL_DIR, settings
from app.core.logging import setup_logging

# 初始化模型管理专用日志器
logger = setup_logging("app")


class ModelManager:
    def __init__(self):
        self.model_dir = MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.current_model = None
        self.current_version = None
        self.models = {}

    def list_available_models(self):
        """列出所有可用的模型版本"""
        logger.info("\n=== 列出可用模型 ===")

        model_files = list(self.model_dir.glob(f'churn_pred_v*'))
        models = []

        for model_file in model_files:
            version = self._extract_version(model_file.name)
            if version:
                models.append({
                    'version': version,
                    'path': str(model_file),
                    'filename': model_file.name
                })

        # 按版本号排序
        models.sort(key=lambda x: x['version'])

        logger.info(f"找到 {len(models)} 个可用模型:")
        for model in models:
            logger.info(f"版本: v{model['version']}, 文件: {model['filename']}")

        return models

    def load_model(self, version):
        """加载指定版本的模型"""
        logger.info(f"\n=== 加载模型 v{version} ===")

        model_path = self.model_dir / f'churn_pred_v{version}{settings.MODEL_FILE_SUFFIX}'

        if not model_path.exists():
            logger.error(f"模型文件不存在: {model_path}")
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        try:
            model_data = joblib.load(model_path)
            self.current_model = model_data['model']
            self.current_version = version
            self.models[version] = model_data

            logger.info(f"模型 v{version} 加载成功")
            return self.current_model
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def get_current_model(self):
        """获取当前加载的模型"""
        if self.current_model is None:
            logger.warning("没有加载任何模型")
            # 尝试加载最新版本的模型
            available_models = self.list_available_models()
            if available_models:
                latest_version = available_models[-1]['version']
                return self.load_model(latest_version)
        return self.current_model

    def get_model_version(self):
        """获取当前模型的版本"""
        return self.current_version

    def switch_model(self, version):
        """切换到指定版本的模型"""
        return self.load_model(version)

    def predict(self, data):
        """使用当前模型进行预测"""
        if self.current_model is None:
            self.get_current_model()

        if self.current_model is None:
            raise ValueError("没有可用的模型")

        # 检查是否有预处理对象
        if self.current_version in self.models and 'preprocessor' in self.models[self.current_version]:
            preprocessor = self.models[self.current_version]['preprocessor']
            data = preprocessor.transform(data)

        return self.current_model.predict(data)

    def predict_proba(self, data):
        """使用当前模型进行概率预测"""
        if self.current_model is None:
            self.get_current_model()

        if self.current_model is None:
            raise ValueError("没有可用的模型")

        # 检查是否有预处理对象
        if self.current_version in self.models and 'preprocessor' in self.models[self.current_version]:
            preprocessor = self.models[self.current_version]['preprocessor']
            data = preprocessor.transform(data)

        return self.current_model.predict_proba(data)

    def _extract_version(self, filename):
        """从文件名中提取版本号"""
        try:
            # 提取 v 后面的数字部分
            version_str = filename.split('v')[1].split('.')[0]
            return int(version_str)
        except (IndexError, ValueError):
            return None


# 全局模型管理器实例
model_manager = ModelManager()


def get_model_manager():
    """获取模型管理器实例"""
    return model_manager


def load_model(version):
    """加载指定版本的模型"""
    return model_manager.load_model(version)


def get_current_model():
    """获取当前模型"""
    return model_manager.get_current_model()


def predict(data):
    """使用当前模型进行预测"""
    return model_manager.predict(data)


def predict_proba(data):
    """使用当前模型进行概率预测"""
    return model_manager.predict_proba(data)


def list_models():
    """列出所有可用模型"""
    return model_manager.list_available_models()


def get_model_version():
    """获取当前模型版本"""
    return model_manager.get_model_version()
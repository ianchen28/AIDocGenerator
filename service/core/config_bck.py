"""
极简化配置管理器
提供按key提取配置的功能，支持环境变量替换
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)


class Config:
    """极简化配置类"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        self.config_path = Path(config_path)
        self._config_data = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换环境变量
        content = self._replace_env_vars(content)

        # 解析YAML
        self._config_data = yaml.safe_load(content)

    def _replace_env_vars(self, content: str) -> str:
        """替换环境变量占位符"""

        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_var, content)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键，如 'api.timeout'
            default: 默认值，当键不存在时返回
        
        Returns:
            配置值或默认值
        """
        try:
            keys = key.split('.')
            value = self._config_data

            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, default)
                else:
                    return default

            return value
        except Exception:
            return default

    def set(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        
        Returns:
            是否设置成功
        """
        try:
            keys = key.split('.')
            config = self._config_data

            # 导航到父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value
            return True
        except Exception:
            return False

    def reload(self) -> bool:
        """重新加载配置"""
        try:
            self._load_config()
            return True
        except Exception:
            return False

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config_data.copy()


# 全局配置实例
_config_instance = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def get(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config().get(key, default)


def set(key: str, value: Any) -> bool:
    """设置配置值"""
    return get_config().set(key, value)


def reload() -> bool:
    """重新加载配置"""
    return get_config().reload()


def get_all() -> Dict[str, Any]:
    """获取所有配置"""
    return get_config().get_all()

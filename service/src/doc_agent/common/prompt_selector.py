"""
Prompt Selector 模块

本模块提供了 PromptSelector 类，用于动态导入 prompt 模块
并选择特定版本的 prompt。现在支持 genre-aware 功能。
"""

import importlib
from pathlib import Path
from typing import Any, Optional

import yaml
from doc_agent.core.logger import logger


class PromptSelector:
    """
    用于动态导入 prompt 模块并选择特定版本 prompt 的类。

    该类通过基于工作流类型、节点名称和版本动态导入 prompt 模块，
    实现灵活的 prompt 管理。现在支持 genre-aware 功能。
    """

    def __init__(self, genre_strategies: Optional[dict] = None):
        """
        初始化 PromptSelector。

        Args:
            genre_strategies (Optional[Dict]): genre 策略字典，如果为 None 则从 genres.yaml 加载
        """
        if genre_strategies is None:
            self.genre_strategies = self._load_genre_strategies()
        else:
            self.genre_strategies = genre_strategies

        logger.debug(
            f"PromptSelector 初始化完成，加载了 {len(self.genre_strategies)} 个 genre 策略"
        )

    def _load_genre_strategies(self) -> dict:
        """
        从 genres.yaml 文件加载 genre 策略。

        Returns:
            Dict: genre 策略字典
        """
        try:
            # 尝试从 service/core/genres.yaml 加载
            genres_file = Path(
                __file__).parent.parent.parent.parent / "core" / "genres.yaml"
            if not genres_file.exists():
                # 如果不存在，返回默认策略
                logger.warning(f"genres.yaml 文件不存在: {genres_file}")
                return self._get_default_genre_strategies()

            with open(genres_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                strategies = data.get('genres', {})
                logger.info(f"成功加载 {len(strategies)} 个 genre 策略")
                return strategies

        except Exception as e:
            logger.error(f"加载 genre 策略失败: {e}")
            return self._get_default_genre_strategies()

    def _get_default_genre_strategies(self) -> dict:
        """
        获取默认的 genre 策略。

        Returns:
            Dict: 默认的 genre 策略字典
        """
        return {
            "default": {
                "name": "通用文档",
                "description": "适用于大多数标准报告和分析。",
                "prompt_versions": {
                    "planner": "v1_default",
                    "supervisor": "v1_metadata_based",
                    "writer": "v1_default",
                    "outline_generation": "v1_default"
                }
            }
        }

    def get_prompt(self,
                   workflow_type: str,
                   node_name: str,
                   genre: str = "default") -> str:
        """
        基于工作流类型、节点名称和 genre 获取特定的 prompt。

        Args:
            workflow_type (str): 工作流类型（例如："chapter_workflow", "prompts"）
            node_name (str): 节点名称（例如："writer", "planner", "supervisor"）
            genre (str): genre 类型（例如："work_report", "speech_draft"），默认为 "default"

        Returns:
            str: 请求的 prompt 模板

        Raises:
            ImportError: 如果模块无法导入
            KeyError: 如果版本在模块中不存在
            AttributeError: 如果模块中不存在 PROMPTS 字典
            ValueError: 如果 genre 或节点在策略中不存在
        """
        try:
            # 1. 获取 genre 策略
            if genre not in self.genre_strategies:
                available_genres = list(self.genre_strategies.keys())
                raise ValueError(
                    f"未找到 genre '{genre}'。可用 genres: {available_genres}")

            genre_strategy = self.genre_strategies[genre]
            prompt_versions = genre_strategy.get('prompt_versions', {})

            # 2. 获取该节点在指定 genre 下的 prompt 版本
            if node_name not in prompt_versions:
                available_nodes = list(prompt_versions.keys())
                raise ValueError(
                    f"在 genre '{genre}' 中未找到节点 '{node_name}'。可用节点: {available_nodes}"
                )

            version = prompt_versions[node_name]
            logger.debug(f"Genre '{genre}' 为节点 '{node_name}' 选择版本: {version}")

            # 3. 构建模块路径
            if workflow_type == "chapter_workflow":
                # chapter_workflow 的 prompt 模块在 prompts 目录下
                module_path = f"doc_agent.prompts.{node_name}"
            else:
                module_path = f"doc_agent.{workflow_type}.{node_name}"

            logger.debug(f"尝试导入模块: {module_path}")

            # 4. 动态导入模块
            module = importlib.import_module(module_path)

            # 5. 首先，尝试从模块中获取 PROMPTS 字典
            if hasattr(module, 'PROMPTS'):
                prompts_dict = module.PROMPTS

                # 检查版本是否存在
                if version not in prompts_dict:
                    available_versions = list(prompts_dict.keys())
                    raise KeyError(
                        f"在模块 {module_path} 中未找到版本 '{version}'。可用版本: {available_versions}"
                    )

                # 返回请求的 prompt
                prompt = prompts_dict[version]
                logger.debug(
                    f"成功获取 prompt: {workflow_type}.{node_name}.{version} (genre: {genre})"
                )
                return prompt
            else:
                # 备用方案：查找独立的 prompt 变量
                prompt_vars = self._get_prompt_variables(module, version)
                if prompt_vars:
                    return prompt_vars
                else:
                    # 尝试从模块中获取任何可用的 prompt
                    available_prompts = self._get_all_prompt_variables(module)
                    if available_prompts:
                        # 返回第一个可用的 prompt
                        first_prompt = list(available_prompts.values())[0]
                        logger.debug(
                            f"为 {workflow_type}.{node_name} (genre: {genre}) 使用第一个可用的 prompt"
                        )
                        return first_prompt
                    else:
                        raise AttributeError(
                            f"模块 {module_path} 不包含 PROMPTS 字典或兼容的 prompt 变量")

        except ImportError as e:
            logger.error(f"导入模块 {module_path} 失败: {e}")
            raise ImportError(f"无法导入模块 {module_path}: {e}") from e
        except AttributeError as e:
            logger.error(f"模块 {module_path} 缺少必需的属性: {e}")
            raise
        except KeyError as e:
            logger.error(f"在模块 {module_path} 中未找到版本 {version}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Genre 或节点配置错误: {e}")
            raise
        except Exception as e:
            logger.error(f"获取 prompt 时发生意外错误: {e}")
            raise

    def get_genre_info(self, genre: str) -> dict:
        """
        获取指定 genre 的信息。

        Args:
            genre (str): genre 名称

        Returns:
            Dict: genre 信息字典，包含 name, description, prompt_versions
        """
        if genre not in self.genre_strategies:
            available_genres = list(self.genre_strategies.keys())
            raise ValueError(
                f"未找到 genre '{genre}'。可用 genres: {available_genres}")

        return self.genre_strategies[genre]

    def list_available_genres(self) -> list:
        """
        列出所有可用的 genres。

        Returns:
            list: 可用 genres 的列表
        """
        return list(self.genre_strategies.keys())

    def list_available_nodes_for_genre(self, genre: str) -> list:
        """
        列出指定 genre 中可用的节点。

        Args:
            genre (str): genre 名称

        Returns:
            list: 可用节点的列表
        """
        if genre not in self.genre_strategies:
            return []

        genre_strategy = self.genre_strategies[genre]
        prompt_versions = genre_strategy.get('prompt_versions', {})
        return list(prompt_versions.keys())

    def _get_prompt_variables(self, module: Any,
                              version: str) -> Optional[str]:
        """
        从模块中获取 prompt 变量的备用方法。

        当 PROMPTS 字典不可用时，此方法查找模块中的独立 prompt 变量。

        Args:
            module: 导入的模块
            version (str): 要查找的版本

        Returns:
            Optional[str]: 如果找到则返回 prompt，否则返回 None
        """
        # 常见的 prompt 变量模式
        patterns = [
            f"{version.upper()}_PROMPT",
            f"{version.upper()}_WRITER_PROMPT",
            f"{version.upper()}_PLANNER_PROMPT",
            f"{version.upper()}_SUPERVISOR_PROMPT",
            f"{version.upper()}_CONTENT_PROCESSOR_PROMPT",
            f"{version.upper()}_OUTLINE_GENERATION_PROMPT",
            "WRITER_PROMPT",
            "PLANNER_PROMPT",
            "SUPERVISOR_PROMPT",
            "CONTENT_PROCESSOR_PROMPT",
            "OUTLINE_GENERATION_PROMPT",
            "FAST_WRITER_PROMPT",
            "FAST_PLANNER_PROMPT",
            "FAST_SUPERVISOR_PROMPT",
            "FAST_CONTENT_PROCESSOR_PROMPT",
            "FAST_OUTLINE_GENERATION_PROMPT",
            # 内容处理器特定模式
            "RESEARCH_DATA_SUMMARY_PROMPT",
            "KEY_POINTS_EXTRACTION_PROMPT",
            "CONTENT_COMPRESSION_PROMPT",
            # 快速内容处理器特定模式
            "FAST_RESEARCH_DATA_SUMMARY_PROMPT",
            "FAST_KEY_POINTS_EXTRACTION_PROMPT",
            "FAST_CONTENT_COMPRESSION_PROMPT"
        ]

        for pattern in patterns:
            if hasattr(module, pattern):
                prompt = getattr(module, pattern)
                logger.debug(f"找到 prompt 变量: {pattern}")
                return prompt

        return None

    def _get_all_prompt_variables(self, module: Any) -> dict[str, str]:
        """
        从模块中获取所有可用的 prompt 变量。

        Args:
            module: 导入的模块

        Returns:
            Dict[str, str]: prompt 变量名称和值的字典
        """
        prompts = {}

        # 常见的 prompt 变量模式
        patterns = [
            "WRITER_PROMPT",
            "PLANNER_PROMPT",
            "SUPERVISOR_PROMPT",
            "CONTENT_PROCESSOR_PROMPT",
            "OUTLINE_GENERATION_PROMPT",
            "FAST_WRITER_PROMPT",
            "FAST_PLANNER_PROMPT",
            "FAST_SUPERVISOR_PROMPT",
            "FAST_CONTENT_PROCESSOR_PROMPT",
            "FAST_OUTLINE_GENERATION_PROMPT",
            # 内容处理器特定模式
            "RESEARCH_DATA_SUMMARY_PROMPT",
            "KEY_POINTS_EXTRACTION_PROMPT",
            "CONTENT_COMPRESSION_PROMPT",
            # 快速内容处理器特定模式
            "FAST_RESEARCH_DATA_SUMMARY_PROMPT",
            "FAST_KEY_POINTS_EXTRACTION_PROMPT",
            "FAST_CONTENT_COMPRESSION_PROMPT"
        ]

        for pattern in patterns:
            if hasattr(module, pattern):
                prompt = getattr(module, pattern)
                prompts[pattern] = prompt

        return prompts

    def get_available_workflows(self) -> list[str]:
        """获取可用的工作流列表"""
        return ["prompts", "chapter_workflow"]

    def list_available_nodes(self, workflow_type: str) -> list:
        """
        列出给定工作流类型的可用节点。

        Args:
            workflow_type (str): 工作流类型

        Returns:
            list: 可用节点的列表
        """
        if workflow_type == "prompts":
            return [
                "writer", "planner", "supervisor", "content_processor",
                "outline_generation", "reflection", "ai_editor"
            ]
        elif workflow_type == "chapter_workflow":
            return ["planner", "writer", "researcher", "supervisor"]
        else:
            return []

    def list_available_versions(self, workflow_type: str,
                                node_name: str) -> list:
        """
        列出给定工作流类型和节点的可用版本。

        Args:
            workflow_type (str): 工作流类型
            node_name (str): 节点名称

        Returns:
            list: 可用版本的列表
        """
        try:
            if workflow_type == "chapter_workflow":
                module_path = f"doc_agent.graph.chapter_workflow.{node_name}"
            else:
                module_path = f"doc_agent.{workflow_type}.{node_name}"
            module = importlib.import_module(module_path)

            if hasattr(module, 'PROMPTS'):
                return list(module.PROMPTS.keys())
            else:
                # 返回常见版本模式
                return [
                    "v1_default", "simple", "detailed", "v1_metadata_based"
                ]
        except ImportError:
            return []

    def validate_prompt(self,
                        workflow_type: str,
                        node_name: str,
                        genre: str = "default") -> bool:
        """
        验证给定参数的 prompt 是否存在。

        Args:
            workflow_type (str): 工作流类型
            node_name (str): 节点名称
            genre (str): genre 类型，默认为 "default"

        Returns:
            bool: 如果 prompt 存在则返回 True，否则返回 False
        """
        try:
            self.get_prompt(workflow_type, node_name, genre)
            return True
        except (ImportError, KeyError, AttributeError, ValueError):
            return False


# 便捷函数，用于轻松访问
def get_prompt(workflow_type: str,
               node_name: str,
               genre: str = "default") -> str:
    """
    便捷函数，无需创建 PromptSelector 实例即可获取 prompt。

    Args:
        workflow_type (str): 工作流类型
        node_name (str): 节点名称
        genre (str): genre 类型，默认为 "default"

    Returns:
        str: 请求的 prompt 模板
    """
    selector = PromptSelector()
    return selector.get_prompt(workflow_type, node_name, genre)

# service/src/doc_agent/tools/ai_editing_tool.py
"""
AI 编辑工具
用于处理文本编辑任务，包括润色、扩写、缩写等功能
"""

from collections.abc import AsyncGenerator

from doc_agent.core.logger import logger

from ..common.prompt_selector import PromptSelector
from ..llm_clients.base import LLMClient


class AIEditingTool:
    """
    AI 编辑工具类
    提供文本润色、扩写、缩写等功能
    支持同步和异步流式输出
    """

    def __init__(self, llm_client: LLMClient, prompt_selector: PromptSelector):
        """
        初始化 AI 编辑工具

        Args:
            llm_client: LLM 客户端实例
            prompt_selector: Prompt 选择器实例
        """
        self.llm_client = llm_client
        self.prompt_selector = prompt_selector
        self.logger = logger.bind(name="ai_editing_tool")

        # 定义有效的编辑操作
        self.valid_actions = [
            "polish", "expand", "summarize", "continue_writing", "custom"
        ]

        # 定义有效的润色风格
        self.valid_polish_styles = [
            "professional", "conversational", "readable", "subtle", "academic",
            "literary"
        ]

    def run(self, action: str, text: str, command: str = None) -> str:
        """
        执行文本编辑任务（同步版本）

        Args:
            action: 编辑操作类型 ("polish", "expand", "summarize", "custom")
            text: 要编辑的文本
            command: 自定义编辑指令（当 action 为 "custom" 时必填）

        Returns:
            str: 编辑后的文本

        Raises:
            ValueError: 当 action 无效时
            Exception: 当 LLM 调用失败时
        """
        try:
            # 验证 action 是否有效
            if action not in self.valid_actions:
                available_actions = ", ".join(self.valid_actions)
                error_msg = f"无效的编辑操作 '{action}'。可用操作: {available_actions}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 验证输入文本
            if not text or not text.strip():
                error_msg = "输入文本不能为空"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.info(f"开始执行 {action} 编辑任务，文本长度: {len(text)} 字符")

            # 获取对应的 Prompt 模板
            try:
                # 直接导入 ai_editor prompt 模块
                from ..prompts.ai_editor import PROMPTS
                prompt_template = PROMPTS.get(action)
                if not prompt_template:
                    available_actions = list(PROMPTS.keys())
                    raise ValueError(
                        f"未找到 action '{action}' 的 prompt 模板。可用 actions: {available_actions}"
                    )
                self.logger.debug(f"成功获取 {action} 的 prompt 模板")
            except Exception as e:
                error_msg = f"获取 prompt 模板失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

            # 格式化 Prompt
            try:
                if action == "custom":
                    if not command:
                        raise ValueError("自定义编辑操作需要提供 command 参数")
                    formatted_prompt = prompt_template.format(text=text,
                                                              command=command)
                else:
                    formatted_prompt = prompt_template.format(text=text)
                self.logger.debug(
                    f"Prompt 格式化完成，长度: {len(formatted_prompt)} 字符")
            except Exception as e:
                error_msg = f"Prompt 格式化失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

            # 调用 LLM 获取结果
            try:
                result = self.llm_client.invoke(formatted_prompt)
                self.logger.info(f"{action} 编辑任务完成，结果长度: {len(result)} 字符")
                return result
            except Exception as e:
                error_msg = f"LLM 调用失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

        except ValueError:
            # 重新抛出 ValueError，不需要额外处理
            raise
        except Exception as e:
            # 记录其他异常并重新抛出
            self.logger.error(f"AI 编辑工具执行失败: {e}")
            raise

    async def arun(self,
                   action: str,
                   text: str,
                   command: str = None,
                   context: str = None,
                   polish_style: str = None) -> AsyncGenerator[str, None]:
        """
        异步执行文本编辑任务（流式输出版本）

        Args:
            action: 编辑操作类型 ("polish", "expand", "summarize", "custom", "continue_writing")
            text: 要编辑的文本
            command: 自定义编辑指令（当 action 为 "custom" 时必填）
            context: 上下文信息（当 action 为 "continue_writing" 时使用）
            polish_style: 润色风格（当 action 为 "polish" 时必填）

        Yields:
            str: 编辑后的文本片段

        Raises:
            ValueError: 当 action 无效时
            Exception: 当 LLM 调用失败时
        """
        try:
            # 验证 action 是否有效
            if action not in self.valid_actions:
                available_actions = ", ".join(self.valid_actions)
                error_msg = f"无效的编辑操作 '{action}'。可用操作: {available_actions}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 验证输入文本
            if not text or not text.strip():
                error_msg = "输入文本不能为空"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.info(f"开始执行 {action} 编辑任务，文本长度: {len(text)} 字符")

            # 获取对应的 Prompt 模板
            try:
                # 直接导入 ai_editor prompt 模块
                from ..prompts.ai_editor import PROMPTS

                if action == "polish":
                    # 验证 polish_style 参数
                    if not polish_style:
                        raise ValueError("润色操作需要提供 polish_style 参数")
                    if polish_style not in self.valid_polish_styles:
                        available_styles = ", ".join(self.valid_polish_styles)
                        raise ValueError(
                            f"无效的润色风格 '{polish_style}'。可用风格: {available_styles}"
                        )

                    # 获取润色风格的 Prompt 字典
                    polish_prompts = PROMPTS.get("polish")
                    if not polish_prompts:
                        raise ValueError("未找到润色相关的 prompt 模板")

                    # 根据 polish_style 选择具体的 Prompt 模板
                    prompt_template = polish_prompts.get(polish_style)
                    if not prompt_template:
                        available_styles = list(polish_prompts.keys())
                        raise ValueError(
                            f"未找到润色风格 '{polish_style}' 的 prompt 模板。可用风格: {available_styles}"
                        )

                    self.logger.debug(
                        f"成功获取 {action} ({polish_style}) 的 prompt 模板")
                else:
                    # 对于其他 action，直接获取 Prompt 模板
                    prompt_template = PROMPTS.get(action)
                    if not prompt_template:
                        available_actions = list(PROMPTS.keys())
                        raise ValueError(
                            f"未找到 action '{action}' 的 prompt 模板。可用 actions: {available_actions}"
                        )
                    self.logger.debug(f"成功获取 {action} 的 prompt 模板")
            except Exception as e:
                error_msg = f"获取 prompt 模板失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

            # 格式化 Prompt
            try:
                if action == "custom":
                    if not command:
                        raise ValueError("自定义编辑操作需要提供 command 参数")
                    formatted_prompt = prompt_template.format(text=text,
                                                              command=command)
                elif action == "continue_writing":
                    # 续写功能不再要求 context 参数
                    if context:
                        formatted_prompt = prompt_template.format(
                            text=text, context=context)
                    else:
                        # 如果没有提供 context，使用不依赖上下文的续写 prompt
                        formatted_prompt = prompt_template.format(
                            text=text, context="无特定上下文信息")
                else:
                    formatted_prompt = prompt_template.format(text=text)
                self.logger.debug(
                    f"Prompt 格式化完成，长度: {len(formatted_prompt)} 字符")
            except Exception as e:
                error_msg = f"Prompt 格式化失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

            # 调用 LLM 获取流式结果
            try:
                async for token in self.llm_client.astream(formatted_prompt):
                    yield token
                self.logger.info(f"{action} 编辑任务完成")
            except Exception as e:
                error_msg = f"LLM 流式调用失败: {e}"
                self.logger.error(error_msg)
                raise Exception(error_msg) from e

        except ValueError:
            # 重新抛出 ValueError，不需要额外处理
            raise
        except Exception as e:
            # 记录其他异常并重新抛出
            self.logger.error(f"AI 编辑工具执行失败: {e}")
            raise

    def get_available_actions(self) -> list[str]:
        """
        获取可用的编辑操作列表

        Returns:
            list[str]: 可用的编辑操作列表
        """
        return self.valid_actions.copy()

    def validate_action(self, action: str) -> bool:
        """
        验证编辑操作是否有效

        Args:
            action: 要验证的编辑操作

        Returns:
            bool: 如果操作有效返回 True，否则返回 False
        """
        return action in self.valid_actions

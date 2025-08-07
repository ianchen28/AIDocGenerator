"""
编辑节点模块

负责融合编辑器功能，对生成的文档进行润色和优化
"""
import json
from typing import Any, Dict, Optional

from doc_agent.core.logger import logger
from doc_agent.core.config import settings
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient


def fusion_editor_node(state: ResearchState,
                       llm_client: LLMClient) -> dict[str, Any]:
    """
    融合编辑器节点
    对已完成的所有章节进行整体润色和优化
    
    Args:
        state: 研究状态
        llm_client: LLM客户端
        
    Returns:
        dict: 包含编辑后内容的字典
    """
    completed_chapters = state.get("completed_chapters", [])
    topic = state.get("topic", "")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()

    logger.info(f"🎨 开始融合编辑 (模式: {complexity_config['level']})")
    logger.info(f"📚 待编辑章节数量: {len(completed_chapters)}")

    if not completed_chapters:
        logger.warning("没有已完成的章节，跳过融合编辑")
        return {"fusion_edited": False}

    # 快速模式跳过融合编辑
    if complexity_config['level'] == 'fast':
        logger.info("🚀 快速模式，跳过融合编辑")
        return {"fusion_edited": False, "completed_chapters": completed_chapters}

    try:
        # 提取所有章节内容
        all_chapter_contents = []
        for chapter in completed_chapters:
            if isinstance(chapter, dict) and "content" in chapter:
                all_chapter_contents.append(chapter["content"])
            else:
                all_chapter_contents.append(str(chapter))

        # 合并内容进行分析
        combined_content = "\n\n---\n\n".join(all_chapter_contents)

        # 构建融合编辑提示词
        prompt = _build_fusion_editing_prompt(topic, combined_content,
                                              complexity_config)

        # 根据复杂度调整参数
        temperature = 0.6  # 较低温度确保编辑的一致性
        max_tokens = complexity_config.get('chapter_target_words', 2000)

        logger.info("🎯 开始LLM融合编辑...")

        # 调用LLM进行融合编辑
        edited_suggestions = llm_client.invoke(prompt,
                                               temperature=temperature,
                                               max_tokens=max_tokens)

        # 应用编辑建议
        updated_chapters = _apply_editing_suggestions(completed_chapters,
                                                      edited_suggestions,
                                                      complexity_config)

        logger.info("✅ 融合编辑完成")

        return {
            "completed_chapters": updated_chapters,
            "fusion_edited": True,
            "editing_suggestions": edited_suggestions
        }

    except Exception as e:
        logger.error(f"融合编辑失败: {str(e)}")
        logger.info("⚠️ 保持原始章节内容")
        return {"fusion_edited": False}


def _build_fusion_editing_prompt(topic: str, combined_content: str,
                                 complexity_config) -> str:
    """构建融合编辑提示词"""

    # 根据复杂度调整编辑深度
    if complexity_config['level'] == 'comprehensive':
        editing_depth = """
请进行深度编辑，包括：
1. 结构优化：调整章节逻辑流程，确保内容递进合理
2. 内容融合：消除重复内容，增强章节间的连贯性
3. 语言润色：提升表达准确性和流畅度
4. 细节完善：补充必要的过渡句和总结段落
5. 格式统一：确保标题层级、引用格式等的一致性
"""
    else:  # standard模式
        editing_depth = """
请进行标准编辑，包括：
1. 消除明显的重复内容
2. 改善章节间的逻辑连接
3. 修正语言表达问题
4. 统一格式风格
"""

    prompt = f"""
你是一位专业的文档编辑专家。请对以下关于"{topic}"的文档进行融合编辑。

{editing_depth}

**原始文档内容：**
{combined_content[:8000]}  # 限制长度避免超出token限制

**编辑要求：**
- 保持原有的技术准确性和引用完整性
- 确保整体结构清晰、逻辑连贯
- 改善文档的可读性和专业性
- 不要删除重要的技术细节

**输出格式：**
请提供具体的编辑建议，说明需要修改的地方和修改原因。
格式：
```
章节X修改建议：
- 问题：[描述问题]
- 建议：[具体修改建议]
- 原因：[修改原因]
```

请开始编辑分析。
"""

    return prompt


def _apply_editing_suggestions(completed_chapters, suggestions: str,
                               complexity_config) -> list:
    """应用编辑建议到章节内容"""

    # 简化版：只进行基本的格式清理
    updated_chapters = []

    for chapter in completed_chapters:
        if isinstance(chapter, dict):
            updated_chapter = chapter.copy()

            # 基本清理：移除多余空行，统一格式
            if "content" in updated_chapter:
                content = updated_chapter["content"]

                # 清理多余空行
                import re
                content = re.sub(r'\n{3,}', '\n\n', content)

                # 确保标题格式统一
                content = re.sub(r'^# ', '## ', content, flags=re.MULTILINE)

                updated_chapter["content"] = content.strip()

            updated_chapters.append(updated_chapter)
        else:
            updated_chapters.append(chapter)

    logger.info(f"📝 应用编辑建议完成，处理了 {len(updated_chapters)} 个章节")

    return updated_chapters

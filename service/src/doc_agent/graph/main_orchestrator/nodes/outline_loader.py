"""
大纲加载器节点模块

负责读取用户上传的大纲文件，并使用大模型将其转换为标准格式的大纲
"""

import json
import os
import tempfile

from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.schemas import Source
from doc_agent.tools.es_search import ESSearchTool
from doc_agent.tools.file_module import FileProcessor


async def outline_loader_node(state: ResearchState, llm_client: LLMClient,
                              es_search_tool: ESSearchTool) -> dict:
    """
    大纲加载器节点
    读取用户上传的大纲文件，使用大模型将其转换为标准格式的大纲
    
    Args:
        state: 研究状态
        llm_client: LLM客户端
        es_search_tool: ES搜索工具
        prompt_selector: 提示词选择器
        genre: 文档类型
        
    Returns:
        dict: 包含 document_outline 的字典
    """
    user_outline_file = state.get("user_outline_file", "")
    job_id = state.get("job_id", "")
    task_prompt = state.get("task_prompt", "")

    # 获取topic，如果没有则从task_prompt中提取
    topic = state.get("topic", "")
    word_count = state.get("word_count", -1)

    if not user_outline_file:
        raise ValueError("用户大纲文件token不能为空")

    # 如果没有topic，尝试从task_prompt中提取
    if not topic and task_prompt:
        logger.info("🔍 从task_prompt中提取topic...")
        prompt = f"""
你是一个专业的任务分析引擎。你的唯一目标是解析用户提供的文本，并从中提取关键的任务要求。

你必须严格遵循以下指令：
1.  分析文本，识别出任务的【主题】、【字数要求】和【其他要求】。
2.  你的输出必须是一个单一、有效的 JSON 对象，不能包含任何 JSON 格式之外的额外文本、解释或注释。
3.  严格按照下面的 schema 和字段规则生成 JSON：

```json
{{
    "topic": "任务的核心主题或标题。",
    "word_count": "从文本中提取明确的字数要求，只保留数字部分作为字符串。如果没有提到任何字数要求，则该字段的值必须是 '-1'。",
    "other_requirements": "除了主题和字数外的所有其他具体要求，例如格式、风格、需要包含的要点、受众等。如果没有，则该字段为空字符串 ''。"
}}
```

用户输入: {task_prompt}

开始输出 json：

"""
        try:
            response = llm_client.invoke(prompt)
            logger.info(f"🔍 任务分析响应: {response}")

            # 去除 ```json 和 ```
            response = response.replace("```json", "").replace("```", "")
            response_data = json.loads(response)
            topic = response_data.get("topic", "")
            extracted_word_count = response_data.get("word_count", "-1")
            other_requirements = response_data.get("other_requirements", "")

            if not topic:
                raise ValueError("从task_prompt中提取的主题为空")

            try:
                word_count = int(extracted_word_count)
            except ValueError:
                word_count = 5000  # 默认值
            if word_count < 0:
                word_count = 5000  # 默认值

            logger.info(f"✅ 成功提取topic: {topic}")
            logger.info(f"✅ 字数要求: {word_count}")
            logger.info(f"✅ 其他要求: {other_requirements}")

        except Exception as e:
            logger.warning(f"⚠️ 从task_prompt提取topic失败: {str(e)}")
            topic = "文档大纲生成"  # 默认主题
            word_count = 5000

    # 如果仍然没有topic，使用默认值
    if not topic:
        topic = "文档大纲生成"
        word_count = 5000

    logger.info(f"📋 开始加载用户大纲文件: {user_outline_file}")
    logger.info(f"主题: {topic}")

    try:
        # 1. 从ES中获取大纲文件内容
        logger.info(f"🔍 从ES中查询大纲文件内容...")
        es_results = await es_search_tool.search_by_file_token(
            file_token=user_outline_file,
            top_k=100  # 获取足够的内容
        )

        if not es_results:
            logger.error(f"❌ 未找到file_token为 {user_outline_file} 的文档")
            raise ValueError(f"未找到大纲文件: {user_outline_file}")

        # 2. 直接使用ES返回的内容
        logger.info(f"📄 找到 {len(es_results)} 个文档片段")

        if not es_results:
            logger.error("❌ 未找到大纲文件内容")
            raise ValueError("未找到大纲文件内容")

        # 直接使用第一个结果的content
        outline_content = es_results[0].original_content
        logger.info(f"📝 大纲文件内容长度: {len(outline_content)} 字符")
        logger.info(f"📝 大纲文件内容预览: {outline_content[:200]}...")

        # 4. 使用hardcode的提示词模板
        prompt_template = """你是一个专业的文档大纲分析专家。用户提供了一个大纲文件，你需要将其转换为标准的结构化大纲格式。

请分析用户提供的大纲文件内容，并生成一个符合以下JSON格式的标准大纲：

```json
{{
    "title": "文档标题",
    "summary": "文档的简短摘要（50-100字）",
    "chapters": [
        {{
            "number": 1,
            "title": "第一章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 1.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 1.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 2,
            "title": "第二章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 2.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 2.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "number": 3,
            "title": "第三章标题",
            "description": "本章的简要描述",
            "sections": [
                {{
                    "number": 3.1,
                    "title": "第一节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.2,
                    "title": "第二节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "number": 3.3,
                    "title": "第三节标题",
                    "description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }}
    ],
    "total_chapters": 3,
    "estimated_total_words": 5000
}}
```

要求：
1. 保持用户原始大纲的结构和逻辑
2. 确保章节和小节的层次关系清晰
3. 为每个章节和小节添加合适的描述
4. 每个章节必须包含3个子节，每个子节必须包含3个要点
5. 必须生成恰好3个章节
6. 章节编号从1开始，子节编号使用小数点格式（如1.1, 1.2, 1.3）
7. 目标总字数控制在5000字左右

用户主题：{topic}
用户大纲文件内容：
{outline_content}

请生成标准格式的大纲JSON："""

        # 5. 构建完整的提示词
        prompt = prompt_template.format(topic=topic,
                                        outline_content=outline_content)

        # 6. 调用LLM生成大纲
        logger.info("🤖 调用LLM分析大纲文件...")
        logger.info(f"📝 发送给LLM的prompt长度: {len(prompt)} 字符")
        logger.info(f"📝 发送给LLM的prompt前200字符: {prompt[:200]}...")

        try:
            # 使用invoke方法调用LLM
            logger.info("🔄 开始调用LLM...")
            logger.info(f"🔄 LLM客户端类型: {type(llm_client)}")
            logger.info(f"🔄 LLM客户端方法: {dir(llm_client)}")

            response = llm_client.invoke(prompt)
            logger.info("✅ LLM调用完成")

            if not response or not response.strip():
                logger.error("❌ LLM返回空响应")
                raise ValueError("LLM返回空响应")

            logger.info(f"📝 LLM原始响应长度: {len(response)} 字符")
            logger.info(f"📝 LLM原始响应前500字符: {repr(response[:500])}")
            logger.info(f"📝 LLM原始响应完整内容: {repr(response)}")

        except Exception as e:
            logger.error(f"❌ LLM调用失败: {e}", exc_info=True)
            raise ValueError(f"LLM调用失败: {e}") from e

        # 7. 解析JSON响应
        try:
            # 尝试直接解析JSON
            outline_data = json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            logger.warning("直接JSON解析失败，尝试提取JSON部分")
            import re

            # 尝试多种JSON提取模式
            json_patterns = [
                r'```json\s*(.*?)\s*```',  # ```json ... ```
                r'```\s*(.*?)\s*```',  # ``` ... ```
                r'\{.*\}',  # 任何JSON对象
            ]

            for pattern in json_patterns:
                json_match = re.search(pattern, response, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(
                            1) if pattern != r'\{.*\}' else json_match.group(0)
                        outline_data = json.loads(json_str)
                        logger.info(f"✅ 使用模式 {pattern} 成功解析JSON")
                        break
                    except json.JSONDecodeError:
                        continue
            else:
                logger.error(f"❌ 无法解析LLM响应为JSON: {response}")
                raise ValueError("无法解析LLM响应为JSON")

        # 8. 验证大纲格式
        if not isinstance(outline_data, dict):
            raise ValueError("大纲数据格式错误")

        if "title" not in outline_data or "chapters" not in outline_data:
            raise ValueError("大纲缺少必要字段")

        # 9. 将大纲保存为文件并上传到存储服务
        file_token = None
        try:
            # 初始化文件处理器
            file_processor = FileProcessor(
                storage_base_url="http://ai.test.hcece.net",
                app="hdec",
                app_secret="hdec_secret",
                tenant_id="100023")

            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w',
                                             suffix='.json',
                                             delete=False,
                                             encoding='utf-8') as temp_file:
                json.dump(outline_data,
                          temp_file,
                          ensure_ascii=False,
                          indent=2)
                temp_file_path = temp_file.name

            # 上传文件
            file_token = file_processor.upload_file(temp_file_path)
            logger.info(f"📁 大纲文件上传成功，Token: {file_token}")

            # 清理临时文件
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"大纲文件上传失败: {str(e)}")
            file_token = None

        # 10. 发布成功事件
        publish_event(
            job_id,
            "大纲生成",
            "outline_loader",
            "SUCCESS", {
                "outline": outline_data,
                "file_token": file_token,
                "description":
                f"成功加载并解析用户大纲文件，包含 {len(outline_data.get('chapters', []))} 个章节",
                "chapters_count": len(outline_data.get("chapters", [])),
                "title": outline_data.get("title", "")
            },
            task_finished=True)

        logger.success(
            f"✅ 大纲加载完成，生成 {len(outline_data.get('chapters', []))} 个章节")

        return {
            "document_outline": outline_data,
            "initial_sources": [],  # 用户上传的大纲文件，不需要额外的源
            "outline_source": "user_upload"  # 标记大纲来源
        }

    except Exception as e:
        logger.error(f"❌ 大纲加载失败: {e}", exc_info=True)
        publish_event(job_id,
                      "大纲加载",
                      "outline_loader",
                      "ERROR", {"description": f"大纲加载失败: {str(e)}"},
                      task_finished=True)
        raise

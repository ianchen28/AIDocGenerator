"""
生成节点模块

负责大纲生成、章节拆分、参考文献生成等功能
"""

import json
import os
import tempfile

from doc_agent.common.prompt_selector import PromptSelector
from doc_agent.core.config import settings
from doc_agent.core.logger import logger
from doc_agent.graph.callbacks import publish_event
from doc_agent.graph.common import format_sources_to_text
from doc_agent.graph.state import ResearchState
from doc_agent.llm_clients.base import LLMClient
from doc_agent.schemas import Source
from doc_agent.tools.file_module import FileProcessor


def outline_generation_node(state: ResearchState,
                            llm_client: LLMClient,
                            prompt_selector: PromptSelector = None,
                            genre: str = "default") -> dict:
    """
    大纲生成节点 - 统一版本
    根据初始研究数据生成文档大纲
    支持基于配置的行为调整

    Args:
        state: 研究状态
        llm_client: LLM客户端
        prompt_selector: 提示词选择器
        genre: 文档类型

    Returns:
        dict: 包含 document_outline 的字典
    """
    topic = state.get("topic", "")
    initial_sources = state.get("initial_sources", [])
    job_id = state.get("job_id", "")

    if not topic:
        raise ValueError("主题不能为空")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    logger.info(f"📋 开始生成大纲 (模式: {complexity_config['level']}): {topic}")

    # 格式化数据
    if initial_sources:
        initial_gathered_data = format_sources_to_text(initial_sources)
    else:
        initial_gathered_data = state.get("initial_gathered_data", "")

    if not initial_gathered_data:
        logger.warning("没有初始研究数据，使用默认大纲")
        return _generate_default_outline(topic, complexity_config)

    # 获取提示词模板
    prompt_template = _get_outline_prompt_template(complexity_config,
                                                   prompt_selector, genre)

    # 构建提示词
    prompt = prompt_template.format(
        topic=topic,
        initial_gathered_data=initial_gathered_data[:5000]  # 限制长度
    )

    try:
        # 根据复杂度调整参数
        temperature = 0.7
        max_tokens = 2000

        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens)

        # 解析响应
        outline = _parse_outline_response(response, complexity_config)

        logger.info(
            f"✅ Job {job_id} 大纲生成完成，包含 {len(outline.get('chapters', []))} 个章节")

        # 将大纲保存为文件并上传到存储服务
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
                json.dump(outline, temp_file, ensure_ascii=False, indent=2)
                temp_file_path = temp_file.name

            # 上传文件
            file_token = file_processor.upload_file(temp_file_path)
            logger.info(f"📁 大纲文件上传成功，Token: {file_token}")

            # 清理临时文件
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"大纲文件上传失败: {str(e)}")
            file_token = None

        publish_event(
            job_id,
            "大纲生成",
            "outline_generation",
            "SUCCESS", {
                "outline": outline,
                "file_token": file_token,
                "description":
                f"大纲生成完成，包含 {len(outline.get('chapters', []))} 个章节"
            },
            task_finished=True)

        return {"document_outline": outline}

    except Exception as e:
        logger.error(f"大纲生成失败: {str(e)}")
        return _generate_default_outline(topic, complexity_config)


def split_chapters_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    章节拆分节点 - 统一版本
    将文档大纲拆分为独立的章节任务列表
    根据配置限制章节数量
    """

    document_outline = state.get("document_outline", {})

    if not document_outline or "chapters" not in document_outline:
        raise ValueError("文档大纲不存在或格式无效")

    # 获取复杂度配置
    complexity_config = settings.get_complexity_config()
    max_chapters = complexity_config.get('max_chapters', -1)

    chapters_to_process = []
    chapters = document_outline['chapters']

    # 限制章节数量
    if max_chapters > 0:
        chapters = chapters[:max_chapters]

    publish_event(
        state.get("job_id", ""), "大纲解析", "document_generation", "RUNNING", {
            "description": "开始解析现有大纲...",
            "documentTitle": document_outline.get("title", "")
        })

    for chapter in chapters:
        # 兼容新旧格式
        chapter_title = chapter.get('title', chapter.get('chapter_title', ''))
        chapter_number = chapter.get('number',
                                     chapter.get('chapter_number', 0))
        description = chapter.get('description', '')

        # 兼容新旧格式：sections vs sub_sections
        sections = chapter.get('sections', chapter.get('sub_sections', []))

        # 转换子节格式
        sub_sections = []
        for section in sections:
            # 兼容新旧格式
            section_title = section.get('title',
                                        section.get('section_title', ''))
            section_number = section.get('number',
                                         section.get('section_number', 0))
            section_description = section.get(
                'description', section.get('section_description', ''))
            key_points = section.get('key_points', [])

            sub_sections.append({
                "section_number": section_number,
                "section_title": section_title,
                "section_description": section_description,
                "key_points": key_points
            })

        chapters_to_process.append({
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "description": description,
            "key_points": [],
            "estimated_sections": len(sub_sections),
            "sub_sections": sub_sections,
            "research_data": ""
        })

    # 获取一句话研究计划告知
    plan_prompt1 = """
你是一位经验丰富的总编辑和写作规划师。

你的任务是根据用户提供的文章标题、任务要求、文章大纲和总字数，制定一个清晰的章节写作计划。
**输入内容**
- 【文章标题】
- 【任务要求】
- 【文章大纲】
- 【全文字数】

**核心指令:**

1.  **生成任务概述 (Overview)**: 结合【文章标题】和【任务要求】，用一句话精炼地总结出本次写作任务的核心目标以及你计划要做的事情。
2.  **分配章节字数 (Allocate Word Count)**:
    * **智能加权分配**: 你必须将【全文字数】智能地分配到【文章大纲】的每一个主要章节（通常是二级标题）。**切勿平均分配**。
    * **分配依据**: 分配字数时，必须综合考虑以下因素：
        * **内容重要性**: 大纲中包含更多子要点、描述更详细、或与【任务要求】直接相关的核心章节，应分配更多字数。
        * **章节类型**: 通常，“引言”和“结论”部分占比较小（例如，各自占总字数的 10-15%），而主体分析、论证章节占比较大。
    * **数学约束**: 所有 `chapter_word_counts` 列表中的 `word_count` 之和，**必须严格等于**【全文字数】。这是一个硬性要求。
3.  **格式化输出**: 你的输出必须是一个单一、有效的 JSON 对象。除了这个 JSON 对象，不要返回任何额外的解释、注释或文字。

**JSON 输出格式:**
```json
{
  "overview": "一句话总结一下要完成任务要做的事情。",
  "chapter_word_counts": [
    {
      "title": "章节标题",
      "word_count": "分配给该章节的字数（数字）"
    }
  ]
}

示例学习：

输入：
- 【文章标题】: "人工智能在教育领域的应用与挑战"
- 【任务要求】: "帮我写一篇 5000 字的深度研究报告来研究人工智能在教育领域的应用进展，需要有具体的案例分析，并对未来的发展趋势提出自己的看法。"
- 【文章大纲】:
{'title': '人工智能技术发展趋势', 'word_count': 0, 'chapters': [{'number': 1, 'title': '人工智能技术概述', 'description': '介绍人工智能的基本概念、发展历程和当前技术现状，为后续章节的深入分析奠定基础。', 'sections': [{'number': 1.1, 'title': '人工智能的基本概念', 'description': '定义人工智能，介绍其核心技术和工作原理。', 'key_points': ['人工智能的定义', '核心技术和工作原理', '与相关领域的联系']}, {'number': 1.2, 'title': '人工智能的发展历程', 'description': '回顾人工智能从诞生到现在的关键发展阶段，分析各阶段的主要成就和挑战。', 'key_points': ['20世纪50年代的兴起与冷落', '20世纪60年代末到70年代的专家系统', '21世纪的快速发展']}, {'number': 1.3, 'title': '当前技术现状', 'description': '概述当前人工智能技术的主要特点和发展水平，探讨其在全球范围内的应用情况。', 'key_points': ['技术特点概述', '全球应用情况', '主要挑战与机遇']}]}, {'number': 2, 'title': '机器学习与深度学习', 'description': '深入探讨机器学习和深度学习的基本理论、技术特点及其在实际应用中的表现。', 'sections': [{'number': 2.1, 'title': '机器学习的基础理论', 'description': '介绍机器学习的基本原理、主要算法和应用场景。', 'key_points': ['机器学习的定义与原理', '主要算法类型', '典型应用场景']}, {'number': 2.2, 'title': '深度学习的技术特点', 'description': '探讨深度学习的技术特点、架构和优势，分析其在图像识别、自然语言处理等领域的应用。', 'key_points': ['深度学习的定义与特点', '多层神经网络架构', '应用案例分析']}, {'number': 2.3, 'title': '机器学习与深度学习的对比', 'description': '对比分析机器学习和深度学习的主要异同，探讨其在不同应用场景中的选择策略。', 'key_points': ['技术上的异同点', '应用场景的差异', '选择策略与未来趋势']}]}]}

- 【全文字数】: 5000

输出：
{
  "overview": "我将为您撰写一篇文章来分析人工智能技术的发展趋势，包括基本概念、发展历程、技术现状、机器学习与深度学习、应用场景等，为后续章节的深入分析奠定基础。",
  "chapter_word_counts": [
    {
      "title": "人工智能技术概述",
      "word_count": 2500
    },
    {
      "title": "机器学习与深度学习",
      "word_count": 2500
    }
  ]
}

"""

    plan_prompt_template2 = """
任务开始
请根据下面的输入，生成写作计划，并输出json格式

输入：
- 【文章标题】：{topic}
- 【任务要求】: {task_prompt}
- 【文章大纲】: {document_outline_str}
- 【全文字数】: {word_count}

输出：
"""
    logger.info(f"outline_from_fe: {document_outline}")
    plan_prompt2 = plan_prompt_template2.format(
        topic=state.get("topic", ""),
        task_prompt=state.get("task_prompt", ""),
        document_outline_str=json.dumps(document_outline, ensure_ascii=False),
        word_count=state.get("word_count", 0))

    plan_prompt = plan_prompt1 + plan_prompt2
    response = llm_client.invoke(plan_prompt, temperature=0.5, max_tokens=2000)

    # 删除 ```json 和 ```
    response = response.replace("```json", "").replace("```", "")

    logger.info(f"plan_prompt: {plan_prompt}")
    logger.info(f"response: {response}")
    try:
        plan_json = json.loads(response)
    except Exception as e:
        logger.error(f"解析计划失败: {e}")
        plan_json = None
    plan_str = plan_json.get("overview", "")

    logger.info(f"一句话研究计划：{plan_str}")

    publish_event(state.get("job_id", ""), "一句话研究计划", "document_generation",
                  "SUCCESS", {"description": plan_str})

    chapter_word_counts = plan_json.get("chapter_word_counts", [])
    if len(chapter_word_counts) != len(chapters_to_process):
        logger.error(
            f"章节字数分配不一致，章节数不一致, {len(chapter_word_counts)} != {len(chapters_to_process)}"
        )
        chapter_word_counts = [{
            "title":
            chapter["chapter_title"],
            "word_count":
            int(state.get("word_count", 0) / len(chapters_to_process))
        } for chapter in chapters_to_process]
    else:
        for (word_count, chapter) in zip(chapter_word_counts,
                                         chapters_to_process):
            chapter["chapter_word_count"] = word_count.get("word_count", 0)

    logger.info(f"✅ 章节拆分完成，共 {len(chapters_to_process)} 个章节")
    publish_event(
        state.get("job_id", ""), "大纲解析", "document_generation", "SUCCESS", {
            "chapters": chapters_to_process,
            "description": f"大纲解析完成，共需编写{len(chapters_to_process)}个章节"
        })

    for i, chapter in enumerate(chapters_to_process):
        logger.info(
            f"  📖 第{i+1}章: {chapter['chapter_title']} ({len(chapter['sub_sections'])} 子节)"
        )

    return {
        "chapters_to_process": chapters_to_process,
        "current_chapter_index": 0,
        "completed_chapters": [],
        "user_data_reference_files": state.get("user_data_reference_files",
                                               []),
        "user_style_guide_content": state.get("user_style_guide_content", []),
        "user_requirements_content": state.get("user_requirements_content", [])
    }


def bibliography_node(state: ResearchState) -> dict:
    """
    参考文献生成节点
    根据全局引用源生成参考文献列表
    """
    cited_sources = state.get("cited_sources", [])  # 🔧 修复：改为列表而不是字典

    logger.info(f"📚 开始生成参考文献，共 {len(cited_sources)} 个引用源")

    # 使用新的 Source 类方法进行批量转换
    answer_origins, webs = Source.batch_to_redis_fe(cited_sources)

    publish_event(
        state.get("job_id", ""), "参考文献生成", "document_generation", "RUNNING", {
            "answerOrigins": answer_origins,
            "webs": webs,
            "description": f"开始生成参考文献，共 {len(cited_sources)} 个引用源"
        })

    if not cited_sources:
        logger.warning("没有引用源，生成空的参考文献")
        bibliography = "\n## 参考文献\n\n暂无参考文献。\n"
    else:
        # 生成参考文献
        bibliography_lines = ["\n## 参考文献\n"]

        # 🔧 修复：使用 source.id 作为引用编号，保持与文档内容一致
        for source in cited_sources:
            citation = _format_citation(source.id, source)
            bibliography_lines.append(citation)

        bibliography = "\n".join(bibliography_lines)

        logger.info(f"✅ 参考文献生成完成，包含 {len(cited_sources)} 条引用")

    # 获取现有的 final_document
    final_document = state.get("final_document", "")

    # 将参考文献添加到最终文档中
    updated_final_document = final_document + bibliography

    logger.info(f"📚 已将参考文献添加到最终文档中，总长度: {len(updated_final_document)} 字符")

    # 保存文档到本地文件
    try:
        import os
        from datetime import datetime

        # 创建输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = state.get("document_outline", {}).get("title", "未命名文档")
        # 清理文件名中的特殊字符
        safe_title = "".join(c for c in title
                             if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{timestamp}_{safe_title}.md"
        filepath = os.path.join(output_dir, filename)

        # 保存文档
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_final_document)

        logger.info(f"💾 文档已保存到本地: {filepath}")

    except Exception as e:
        logger.error(f"保存文档失败: {e}")

    # 返回更新后的 final_document
    return {"final_document": updated_final_document}


def _get_outline_prompt_template(complexity_config, prompt_selector, genre):
    """获取大纲生成的提示词模板"""
    try:
        if complexity_config['use_simplified_prompts']:
            # 快速模式使用简化提示词 - 现在从prompts模块获取
            from doc_agent.prompts.outline_generation import V4_FAST
            return V4_FAST

        # 标准模式使用完整提示词
        if prompt_selector:
            # 优先使用三级大纲结构版本
            try:
                return prompt_selector.get_prompt("main_orchestrator",
                                                  "outline",
                                                  "v3_with_subsections")
            except Exception:
                # 如果三级版本不可用，使用默认版本
                return prompt_selector.get_prompt("main_orchestrator",
                                                  "outline", genre)

    except Exception as e:
        logger.error("获取提示词模板失败: {}", e)

    # 备用模板 - 使用三级大纲结构
    return """
你是一位专业的文档结构设计专家。基于提供的初始研究数据，为主题生成一个详细的文档大纲。

**文档主题:** {topic}

**研究数据摘要:**
{initial_gathered_data}

**任务要求:**
1. 分析研究数据，识别主要主题
2. 创建一个完整的文档结构
3. 每个章节应该有明确的焦点
4. 确保覆盖主题的核心要点
5. **必须生成三级大纲结构**：章节 -> 子节 -> 要点

**输出格式要求:**
请严格按照以下JSON格式输出，不要包含任何其他内容：

{{
    "title": "文档标题",
    "summary": "文档的简短摘要（50-100字）",
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "第一章标题",
            "description": "本章的简要描述",
            "sub_sections": [
                {{
                    "section_number": 1.1,
                    "section_title": "第一节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 1.2,
                    "section_title": "第二节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 1.3,
                    "section_title": "第三节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "chapter_number": 2,
            "chapter_title": "第二章标题",
            "description": "本章的简要描述",
            "sub_sections": [
                {{
                    "section_number": 2.1,
                    "section_title": "第一节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 2.2,
                    "section_title": "第二节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 2.3,
                    "section_title": "第三节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }},
        {{
            "chapter_number": 3,
            "chapter_title": "第三章标题",
            "description": "本章的简要描述",
            "sub_sections": [
                {{
                    "section_number": 3.1,
                    "section_title": "第一节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 3.2,
                    "section_title": "第二节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }},
                {{
                    "section_number": 3.3,
                    "section_title": "第三节标题",
                    "section_description": "本节的简要描述",
                    "key_points": ["要点1", "要点2", "要点3"]
                }}
            ]
        }}
    ],
    "total_chapters": 3,
    "estimated_total_words": 5000
}}

**重要提示:**
- **必须生成恰好3个章节**
- **每个章节必须包含3个子节**
- **每个子节必须包含3个要点**
- 要生成完整的三级大纲结构
- 章节标题应该简洁明了
- 描述应该简短但清晰
- 必须输出有效的JSON格式
- 目标总字数控制在5000字左右
"""


def _parse_outline_response(response: str, complexity_config) -> dict:
    """解析大纲生成响应"""
    # 清除收尾的 ```json 和 ```
    response = response.replace('```json', '').replace('```', '').strip()

    try:
        # 尝试解析JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            outline = json.loads(json_match.group(0))

            # 验证和修复大纲结构
            outline = _validate_and_fix_outline_structure(
                outline, complexity_config)

            # 根据复杂度限制章节数量
            max_chapters = complexity_config.get('max_chapters', -1)
            if max_chapters > 0 and 'chapters' in outline:
                outline['chapters'] = outline['chapters'][:max_chapters]

            return outline
    except Exception as e:
        logger.error(f"解析大纲响应失败: {e}")

    # 返回默认大纲
    return _generate_default_outline("未知主题", complexity_config)


def _validate_and_fix_outline_structure(outline: dict,
                                        complexity_config: dict) -> dict:
    """验证和修复大纲结构，确保三级结构完整，支持新旧格式"""

    if 'chapters' not in outline:
        logger.warning("大纲缺少chapters字段，使用默认大纲")
        return _generate_default_outline("未知主题", complexity_config)

    chapters = outline['chapters']
    fixed_chapters = []

    for i, chapter in enumerate(chapters):
        # 兼容新旧格式：chapter_title -> title
        if 'title' not in chapter and 'chapter_title' in chapter:
            chapter['title'] = chapter['chapter_title']
        elif 'title' not in chapter:
            chapter['title'] = f"第{i+1}章"

        # 兼容新旧格式：chapter_number -> number
        if 'number' not in chapter and 'chapter_number' in chapter:
            chapter['number'] = chapter['chapter_number']
        elif 'number' not in chapter:
            chapter['number'] = i + 1

        if 'description' not in chapter:
            chapter['description'] = f"第{i+1}章的内容描述"

        # 兼容新旧格式：sections -> sub_sections
        sections_key = 'sections' if 'sections' in chapter else 'sub_sections'
        if sections_key not in chapter or not chapter[sections_key]:
            logger.info(f"章节 {chapter['title']} 缺少子节，添加默认子节")
            chapter[sections_key] = [{
                "number": float(f"{i+1}.1"),
                "title": f"{chapter['title']}概述",
                "description": f"{chapter['title']}的基本概述",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "number": float(f"{i+1}.2"),
                "title": f"{chapter['title']}分析",
                "description": f"{chapter['title']}的深入分析",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "number": float(f"{i+1}.3"),
                "title": f"{chapter['title']}总结",
                "description": f"{chapter['title']}的总结和展望",
                "key_points": ["要点1", "要点2", "要点3"]
            }]
        else:
            # 验证子节结构，兼容新旧格式
            for j, section in enumerate(chapter[sections_key]):
                # 兼容新旧格式：section_title -> title
                if 'title' not in section and 'section_title' in section:
                    section['title'] = section['section_title']
                elif 'title' not in section:
                    section['title'] = f"第{i+1}.{j+1}节"

                # 兼容新旧格式：section_description -> description
                if 'description' not in section and 'section_description' in section:
                    section['description'] = section['section_description']
                elif 'description' not in section:
                    section['description'] = f"第{i+1}.{j+1}节的描述"

                # 兼容新旧格式：section_number -> number
                if 'number' not in section and 'section_number' in section:
                    section['number'] = section['section_number']
                elif 'number' not in section:
                    section['number'] = float(f"{i+1}.{j+1}")

                if 'key_points' not in section or not section['key_points']:
                    section['key_points'] = ["要点1", "要点2", "要点3"]

        # 统一使用新格式
        if 'sections' not in chapter and sections_key in chapter:
            chapter['sections'] = chapter[sections_key]
            del chapter[sections_key]

        fixed_chapters.append(chapter)

    # 确保至少有3个章节
    while len(fixed_chapters) < 3:
        chapter_num = len(fixed_chapters) + 1
        fixed_chapters.append({
            "number":
            chapter_num,
            "title":
            f"第{chapter_num}章",
            "description":
            f"第{chapter_num}章的内容描述",
            "sections": [{
                "number": float(f"{chapter_num}.1"),
                "title": f"第{chapter_num}章概述",
                "description": f"第{chapter_num}章的基本概述",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "number": float(f"{chapter_num}.2"),
                "title": f"第{chapter_num}章分析",
                "description": f"第{chapter_num}章的深入分析",
                "key_points": ["要点1", "要点2", "要点3"]
            }, {
                "number": float(f"{chapter_num}.3"),
                "title": f"第{chapter_num}章总结",
                "description": f"第{chapter_num}章的总结和展望",
                "key_points": ["要点1", "要点2", "要点3"]
            }]
        })

    outline['chapters'] = fixed_chapters
    logger.info(f"✅ 大纲结构验证完成， 包含 {len(fixed_chapters)} 个章节，每个章节包含子节")

    return outline


def _generate_default_outline(topic: str, complexity_config) -> dict:
    """生成默认大纲"""
    max_chapters = complexity_config.get('max_chapters', 3)
    if max_chapters <= 0:
        max_chapters = 3

    # 根据主题生成通用大纲
    chapters = []
    for i in range(min(max_chapters, 3)):
        chapters.append({
            "number":
            i + 1,
            "title":
            f"{topic} - 第{i + 1}部分",
            "description":
            f"关于{topic}的第{i + 1}部分内容",
            "sections": [{
                "number":
                float(f"{i+1}.1"),
                "title":
                f"第{i+1}部分概述",
                "description":
                f"第{i+1}部分的基本概述",
                "key_points":
                [f"{topic}概述要点1", f"{topic}概述要点2", f"{topic}概述要点3"]
            }, {
                "number":
                float(f"{i+1}.2"),
                "title":
                f"第{i+1}部分分析",
                "description":
                f"第{i+1}部分的深入分析",
                "key_points":
                [f"{topic}分析要点1", f"{topic}分析要点2", f"{topic}分析要点3"]
            }, {
                "number":
                float(f"{i+1}.3"),
                "title":
                f"第{i+1}部分总结",
                "description":
                f"第{i+1}部分的总结和展望",
                "key_points":
                [f"{topic}总结要点1", f"{topic}总结要点2", f"{topic}总结要点3"]
            }]
        })

    return {
        "title": f"{topic} 研究报告",
        "summary": f"本文档深入探讨了{topic}的相关内容，包括问题分析和解决方案。",
        "chapters": chapters[:max_chapters]  # 确保不超过最大章节数
    }


def _format_citation(source_id: int, source: Source) -> str:
    """格式化单个引用"""
    citation = f"[{source_id}] {source.title}"

    # 添加作者信息
    if source.author:
        citation += f", {source.author}"

    # 添加日期信息
    if source.date:
        citation += f", {source.date}"

    # 添加URL信息
    if source.url:
        citation += f" - {source.url}"

    # 添加页码信息
    if source.page_number is not None:
        citation += f" (第{source.page_number}页)"

    citation += f" ({source.source_type})"

    return citation

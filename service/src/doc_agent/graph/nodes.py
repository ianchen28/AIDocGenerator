# service/src/doc_agent/graph/nodes.py
from .state import ResearchState
from ..llm_clients.base import LLMClient
from ..tools.web_search import WebSearchTool
from ..tools.es_search import ESSearchTool
from ..llm_clients.providers import EmbeddingClient

# 添加配置导入
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = None
for parent in current_file.parents:
    if parent.name == 'service':
        service_dir = parent
        break

if service_dir and str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from core.config import settings

# 修复相对导入
try:
    from ..utils import parse_planner_response
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from src.doc_agent.utils import parse_planner_response
    except ImportError:
        # 如果都失败，创建一个简单的解析函数
        def parse_planner_response(response):
            """简单的响应解析函数"""
            import json
            try:
                data = json.loads(response)
                return data.get("research_plan",
                                ""), data.get("search_queries", [])
            except:
                return "默认研究计划", ["默认搜索查询"]


def planner_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    节点1: 规划研究步骤
    
    从状态中获取 topic，创建 prompt 调用 LLM 生成研究计划和搜索查询
    
    Args:
        state: 研究状态，包含 topic
        llm_client: LLM客户端实例
        
    Returns:
        dict: 包含 research_plan 和 search_queries 的字典
    """
    topic = state.get("topic", "")
    if not topic:
        raise ValueError("Topic is required in state")

    # 获取任务规划器配置
    task_planner_config = settings.get_agent_component_config("task_planner")
    if not task_planner_config:
        raise ValueError("Task planner configuration not found")

    # 创建研究计划生成的 prompt，要求 JSON 格式响应
    prompt = f"""
你是一个专业的研究规划专家。请为以下主题制定详细的研究计划和搜索策略。

主题: {topic}

请严格按照以下 JSON 格式输出，不要包含任何其他内容：

{{
    "research_plan": "详细的研究计划，包括：1. 需要了解的核心概念 2. 需要收集的信息类型 3. 研究的时间安排 4. 可能遇到的挑战和解决方案",
    "search_queries": ["具体的搜索查询1", "具体的搜索查询2", "具体的搜索查询3", "具体的搜索查询4", "具体的搜索查询5"]
}}

要求：
1. research_plan 应该是一个详细的步骤计划，包含具体的研究步骤和策略
2. search_queries 应该包含3-5个具体的搜索查询，每个查询要针对性强且覆盖主题的不同方面
3. 必须严格按照 JSON 格式输出，确保 JSON 格式正确
4. 搜索查询应该使用通用关键词，避免过于具体的术语，确保能在知识库中找到相关内容
5. 搜索查询应该包含主题的核心词汇，比如"水电站"、"电力"、"能源"等通用术语
"""

    try:
        # 调用 LLM 生成研究计划
        response = llm_client.invoke(
            prompt,
            temperature=task_planner_config.temperature,
            max_tokens=task_planner_config.max_tokens,
            **task_planner_config.extra_params)

        # 解析 JSON 响应
        research_plan, search_queries = parse_planner_response(response)

        return {
            "research_plan": research_plan,
            "search_queries": search_queries
        }

    except Exception as e:
        # 如果 LLM 调用失败，返回默认计划
        print(f"Planner node error: {str(e)}")
        return {
            "research_plan": f"默认研究计划：对主题 '{topic}' 进行深入研究，收集相关信息并整理成文档。",
            "search_queries":
            [f"{topic} 介绍", f"{topic} 最新发展", f"{topic} 应用案例"]
        }


def researcher_node(state: ResearchState,
                    web_search_tool: WebSearchTool) -> dict:
    raise NotImplementedError("请使用 async_researcher_node")


async def async_researcher_node(state: ResearchState,
                                web_search_tool: WebSearchTool) -> dict:
    """
    异步节点2: 执行搜索研究
    
    从状态中获取 search_queries，使用搜索工具收集相关信息
    优先使用向量检索，如果失败则回退到文本搜索
    
    Args:
        state: 研究状态，包含 search_queries
        web_search_tool: 网络搜索工具
        
    Returns:
        dict: 包含 gathered_data 的字典
    """
    search_queries = state.get("search_queries", [])
    if not search_queries:
        return {"gathered_data": "没有搜索查询需要执行"}

    all_results = []

    # 获取embedding配置
    embedding_config = settings.supported_models.get("gte_qwen")
    embedding_client = None
    if embedding_config:
        try:
            embedding_client = EmbeddingClient(
                base_url=embedding_config.url,
                api_key=embedding_config.api_key)
            print("✅ Embedding客户端初始化成功")
        except Exception as e:
            print(f"⚠️  Embedding客户端初始化失败: {str(e)}")
            embedding_client = None
    else:
        print("❌ 未找到 embedding 配置，将使用文本搜索")

    # 用配置初始化ES工具
    es_config = settings.elasticsearch_config
    async with ESSearchTool(hosts=es_config.hosts,
                            username=es_config.username,
                            password=es_config.password,
                            index_prefix=es_config.index_prefix,
                            timeout=es_config.timeout) as es_search_tool:

        for i, query in enumerate(search_queries, 1):
            print(f"执行搜索查询 {i}/{len(search_queries)}: {query}")

            # 网络搜索
            web_results = ""
            try:
                web_results = web_search_tool.search(query)
                if "模拟" in web_results or "mock" in web_results.lower():
                    print(f"网络搜索返回模拟结果，跳过: {query}")
                    web_results = ""
            except Exception as e:
                print(f"网络搜索失败: {str(e)}")
                web_results = ""

            # ES搜索 - 优先向量检索，失败则回退到文本搜索
            es_results = ""
            try:
                if embedding_client:
                    # 尝试向量检索
                    try:
                        embedding_response = embedding_client.invoke(query)
                        import json
                        try:
                            embedding_data = json.loads(embedding_response)
                            if isinstance(embedding_data, list):
                                if len(embedding_data) > 0 and isinstance(
                                        embedding_data[0], list):
                                    query_vector = embedding_data[0]
                                else:
                                    query_vector = embedding_data
                            elif isinstance(embedding_data,
                                            dict) and 'data' in embedding_data:
                                query_vector = embedding_data['data']
                            else:
                                print(
                                    f"⚠️  无法解析embedding响应格式: {type(embedding_data)}"
                                )
                                query_vector = None
                        except json.JSONDecodeError:
                            print(f"⚠️  JSON解析失败，使用文本搜索")
                            query_vector = None

                        if query_vector and len(query_vector) == 1536:
                            print(
                                f"✅ 向量维度: {len(query_vector)}，前5: {query_vector[:5]}"
                            )
                            # 使用新的 search 方法，传入正确的参数
                            # 如果 query 为空，使用默认查询字符串
                            search_query = query if query.strip() else "相关文档"
                            es_results = await es_search_tool.search(
                                query=search_query,
                                query_vector=query_vector,
                                top_k=3)
                            print(f"✅ 向量检索执行成功，结果长度: {len(es_results)}")
                        else:
                            print(f"❌ 向量生成失败，使用文本搜索")
                            # 回退到文本搜索
                            es_results = await es_search_tool.search(
                                query=query, query_vector=None, top_k=3)
                            print(f"✅ 文本搜索执行成功，结果长度: {len(es_results)}")
                    except Exception as e:
                        print(f"❌ 向量检索异常: {str(e)}，使用文本搜索")
                        # 回退到文本搜索
                        es_results = await es_search_tool.search(
                            query=query, query_vector=None, top_k=3)
                        print(f"✅ 文本搜索执行成功，结果长度: {len(es_results)}")
                else:
                    # 没有embedding客户端，直接使用文本搜索
                    print("📝 使用文本搜索")
                    es_results = await es_search_tool.search(query=query,
                                                             query_vector=None,
                                                             top_k=3)
                    print(f"✅ 文本搜索执行成功，结果长度: {len(es_results)}")

            except Exception as e:
                print(f"❌ ES搜索失败: {str(e)}")
                es_results = f"ES搜索失败: {str(e)}"

            # 聚合结果
            query_results = f"=== 搜索查询 {i}: {query} ===\n\n"
            if web_results:
                query_results += f"网络搜索结果:\n{web_results}\n\n"
            if es_results:
                query_results += f"知识库搜索结果:\n{es_results}\n\n"
            if not web_results and not es_results:
                query_results += "未找到相关搜索结果\n\n"
            all_results.append(query_results)

    # 合并所有搜索结果
    if all_results:
        gathered_data = "\\n\\n".join(all_results)
        print(f"✅ 收集到 {len(all_results)} 条搜索结果")
        print(f"📊 总数据长度: {len(gathered_data)} 字符")
        # 只显示前200字符作为预览，避免日志过长
        preview = gathered_data[:200] + "..." if len(
            gathered_data) > 200 else gathered_data
        print(f"📝 数据预览: {preview}")
    else:
        gathered_data = "未收集到任何搜索结果"
        print("❌ 未收集到任何搜索结果")

    return {"gathered_data": gathered_data}


def writer_node(state: ResearchState, llm_client: LLMClient) -> dict:
    """
    节点3: 撰写文档
    
    基于收集的研究数据和计划，生成高质量的最终文档
    
    Args:
        state: 研究状态，包含 topic, research_plan, gathered_data
        llm_client: LLM客户端实例
        
    Returns:
        dict: 包含 final_document 的字典
    """
    topic = state.get("topic", "")
    research_plan = state.get("research_plan", "")
    gathered_data = state.get("gathered_data", "")

    if not topic:
        raise ValueError("Topic is required in state")

    if not gathered_data:
        return {"final_document": f"# {topic}\n\n由于没有收集到相关数据，无法生成完整文档。"}

    # 获取文档生成器配置
    document_writer_config = settings.get_agent_component_config(
        "document_writer")
    if not document_writer_config:
        # 使用默认配置
        temperature = 0.7
        max_tokens = 4000
        extra_params = {}
    else:
        temperature = document_writer_config.temperature
        max_tokens = document_writer_config.max_tokens
        extra_params = document_writer_config.extra_params

    # 构建高质量的提示词
    prompt = f"""
**Role:** You are a professional researcher and expert writer, tasked with creating a comprehensive and well-structured document.

**Topic:** {topic}

**Original Research Plan:**
{research_plan}

**Raw Data & Research Findings:**
{gathered_data}

**Your Task:**
Based *exclusively* on the provided "Raw Data & Research Findings", write a comprehensive document on the specified "Topic". Follow these instructions carefully:

1. **Synthesize, Do Not Copy:** Do not simply list the raw data. You must synthesize, analyze, and organize the information into a coherent narrative.

2. **Structure:** Structure the document logically with a clear introduction, body, and conclusion. Use headings, subheadings, bullet points, and bold text to improve readability. The output format must be Markdown.

3. **Adhere to the Plan:** Use the "Original Research Plan" as a guide for the document's structure, but feel free to adapt it if the data suggests a better flow.

4. **Be Objective:** Stick to the facts and information presented in the raw data. Do not introduce any external knowledge or personal opinions.

5. **Completeness:** Ensure all key aspects from the gathered data are covered in the final document.

6. **Professional Quality:** Write in a professional, academic style that would be suitable for technical documentation or research reports.

7. **Markdown Formatting:** Use proper Markdown syntax including:
   - Headers (# ## ###)
   - Lists (both bulleted and numbered)
   - Bold and italic text for emphasis
   - Tables where appropriate
   - Code blocks for technical specifications
   - Blockquotes for important notes

Begin writing the document now.
"""

    # 限制 prompt 长度，避免超过模型输入限制
    max_prompt_length = 25000  # 25K 字符限制，给 writer 更多空间
    if len(prompt) > max_prompt_length:
        print(
            f"⚠️  Writer prompt 长度 {len(prompt)} 超过限制 {max_prompt_length}，进行截断"
        )
        # 保留开头和结尾的重要信息，截断中间的研究资料
        header = prompt[:prompt.find("**Raw Data & Research Findings:**") +
                        len("**Raw Data & Research Findings:**")]
        footer = prompt[prompt.find("**Your Task:**"):]
        # 从 gathered_data 中取前 15000 字符
        gathered_data_preview = gathered_data[:15000] + "\n\n... (内容已截断，保留前15000字符)"
        prompt = header + "\n\n" + gathered_data_preview + "\n\n" + footer
        print(f"📝 截断后 writer prompt 长度: {len(prompt)} 字符")

    try:
        # 调用LLM生成文档
        response = llm_client.invoke(prompt,
                                     temperature=temperature,
                                     max_tokens=max_tokens,
                                     **extra_params)

        # 确保响应是有效的Markdown格式
        if not response.strip():
            response = f"# {topic}\n\n无法生成文档内容。"
        elif not response.startswith("#"):
            # 如果没有标题，添加默认标题
            response = f"# {topic}\n\n{response}"

        return {"final_document": response}

    except Exception as e:
        # 如果LLM调用失败，返回错误信息
        print(f"Writer node error: {str(e)}")
        error_document = f"""# {topic}

## 文档生成错误

由于技术原因，无法生成完整的文档。

**错误信息:** {str(e)}

**原始数据摘要:**
{gathered_data[:500]}{"..." if len(gathered_data) > 500 else ""}

请检查系统配置或稍后重试。
"""
        return {"final_document": error_document}

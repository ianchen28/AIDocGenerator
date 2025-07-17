# service/src/doc_agent/utils/content_processor.py
from typing import List, Dict, Any
import json
from ..llm_clients.base import LLMClient


def summarize_content(content: str,
                      llm_client: LLMClient,
                      max_length: int = 2000) -> str:
    """
    缩写内容，提取关键信息
    
    Args:
        content: 原始内容
        llm_client: LLM客户端
        max_length: 目标长度
        
    Returns:
        str: 缩写后的内容
    """
    if len(content) <= max_length:
        return content

    prompt = f"""
请将以下内容缩写到 {max_length} 字符以内，保留关键信息和要点：

{content[:8000]}  # 限制输入长度

要求：
1. 保留核心观点和重要事实
2. 删除冗余和重复信息
3. 使用简洁明了的语言
4. 保持逻辑结构清晰
5. 确保缩写后的内容仍然有价值

请直接返回缩写后的内容，不要添加任何额外说明。
"""

    try:
        response = llm_client.invoke(prompt,
                                     temperature=0.3,
                                     max_tokens=min(max_length * 2, 4000))
        return response.strip()
    except Exception as e:
        print(f"⚠️  内容缩写失败: {str(e)}")
        # 简单的截断作为后备方案
        return content[:max_length] + "..."


def extract_key_points(content: str,
                       llm_client: LLMClient,
                       num_points: int = 5) -> List[str]:
    """
    从内容中提取关键要点
    
    Args:
        content: 原始内容
        llm_client: LLM客户端
        num_points: 要点数量
        
    Returns:
        List[str]: 关键要点列表
    """
    prompt = f"""
请从以下内容中提取 {num_points} 个最重要的关键要点：

{content[:6000]}  # 限制输入长度

要求：
1. 提取最核心、最重要的信息
2. 每个要点应该是一个完整的观点
3. 要点之间应该有逻辑关联
4. 使用简洁明了的表达

请以JSON格式返回：
{{
    "key_points": ["要点1", "要点2", "要点3", "要点4", "要点5"]
}}
"""

    try:
        response = llm_client.invoke(prompt, temperature=0.3, max_tokens=1000)

        # 解析JSON响应
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        try:
            data = json.loads(cleaned_response.strip())
            return data.get("key_points", [])
        except Exception as json_err:
            print(f"⚠️  关键要点提取失败: JSON解析错误: {json_err}")
            print(f"⚠️  LLM原始响应: {repr(response)}")
            # 简单的后备方案
            return [f"要点{i+1}" for i in range(num_points)]

    except Exception as e:
        print(f"⚠️  关键要点提取失败: {str(e)}")
        # 简单的后备方案
        return [f"要点{i+1}" for i in range(num_points)]


def expand_content(content: str,
                   llm_client: LLMClient,
                   target_length: int = 3000) -> str:
    """
    扩写内容，增加详细程度
    
    Args:
        content: 原始内容
        llm_client: LLM客户端
        target_length: 目标长度
        
    Returns:
        str: 扩写后的内容
    """
    if len(content) >= target_length:
        return content

    prompt = f"""
请将以下内容扩写到 {target_length} 字符左右，增加详细程度和深度：

{content}

要求：
1. 保持原有核心观点不变
2. 增加具体的例子和说明
3. 添加相关的背景信息
4. 使用更丰富的表达方式
5. 确保扩写后的内容有价值

请直接返回扩写后的内容，不要添加任何额外说明。
"""

    try:
        response = llm_client.invoke(prompt,
                                     temperature=0.7,
                                     max_tokens=min(target_length * 2, 6000))
        return response.strip()
    except Exception as e:
        print(f"⚠️  内容扩写失败: {str(e)}")
        return content


def process_research_data(research_data: str,
                          llm_client: LLMClient,
                          summary_length: int = 3000,
                          key_points_count: int = 8) -> Dict[str, Any]:
    """
    处理研究数据，生成摘要和关键要点
    
    Args:
        research_data: 原始研究数据
        llm_client: LLM客户端
        summary_length: 摘要长度
        key_points_count: 关键要点数量
        
    Returns:
        Dict[str, Any]: 包含摘要和关键要点的字典
    """
    print(f"📊 处理研究数据: {len(research_data)} 字符")

    # 生成摘要
    summary = summarize_content(research_data, llm_client, summary_length)

    # 提取关键要点
    key_points = extract_key_points(research_data, llm_client,
                                    key_points_count)

    print(f"✅ 数据处理完成: 摘要 {len(summary)} 字符, {len(key_points)} 个要点")

    return {
        "summary": summary,
        "key_points": key_points,
        "original_length": len(research_data),
        "processed_length": len(summary)
    }

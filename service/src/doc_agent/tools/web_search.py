# service/src/doc_agent/tools/web_search.py
from typing import Optional


class WebSearchTool:
    """
    网络搜索工具类
    用于执行网络搜索并返回搜索结果
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化网络搜索工具
        
        Args:
            api_key: Tavily API密钥，暂时未使用
        """
        self.api_key = api_key

    def search(self, query: str) -> str:
        """
        执行网络搜索
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            str: 搜索结果（暂时返回模拟结果）
        """
        # TODO: 后续将实现实际的Tavily API调用
        # 目前返回模拟结果
        return f"Search results for: {query}\n\n" \
               f"1. 相关网页标题1 - 这是一个模拟的搜索结果\n" \
               f"   摘要: 这是第一个搜索结果的摘要内容，包含了一些相关信息...\n\n" \
               f"2. 相关网页标题2 - 另一个模拟的搜索结果\n" \
               f"   摘要: 这是第二个搜索结果的摘要内容，提供了更多相关的信息...\n\n" \
               f"3. 相关网页标题3 - 第三个模拟的搜索结果\n" \
               f"   摘要: 这是第三个搜索结果的摘要内容，补充了额外的相关信息...\n\n" \
               f"注意: 这是模拟的搜索结果，实际实现时将调用Tavily API获取真实数据。"

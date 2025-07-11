# service/src/doc_agent/llm_clients/providers.py
import httpx
from .base import LLMClient


class GeminiClient(LLMClient):

    def __init__(self,
                 api_key: str,
                 model: str = "gemini-1.5-pro-latest",
                 base_url: str = None):
        """
        初始化Gemini客户端
        
        Args:
            api_key: Gemini API密钥
            model: 模型名称，默认为gemini-1.5-pro-latest
            base_url: API基础URL，如果为None则使用默认URL
        """
        self.api_key = api_key
        self.model = model
        # 如果提供了base_url，使用它；否则使用默认URL
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用Gemini API
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            str: 模型响应的内容
        """
        try:
            # 获取可选参数
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)

            # 构建请求数据
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }

            # 发送请求 - 修复 Gemini API URL
            # ChatAI API 使用不同的端点格式
            if "chataiapi.com" in self.base_url:
                # ChatAI API 格式
                url = f"{self.base_url}/chat/completions"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                # 使用 OpenAI 兼容格式
                data = {
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            else:
                # 标准 Gemini API 格式
                url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
                headers = {}
                # 使用 Gemini 格式
                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                }

            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # 提取响应内容 - 支持两种格式
                if "chataiapi.com" in self.base_url:
                    # ChatAI API 返回 OpenAI 兼容格式
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        return content
                    else:
                        raise ValueError(
                            "No response content received from ChatAI API")
                else:
                    # 标准 Gemini API 格式
                    if "candidates" in result and len(
                            result["candidates"]) > 0:
                        content = result["candidates"][0]["content"]["parts"][
                            0]["text"]
                        return content
                    else:
                        raise ValueError(
                            "No response content received from Gemini API")

        except Exception as e:
            raise Exception(f"Gemini API调用失败: {str(e)}")


class DeepSeekClient(LLMClient):

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥
            model: 模型名称，默认为deepseek-chat
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用DeepSeek API
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            str: 模型响应的内容
        """
        try:
            # 获取可选参数
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)

            # 构建请求数据
            data = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # 发送请求
            url = f"{self.base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # 提取响应内容
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return content
                else:
                    raise ValueError(
                        "No response content received from DeepSeek API")

        except Exception as e:
            raise Exception(f"DeepSeek API调用失败: {str(e)}")


class InternalLLMClient(LLMClient):

    def __init__(self,
                 api_url: str,
                 api_key: str,
                 model: str = "qwen-2.5-72b"):
        """
        初始化内部模型客户端
        
        Args:
            api_url: 内部API地址
            api_key: API密钥
            model: 模型名称
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用内部模型API
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数，如temperature, max_tokens等
            
        Returns:
            str: 模型响应的内容
        """
        try:
            # 获取可选参数
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)

            # 构建请求数据
            data = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # 发送请求
            url = f"{self.api_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            } if self.api_key != "EMPTY" else {}

            with httpx.Client(timeout=180.0) as client:  # 内部模型可能需要更长时间
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                # 提取响应内容
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return content
                else:
                    raise ValueError(
                        "No response content received from Internal API")

        except Exception as e:
            raise Exception(f"Internal API调用失败: {str(e)}")


class RerankerClient(LLMClient):

    def __init__(self, api_url: str, api_key: str):
        """
        初始化Reranker客户端
        
        Args:
            api_url: Reranker API地址
            api_key: API密钥
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key

    def invoke(self, prompt: str, **kwargs) -> dict:
        """
        调用Reranker API
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
        Returns:
            dict: 重排序结果
        """
        try:
            documents = kwargs.get("documents", [])
            doc_objs = [{"text": doc} for doc in documents]
            size = kwargs.get("size", len(doc_objs))
            data = {"query": prompt, "doc_list": doc_objs, "size": size}
            url = f"{self.api_url}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            } if self.api_key != "EMPTY" else {}
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result
        except Exception as e:
            raise Exception(f"Reranker API调用失败: {str(e)}")


class EmbeddingClient(LLMClient):

    def __init__(self, api_url: str, api_key: str):
        """
        初始化Embedding客户端
        
        Args:
            api_url: Embedding API地址
            api_key: API密钥
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用Embedding API
        
        Args:
            prompt: 输入文本
            **kwargs: 其他参数
            
        Returns:
            str: 嵌入向量（JSON格式）
        """
        try:
            # 构建请求数据 - 修复字段名
            data = {"inputs": prompt, "model": kwargs.get("model", "gte-qwen")}

            # 发送请求 - 直接使用根端点，因为测试显示它工作正常
            url = f"{self.api_url}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            } if self.api_key != "EMPTY" else {}

            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
                return str(result)  # 返回嵌入向量

        except Exception as e:
            raise Exception(f"Embedding API调用失败: {str(e)}")

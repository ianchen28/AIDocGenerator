from unittest.mock import MagicMock, patch

from src.doc_agent.llm_clients.providers import (
    DeepSeekClient,
    GeminiClient,
    InternalLLMClient,
    MoonshotClient,
)


class TestLLMClients:

    @patch('httpx.Client.post')
    def test_gemini_client_with_think_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "<think>思考</think>最终答案。"
                    }]
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        client = GeminiClient(base_url="http://fake",
                              api_key="fake",
                              model_name="gemini-1.5-pro-latest",
                              reasoning=True)
        result = client.invoke("测试prompt")
        assert "最终答案" in result
        assert "<think>" not in result

    @patch('httpx.Client.post')
    def test_deepseek_client_with_think_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "<think>推理</think>DeepSeek答案。"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        client = DeepSeekClient(base_url="http://fake",
                                api_key="fake",
                                model_name="deepseek",
                                reasoning=True)
        result = client.invoke("测试prompt")
        assert "DeepSeek答案" in result
        assert "<think>" not in result

    @patch('httpx.Client.post')
    def test_moonshot_client_with_think_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "<think>推理</think>Moonshot答案。"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        client = MoonshotClient(base_url="http://fake",
                                api_key="fake",
                                model_name="moonshot",
                                reasoning=True)
        result = client.invoke("测试prompt")
        assert "Moonshot答案" in result
        assert "<think>" not in result

    @patch('httpx.Client.post')
    def test_internal_llm_client_with_think_tags(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "<think>推理</think>Internal答案。"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        client = InternalLLMClient(base_url="http://fake",
                                   api_key="fake",
                                   model_name="internal",
                                   reasoning=True)
        result = client.invoke("测试prompt")
        assert "Internal答案" in result
        assert "<think>" not in result

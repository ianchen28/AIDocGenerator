import subprocess
import tempfile


class CodeExecuteTool:
    """
    代码执行工具类
    用于执行代码并返回执行结果
    目前仅支持 Python 代码。
    TODO: 后续升级为更安全的沙箱环境（如 Docker、nsjail 等）
    """

    def __init__(self):
        pass

    def execute(self, code: str, timeout: int = 5) -> str:
        """
        执行 Python 代码并返回执行结果

        Args:
            code: 要执行的 Python 代码字符串
            timeout: 执行超时时间（秒）
        Returns:
            str: 执行结果（stdout + stderr）
        TODO: 后续增加内存/CPU/输出长度限制，防止安全风险
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                         delete=False) as f:
            f.write(code)
            file_path = f.name
        try:
            result = subprocess.run(['python', file_path],
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout)
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "代码执行超时"
        except Exception as e:
            output = f"执行出错: {e}"
        return output

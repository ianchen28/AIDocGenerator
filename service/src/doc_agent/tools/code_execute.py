import subprocess
import tempfile

from doc_agent.core.logger import logger


class CodeExecuteTool:
    """
    代码执行工具类
    用于执行代码并返回执行结果
    目前仅支持 Python 代码。
    TODO: 后续升级为更安全的沙箱环境（如 Docker、nsjail 等）
    """

    def __init__(self):
        logger.info("初始化代码执行工具")

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
        logger.info(f"开始执行代码，超时时间: {timeout}秒")
        logger.debug(f"待执行代码: {code}")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                         delete=False) as f:
            f.write(code)
            file_path = f.name
            logger.debug(f"临时文件路径: {file_path}")

        try:
            logger.info("执行 Python 代码")
            result = subprocess.run(['python', file_path],
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout)
            output = result.stdout + result.stderr
            logger.debug(f"执行结果 - stdout: {result.stdout}")
            logger.debug(f"执行结果 - stderr: {result.stderr}")
            logger.info("代码执行完成")
        except subprocess.TimeoutExpired:
            logger.error(f"代码执行超时 (timeout={timeout}秒)")
            output = "代码执行超时"
        except Exception as e:
            logger.error(f"代码执行出错: {e}")
            output = f"执行出错: {e}"

        return output

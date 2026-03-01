"""主程序入口与日志测试模块。

用于验证 src.utils.logger 的各项功能，包括原生调用、封装调用栈回溯、
以及异常追踪（打印到控制台与 error.log）。
"""

from src.utils import logger as log_module
from src.utils.logger import logger


def test_standard_levels() -> None:
    """测试原生的各种日志级别输出。"""
    logger.debug("这是一条 [原生] DEBUG 信息")
    logger.info("这是一条 [原生] INFO 信息")
    logger.warning("这是一条 [原生] WARNING 信息")
    logger.error("这是一条 [原生] ERROR 信息")
    logger.success("这是一条 [原生] SUCCESS 信息")  # Loguru 特有的成功级别


def test_wrapped_methods() -> None:
    """测试二次封装的方法，验证调用栈 depth=1 是否生效。
    
    如果配置正确，日志输出的文件名和行号应指向本文件（main.py），
    而不是 logger.py 内部的包装函数。
    """
    log_module.debug("这是一条 [封装] DEBUG 信息")
    log_module.info("这是一条 [封装] INFO 信息")
    log_module.warning("这是一条 [封装] WARNING 信息")
    log_module.error("这是一条 [封装] ERROR 信息")
    log_module.critical("这是一条 [封装] CRITICAL 信息")


def test_exception_logging() -> None:
    """测试异常捕获与诊断日志记录。
    
    验证是否生成 error_*.log 并包含完整的变量上下文 (diagnose=True)。
    """
    try:
        a: int = 10
        b: int = 0
        _ = a / b
    except ZeroDivisionError as e:
        # logger.exception 会自动捕获 traceback 并输出到 ERROR 级别
        logger.exception(f"发生致命的数学错误: {e}")


def main() -> None:
    """主函数，执行所有日志测试。"""
    logger.info("--- 开始日志系统测试 ---")
    
    logger.info(">>> 1. 测试原生日志级别")
    test_standard_levels()
    
    logger.info(">>> 2. 测试二次封装日志级别 (请注意检查行号)")
    test_wrapped_methods()
    
    logger.info(">>> 3. 测试异常追踪记录 (请随后检查 logs/ 目录下的 error 日志)")
    test_exception_logging()
    
    logger.info("--- 日志系统测试结束 ---")


if __name__ == "__main__":
    main()
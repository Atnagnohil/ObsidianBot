"""日志工具模块，基于 Loguru 封装。

参考主流 QQ 机器人框架（如 NoneBot2）的日志设计，提供开箱即用的日志功能。
支持控制台彩色输出、文件按大小/时间轮转，并修复了二次封装导致的调用栈丢失问题。
"""

import sys
from pathlib import Path
from typing import Any, Union

import loguru

# 导出原生 logger 对象，推荐在其他模块中直接 from utils.logger import logger
logger = loguru.logger


def init_logger(
    log_dir: Union[str, Path] = "logs",
    rotation: str = "10 MB",
    retention: str = "7 days",
    console_level: str = "DEBUG",
    file_level: str = "DEBUG",
) -> None:
    """初始化并配置全局日志记录器。

    Args:
        log_dir (Union[str, Path], optional): 日志保存目录. 默认为 "logs".
        rotation (str, optional): 日志轮转条件（大小或时间）. 默认为 "10 MB".
        retention (str, optional): 日志保留时长. 默认为 "7 days".
        console_level (str, optional): 控制台输出级别. 默认为 "DEBUG".
        file_level (str, optional): 文件输出级别. 默认为 "DEBUG".
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 移除 Loguru 默认的处理器，避免重复输出
    logger.remove()

    # 1. 添加控制台处理器（带颜色与格式）
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=console_level,
        colorize=True,
        enqueue=True,  # 开启异步队列，提升高并发聊天场景性能
    )

    # 2. 添加全量日志文件处理器
    logger.add(
        log_path / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=file_level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
    )

    # 3. 添加错误日志专属文件处理器
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,  # 错误时记录完整的异常回溯栈
        diagnose=True,   # 记录变量值以辅助诊断
    )


# ---------------------------------------------------------------------------
# 便捷包装方法 (向下兼容)
# 注意：必须使用 opt(depth=1) 使 loguru 忽略当前包装函数的调用层级，
# 从而在日志中正确显示实际调用此函数的业务代码的文件名与行号。
# ---------------------------------------------------------------------------

def debug(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 DEBUG 级别日志。
    
    Args:
        message (str): 日志信息。
        *args (Any): 字符串格式化位置参数。
        **kwargs (Any): 字符串格式化关键字参数。
    """
    logger.opt(depth=1).debug(message, *args, **kwargs)


def info(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 INFO 级别日志。"""
    logger.opt(depth=1).info(message, *args, **kwargs)


def warning(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 WARNING 级别日志。"""
    logger.opt(depth=1).warning(message, *args, **kwargs)


def error(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 ERROR 级别日志。"""
    logger.opt(depth=1).error(message, *args, **kwargs)


def critical(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 CRITICAL 级别日志。"""
    logger.opt(depth=1).critical(message, *args, **kwargs)


# 模块被导入时自动执行基础初始化
init_logger()
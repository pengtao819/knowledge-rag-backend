import logging
import sys
from logging.handlers import RotatingFileHandler
from config import BASE_DIR

# 日志目录
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 清空已有 handler，避免重载时重复
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    # 格式：时间 | 级别 | 模块名 | 消息
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler，单文件最大 10MB，最多保留 5 个
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 压制第三方库的日志，只保留 WARNING 以上
    for name in [
        "httpx", "httpx2", "httpcore",
        "openai", "urllib3", "chromadb",
        "asyncio", "watchfiles",
        "sqlalchemy", "aiomysql",
        "pdfminer", "pdfplumber"
    ]:
        logging.getLogger(name).setLevel(logging.WARNING)

    # pdfminer 的字体警告是噪音，直接压到 ERROR
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("pdfplumber").setLevel(logging.ERROR)

    logger.info("日志系统初始化完成")
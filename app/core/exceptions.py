class AppError(Exception):
    """所有业务异常的基类"""
    status_code = 500
    detail = "服务器内部错误"

    def __init__(self, detail: str = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class ConversationNotFoundError(AppError):
    status_code = 404
    detail = "会话不存在"


class LLMTimeoutError(AppError):
    status_code = 504
    detail = "LLM 调用超时，请重试"


class RetrievalError(AppError):
    status_code = 500
    detail = "知识库检索失败"


class PDFParseError(AppError):
    status_code = 400
    detail = "PDF 解析失败"
import os
from fastapi import UploadFile
import pdfplumber
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 上传目录
UPLOAD_FOLDER = './uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 中文分隔符-优先级
CHINESE_SEPARATORS = [
    "\n\n",
    "\n",
    "。",
    "！",
    "？",
    "；",
    "，",
    ". ",   # .加空格
    "! ",   # !加空格
    "? ",
    "; ",
    ", ",
    " ",
    "",     # 超长无标点文本-兜底
]

# 上传保存PDF文档
async def save_upload_pdf(upload_file: UploadFile):
    # 拼接完整路径
    save_path = os.path.join(UPLOAD_FOLDER, upload_file.filename)

    # 写入本地文件
    with open(save_path, 'wb') as f:
        content = await upload_file.read()
        f.write(content)

    return {
        "statusCode": 200,
        "msg": "文件上传成功",
        "filename": upload_file.filename,
        "save_path": save_path
    }

# 解析PDF文档
def parse_pdf(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    docs: List[Document] = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            docs.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "source": filename,
                        "page": page_num,
                    },
                )
            )

# 分块PDF文档
# 待解决问题：大文件处理太慢
def chunking_pdf(chunk_size: int = 500,chunk_overlap: int = 100) -> RecursiveCharacterTextSplitter:
    # 先使用递归字符分块
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap必须小于chunk_size")

    splitter =  RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,          # 最大字符长度
        chunk_overlap=chunk_overlap,    # 重叠字符数
        separators=CHINESE_SEPARATORS,
        length_function=len,
        keep_separator=True,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(document)

    # 加上编号，用于后面引用来源
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx

    return chunks






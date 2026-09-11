import os
from fastapi import UploadFile
import pdfplumber

# 上传目录
UPLOAD_FOLDER = './uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 上传保存PDF文档函数
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

# 解析PDF文档函数
def parse_pdf(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    text_all = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_all += page_text + "\n"
    return text_all





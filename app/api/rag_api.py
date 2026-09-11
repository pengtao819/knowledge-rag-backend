from fastapi import APIRouter, UploadFile, File, HTTPException
# 导入service里的上传处理函数
from app.services.rag_service import save_upload_pdf, parse_pdf
import os

router = APIRouter(prefix="/rag", tags=["RAG知识库"])
UPLOAD_FOLDER = './uploads'


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="仅支持PDF文件")

        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file_exist = os.path.exists(save_path)

        if not file_exist:
            # 文件不存在：保存到磁盘
            with open(save_path, "wb") as f:
                f.write(await file.read())
            msg = "文件不存在，已保存并解析"
        else:
            # 文件已存在：不保存，直接使用旧文件解析
            msg = "同名文件已存在，跳过保存，直接解析已有文件"

        # 无论新文件还是旧文件，都执行解析
        text = parse_pdf(file.filename)

        return {
            "filename": file.filename,
            "is_new_upload": not file_exist,
            "text_preview": text[:300],
            "msg": msg
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF处理失败：{str(e)}")
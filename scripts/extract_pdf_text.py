import pdfplumber

with pdfplumber.open(r"D:\PythonProjects\knowledge-rag-backend\uploads\Happy-LLM-0727.pdf") as pdf:
    with open(r"D:\PythonProjects\knowledge-rag-backend\data\hello_agents_full.txt", "w", encoding="utf-8") as f:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            f.write(f"\n===== Page {i} =====\n{text}\n")
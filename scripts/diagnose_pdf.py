import sys
import re
import logging
from collections import Counter
import pdfplumber

# 屏蔽 pdfplumber 的字体警告
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)


def clean_text(text):
    text = re.sub(r'(?<=[\u4e00-\u9fff])\n(?=[A-Za-z0-9])', ' ', text)
    text = re.sub(r'(?<=[A-Za-z0-9])\n(?=[\u4e00-\u9fff])', ' ', text)
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    text = text.replace('\n\n', '<<PARA>>').replace('\n', '').replace('<<PARA>>', '\n\n')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def main(pdf_path, max_pages=None):
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        if max_pages:
            total = min(total, max_pages)
        print(f"共 {len(pdf.pages)} 页，本次分析前 {total} 页\n")

        results = []
        for i, page in enumerate(pdf.pages, 1):
            if i > total:
                break
            if i % 50 == 0:
                print(f"  已处理 {i}/{total} 页...")
            raw = (page.extract_text() or "").strip()
            cleaned = clean_text(raw) if raw else ""
            if not cleaned:
                results.append((i, 0, "", 0.0, ""))
                continue
            c = Counter(cleaned)
            top_char, top_count = c.most_common(1)[0]
            ratio = top_count / len(cleaned)
            results.append((i, len(cleaned), repr(top_char), ratio, cleaned[:60].replace("\n", " ")))

    results.sort(key=lambda x: x[3], reverse=True)
    print(f"\n{'页码':<6}{'长度':<8}{'高频字符':<10}{'占比':<10}预览")
    print("-" * 100)
    for r in results[:25]:
        print(f"{r[0]:<6}{r[1]:<8}{r[2]:<10}{r[3]:<10.2%}{r[4]}")

    print("\n=== 占比分布 ===")
    buckets = {"<10%": 0, "10-20%": 0, "20-30%": 0, "30-50%": 0, ">=50%": 0}
    for r in results:
        ratio = r[3]
        if ratio < 0.10: buckets["<10%"] += 1
        elif ratio < 0.20: buckets["10-20%"] += 1
        elif ratio < 0.30: buckets["20-30%"] += 1
        elif ratio < 0.50: buckets["30-50%"] += 1
        else: buckets[">=50%"] += 1
    for k, v in buckets.items():
        print(f"  {k}: {v} 页")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/diagnose_pdf.py <pdf路径> [最大页数]")
        sys.exit(1)
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(sys.argv[1], max_pages)
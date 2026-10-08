"""
从 merged.json 中抽取 15 条单文档问答，作为公开测试集。
同时生成对应的 PDF 知识库文件。
"""
import json
import os
import random
import jieba
import jieba.posseg as pseg
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED_PATH = os.path.join(BASE_DIR, "data", "merged.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "data", "crud_eval.json")
OUTPUT_PDF = os.path.join(BASE_DIR, "data", "crud_docs.pdf")

random.seed(42)


def extract_keywords(answer: str, top_n: int = 3):
    """从标准答案中提取关键词。
    优先提取数字（含小数、百分比），其次提取名词。
    """
    import re
    # 1. 先抓数字：匹配 1442.63、2.39%、22.16% 这类
    numbers = re.findall(r'\d+\.?\d*%?', answer)
    keywords = []
    for n in numbers:
        if len(n) >= 3 and n not in keywords:   # 过滤掉 "1"、"2" 这种
            keywords.append(n)
        if len(keywords) >= top_n:
            break

    # 2. 数字不够，补名词
    if len(keywords) < top_n:
        words = pseg.cut(answer)
        for word, flag in words:
            if len(word) < 2:
                continue
            if flag in ("n", "nr", "ns", "nt", "nz", "eng"):
                if word not in keywords:
                    keywords.append(word)
            if len(keywords) >= top_n:
                break

    return keywords[:top_n]


def build_eval_set(qa_list, sample_n=15):
    sample = random.sample(qa_list, sample_n)
    eval_set = []
    for i, item in enumerate(sample, 1):
        answer = item["answers"]
        eval_set.append({
            "id": i,
            "question": item["questions"],
            "ground_truth": answer,
            "keywords": extract_keywords(answer),
            "category": "simple_fact",
            "source_id": item["ID"],
        })
    return sample, eval_set


def build_pdf(sample, output_path):
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    for i, item in enumerate(sample, 1):
        content = item["news1"]
        c.setFont("STSong-Light", 10)
        text_obj = c.beginText(40, height - 60)
        text_obj.textLine(f"=== 文档 {i}（ID: {item['ID']}）===")
        text_obj.textLine("")

        for j in range(0, len(content), 50):
            line = content[j:j + 50]
            text_obj.textLine(line)
            if text_obj.getY() < 60:
                c.drawText(text_obj)
                c.showPage()
                c.setFont("STSong-Light", 10)
                text_obj = c.beginText(40, height - 60)

        c.drawText(text_obj)
        c.showPage()

    c.save()


def main():
    print("加载 merged.json...")
    with open(MERGED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    qa_list = data["questanswer_1doc"]
    print(f"单文档问答总条数：{len(qa_list)}")

    sample, eval_set = build_eval_set(qa_list, sample_n=100)

    # 保存评估集
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(eval_set, f, ensure_ascii=False, indent=2)
    print(f"评估集已保存：{OUTPUT_JSON}")

    # 打印前 3 条供人工审查
    for item in eval_set[:3]:
        print(f"\n--- ID {item['id']} ---")
        print(f"问题：{item['question']}")
        print(f"答案：{item['ground_truth']}")
        print(f"关键词：{item['keywords']}")

    # 生成 PDF
    print(f"\n生成 PDF 知识库...")
    build_pdf(sample, OUTPUT_PDF)
    print(f"PDF 已生成：{OUTPUT_PDF}")


if __name__ == "__main__":
    main()
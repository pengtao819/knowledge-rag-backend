"""
验证评估问题集的 keywords 和 source_page 是否准确。
"""
import json
import os
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_PATH = os.path.join(BASE_DIR, "data", "hello_agents_full.txt")
EVAL_PATH = os.path.join(BASE_DIR, "data", "eval_questions.json")


def load_pages(path):
    """读取按页分割的文本，返回 {page_num: text} 字典"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = unicodedata.normalize('NFKC', content)

    pages = {}
    pattern = re.compile(r"=====\s*Page\s+(\d+)\s*=====")
    matches = list(pattern.finditer(content))

    for i, m in enumerate(matches):
        page_num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        pages[page_num] = content[start:end]

    return pages


def verify():
    pages = load_pages(TEXT_PATH)
    print(f"共加载 {len(pages)} 页\n")

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"共 {len(questions)} 条测试问题")
    print("=" * 100)

    problems = []

    for q in questions:
        qid = q["id"]
        page = q.get("source_page")
        keywords = q["keywords"]
        category = q["category"]

        print(f"\n[ID {qid}] {q['question']}")
        print(f"  类别：{category}   source_page：{page}")

        if category == "out_of_scope":
            # 只检查核心概念词（不含通用词）
            generic_words = {"参数量", "量化", "重排序", "位置编码", "文档未提及", "bit"}
            core_kws = [kw for kw in keywords if kw not in generic_words]
            all_text = "".join(pages.values())
            hits = [kw for kw in core_kws if kw in all_text]
            if hits:
                print(f"  ! out_of_scope，但核心词在文档中出现：{hits}")
                problems.append((qid, f"out_of_scope 不成立：{hits}"))
            else:
                print(f"  ✓ 核心词都不在文档中，out_of_scope 成立")
            continue

        if page is None or page not in pages:
            print(f"  X source_page {page} 不存在")
            problems.append((qid, f"source_page {page} 不存在"))
            continue

        page_text = pages[page]
        missing = [kw for kw in keywords if kw not in page_text]

        if missing:
            print(f"  X 以下关键词在第 {page} 页找不到：{missing}")
            for kw in missing:
                found_pages = [p for p, t in pages.items() if kw in t]
                if found_pages:
                    print(f"     '{kw}' 实际出现在页：{found_pages[:5]}")
                else:
                    print(f"     '{kw}' 在整个文档中找不到")
            problems.append((qid, f"keywords 缺失：{missing}"))
        else:
            print(f"  ✓ 所有关键词都在第 {page} 页出现")

    print("\n" + "=" * 100)
    print(f"\n共发现 {len(problems)} 条问题：")
    for qid, desc in problems:
        print(f"  ID {qid}: {desc}")


if __name__ == "__main__":
    verify()
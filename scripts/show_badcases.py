import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(BASE_DIR, "results", "eval_report.json")

with open(REPORT, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"总问题数：{data['total']}")
print(f"知识库内：{data['in_scope']}")
print(f"知识库外：{data['out_of_scope']}")
print(f"错误案例数：{data['badcase_count']}\n")

for b in data["badcases"]:
    print("=" * 70)
    print(f"ID {b['id']} | 类别：{b.get('category')} | 原因：{b.get('reason')}")
    print(f"问题：{b.get('question', '')}")
    if "ground_truth" in b:
        print(f"标准：{b['ground_truth']}")
    if "answer" in b:
        print(f"回答：{b['answer']}")
    if "keywords" in b:
        print(f"关键词：{b['keywords']}")
    if "error" in b:
        print(f"错误：{b['error']}")
    if "sources_preview" in b:
        print(f"检索片段：{b['sources_preview']}")
    print()
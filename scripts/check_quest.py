import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED = os.path.join(BASE_DIR, "data", "merged.json")

with open(MERGED, "r", encoding="utf-8") as f:
    data = json.load(f)

qa_list = data["questanswer_1doc"]
print(f"单文档问答总条数：{len(qa_list)}")
print(f"\n=== 第 1 条 ===")
print(json.dumps(qa_list[0], ensure_ascii=False, indent=2))
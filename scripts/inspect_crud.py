import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED_PATH = os.path.join(BASE_DIR, "data", "merged.json")

# 读取 JSON
print("加载中...")
with open(MERGED_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"顶层类型：{type(data).__name__}")

if isinstance(data, list):
    print(f"总条数：{len(data)}")
    print("\n=== 第 1 条 ===")
    print(json.dumps(data[0], ensure_ascii=False, indent=2)[:2000])
    print("\n=== 第 2 条 ===")
    print(json.dumps(data[1], ensure_ascii=False, indent=2)[:2000])

    # 统计任务类型分布
    from collections import Counter
    keys = Counter()
    for item in data:
        if isinstance(item, dict):
            for k in item.keys():
                keys[k] += 1
    print("\n=== 所有出现过的字段 ===")
    for k, c in keys.most_common():
        print(f"  {k}: {c} 次")

elif isinstance(data, dict):
    print(f"键：{list(data.keys())}")
    first_key = list(data.keys())[0]
    print(f"\n=== {first_key} ===")
    print(json.dumps(data[first_key], ensure_ascii=False, indent=2)[:2000])
import json
import requests
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(BASE_DIR, "results", "eval_report.json")

targets = [
    {
        "id": 21,
        "question": "第二章讲的 Transformer 位置编码和第五章 LLaMA2 使用的位置编码有什么不同？它们分别解决什么问题？",
        "category": "multi_hop",
    },
    {
        "id": 22,
        "question": "第三章介绍的 BERT 预训练目标，与第四章说的主流 LLM 预训练任务有什么不同？",
        "category": "multi_hop",
    },
]

for item in targets:
    print(f"\n=== ID {item['id']} ===")
    try:
        resp = requests.post(
            "http://localhost:8000/rag/chat",
            json={"question": item["question"], "top_k": 3},
            timeout=300,
            proxies={"http": None, "https": None},
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"回答：{data.get('answer', '')[:500]}")
        print(f"来源数：{len(data.get('sources', []))}")
    except Exception as e:
        print(f"失败：{e}")
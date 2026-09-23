"""
RAG 评估脚本：调用 /rag/chat 接口，逐条评估检索和回答质量。

评估三个指标：
1. 回答准确率：模型回答里是否包含标准答案的关键词（命中一半以上算对）
2. 检索命中率：返回的 sources 里是否包含问题相关关键词
3. 知识库外拒答率：out_of_scope 类问题，模型是否老实说"不知道"
"""
import json
import os
import time
import requests
from tqdm import tqdm

# 路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_SET_PATH = os.path.join(BASE_DIR, "data", "eval_questions.json")
REPORT_PATH = os.path.join(BASE_DIR, "results", "eval_report.json")

# 接口配置
API_URL = "http://localhost:8000/rag/chat"
TOP_K = 3
TIMEOUT = 90  # 单条请求超时（秒）


def call_api(question):
    """
    调用问答接口。每条问题新开会话（不传 conversation_id），
    避免历史对话污染评估结果。
    """
    payload = {
        "question": question,
        "top_k": TOP_K,
    }
    resp = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    return answer, sources


def source_hit(sources, keywords):
    """
    检索命中：任意一个 source 的 preview 里包含任意一个关键词。
    """
    if not sources:
        return False
    combined = " ".join(s.get("preview", "") for s in sources)
    return any(kw in combined for kw in keywords)


def answer_correct(answer, keywords):
    """
    回答准确：命中一半以上关键词算对。
    避免 keywords 写得太细导致误判。
    """
    if not keywords:
        return True
    hits = sum(1 for kw in keywords if kw in answer)
    threshold = max(1, len(keywords) // 2)
    return hits >= threshold


def is_refusal(answer):
    """
    判断回答是否为拒答。
    知识库外的问题，模型应该老实说"找不到"、"未提及"。
    """
    refusal_keywords = [
        "无法", "没有找到", "未提及", "不知道", "没有相关",
        "未包含", "不含", "没有提供", "未介绍", "未给出",
        "查不到", "无法回答", "没有涉及",
    ]
    return any(kw in answer for kw in refusal_keywords)


def evaluate():
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total = len(questions)
    in_scope_total = 0
    answer_correct_count = 0
    source_hit_count = 0
    out_of_scope_total = 0
    out_of_scope_refusal_count = 0
    badcases = []

    for item in tqdm(questions, desc="评估中"):
        try:
            answer, sources = call_api(item["question"])
        except Exception as e:
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "category": item.get("category"),
                "reason": "接口调用失败",
                "error": str(e),
            })
            continue

        # ----- 知识库外问题：考察拒答能力 -----
        if item["category"] == "out_of_scope":
            out_of_scope_total += 1
            if is_refusal(answer):
                out_of_scope_refusal_count += 1
            else:
                badcases.append({
                    "id": item["id"],
                    "question": item["question"],
                    "category": "out_of_scope",
                    "reason": "应该拒答但未拒答（可能产生了幻觉）",
                    "answer": answer,
                })
            continue

        # ----- 知识库内问题 -----
        in_scope_total += 1

        # 检索命中
        if source_hit(sources, item["keywords"]):
            source_hit_count += 1
        else:
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "category": item["category"],
                "reason": "检索未命中",
                "keywords": item["keywords"],
                "sources_preview": [
                    s.get("preview", "")[:100] for s in sources
                ],
            })

        # 回答准确
        if answer_correct(answer, item["keywords"]):
            answer_correct_count += 1
        else:
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "category": item["category"],
                "reason": "回答未包含足够关键词",
                "ground_truth": item["ground_truth"],
                "keywords": item["keywords"],
                "answer": answer,
            })

    # ----- 汇总报告 -----
    report = {
        "total": total,
        "in_scope": in_scope_total,
        "out_of_scope": out_of_scope_total,
        "answer_accuracy": answer_correct_count / in_scope_total if in_scope_total else 0,
        "source_hit_rate": source_hit_count / in_scope_total if in_scope_total else 0,
        "out_of_scope_refusal_rate": out_of_scope_refusal_count / out_of_scope_total if out_of_scope_total else 0,
        "badcase_count": len(badcases),
        "badcases": badcases,
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ----- 终端打印 -----
    print("\n" + "=" * 60)
    print("             RAG 评估报告")
    print("=" * 60)
    print(f"总问题数：            {total}")
    print(f"知识库内问题：        {in_scope_total}")
    print(f"知识库外问题：        {out_of_scope_total}")
    print("-" * 60)
    print(f"回答准确率：          {report['answer_accuracy']:.2%}")
    print(f"检索命中率：          {report['source_hit_rate']:.2%}")
    print(f"知识库外拒答率：      {report['out_of_scope_refusal_rate']:.2%}")
    print(f"错误案例数：          {len(badcases)}")
    print("=" * 60)
    print(f"\n详细报告已保存到：{REPORT_PATH}")


if __name__ == "__main__":
    evaluate()
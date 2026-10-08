"""
CRUD-RAG 公开测试集评估脚本。
调用 /rag/chat 接口，逐条评估检索和回答质量。
"""
import json
import os
import requests
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_SET_PATH = os.path.join(BASE_DIR, "data", "crud_eval.json")
REPORT_PATH = os.path.join(BASE_DIR, "results", "crud_eval_report.json")

API_URL = "http://localhost:8000/rag/chat"
COLLECTION = "crud_rag_news_100"
TOP_K = 3
TIMEOUT = 200


def call_api(question):
    payload = {
        "question": question,
        "top_k": TOP_K,
        "collection_name": COLLECTION,
    }
    resp = requests.post(
        API_URL,
        json=payload,
        timeout=TIMEOUT,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("answer", ""), data.get("sources", [])


def source_hit(sources, keywords):
    """检索命中：返回的 sources preview 里包含任一关键词"""
    if not sources:
        return False
    combined = " ".join(s.get("preview", "") for s in sources)
    return any(kw in combined for kw in keywords)


def answer_correct(answer, keywords, sources):
    """
    回答正确性判定（严格版）：
    答案必须在检索到的上下文里能找到支撑，才算 RAG 正确。

    如果回答里有答案，但检索的 sources 里没有对应的关键词，
    说明 LLM 是靠内部知识回答的，不算 RAG 正确。
    """
    if not keywords:
        return True

    # 回答里有答案
    answer_has_kw = any(kw in answer for kw in keywords)

    # 检索到的上下文里也有关键词支撑
    source_text = " ".join(s.get("preview", "") for s in sources) if sources else ""
    source_has_kw = any(kw in source_text for kw in keywords)

    # 两者都满足才算正确
    return answer_has_kw and source_has_kw


def evaluate():
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total = len(questions)
    answer_correct_count = 0
    source_hit_count = 0
    badcases = []

    for item in tqdm(questions, desc="评估中"):
        try:
            answer, sources = call_api(item["question"])
        except Exception as e:
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "reason": "接口调用失败",
                "error": str(e),
            })
            continue

        # 检索命中
        hit = source_hit(sources, item["keywords"])
        if hit:
            source_hit_count += 1
        else:
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "reason": "检索未命中",
                "keywords": item["keywords"],
            })

        # 回答正确（严格判定）
        if answer_correct(answer, item["keywords"], sources):
            answer_correct_count += 1
        else:
            # 细分错误原因
            if "根据当前知识库" in answer or "无法确定" in answer:
                reason = "模型拒答（可能是真没检索到）"
            else:
                reason = "回答无检索支撑（可能靠内部知识作答）"
            badcases.append({
                "id": item["id"],
                "question": item["question"],
                "reason": reason,
                "ground_truth": item["ground_truth"],
                "keywords": item["keywords"],
                "answer": answer,
                "sources_preview": [s.get("preview", "")[:100] for s in sources],
            })

    report = {
        "total": total,
        "collection": COLLECTION,
        "answer_accuracy": answer_correct_count / total if total else 0,
        "source_hit_rate": source_hit_count / total if total else 0,
        "badcase_count": len(badcases),
        "badcases": badcases,
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("       CRUD-RAG 公开测试集评估报告（严格模式）")
    print("=" * 60)
    print(f"知识库：        {COLLECTION}")
    print(f"总问题数：      {total}")
    print(f"回答准确率：    {report['answer_accuracy']:.2%}")
    print(f"检索命中率：    {report['source_hit_rate']:.2%}")
    print(f"错误案例数：    {len(badcases)}")
    print("=" * 60)
    print(f"\n详细报告：{REPORT_PATH}")


if __name__ == "__main__":
    evaluate()
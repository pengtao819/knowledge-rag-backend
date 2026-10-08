"""
查看评估报告中的错误案例。
支持自建测试集和公开测试集两份报告。
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 两份报告的路径
REPORTS = {
    "自建测试集（Happy-LLM）": os.path.join(BASE_DIR, "results", "eval_report.json"),
    "公开测试集（CRUD-RAG）": os.path.join(BASE_DIR, "results", "crud_eval_report.json"),
}


def show_report(name, path):
    print("\n" + "=" * 70)
    print(f"  {name}")
    print("=" * 70)

    if not os.path.exists(path):
        print(f"  报告不存在：{path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"总问题数：{data.get('total')}")
    print(f"回答准确率：{data.get('answer_accuracy', 0):.2%}")
    print(f"检索命中率：{data.get('source_hit_rate', 0):.2%}")
    if "out_of_scope_refusal_rate" in data:
        print(f"知识库外拒答率：{data['out_of_scope_refusal_rate']:.2%}")
    print(f"错误案例数：{data.get('badcase_count')}")

    badcases = data.get("badcases", [])
    if not badcases:
        print("\n无错误案例。")
        return

    print(f"\n--- 错误案例详情（最多显示 10 条）---")
    for b in badcases[:10]:
        print("\n" + "-" * 60)
        print(f"ID {b['id']} | 原因：{b.get('reason')}")
        print(f"问题：{b.get('question', '')[:120]}")
        if b.get("keywords"):
            print(f"关键词：{b['keywords']}")
        if b.get("ground_truth"):
            print(f"标准：{b['ground_truth'][:200]}")
        if b.get("answer"):
            print(f"回答：{b['answer'][:200]}")
        if b.get("error"):
            print(f"错误：{b['error']}")
        if b.get("sources_preview"):
            print(f"检索片段：{b['sources_preview']}")


if __name__ == "__main__":
    for name, path in REPORTS.items():
        show_report(name, path)
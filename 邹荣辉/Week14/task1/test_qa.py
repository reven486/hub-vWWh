"""测试脚本：跑两个问题验证检索 + 回答流程是否正常。"""
import sys

# 强制 UTF-8 输出，避免 Windows GBK 控制台乱码
sys.stdout.reconfigure(encoding="utf-8")

from qa import build_chain

chain = build_chain()

questions = [
    "BERT 模型的核心创新是什么？",
    "这个操作系统原理实验教学辅助系统是用来做什么的？",
]

for q in questions:
    print(f"\n========== 问题 ==========\n{q}")
    answer = chain.invoke(q)
    print(f"\n========== 回答 ==========\n{answer}")

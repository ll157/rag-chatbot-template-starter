# 语料存放位置说明

正式演示语料（10 份虚构 PDF + 页码索引 index.md）按用户指定存放在**仓库外**：

- 目录：`D:\RAG项目\产品说明书\`
- 生成脚本：`scripts/make_corpus.py`（用系统 Python 运行，可随时重新生成）
- 事实源：`docs/corpus_facts.md`
- 出题依据：`docs/eval/questions_dev.md`（开发 18 题）、`docs/eval/sealed/questions_sealed.md`（封存 12 题）

为什么不放仓库：语料是本地演示数据（PDF 二进制），入库会让仓库膨胀；脚本 + 事实表 + 索引在仓库里，任何人克隆后跑一遍脚本即可完整复现。

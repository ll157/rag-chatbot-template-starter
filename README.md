# 产品说明书问答助手（RAG）

基于开源模板 [rag-chatbot-template-starter](https://github.com/panutpl/rag-chatbot-template-starter)（Fork）二次开发的**产品说明书问答系统**：上传产品 PDF，用自然语言提问，得到**带"文件名+页码"引用出处**的回答，并配有一套完整的**评测与可靠性验证体系**。

> 分支：`feature/product-assistant` ｜ 版本冻结：`v0.1-rc`（tag）｜ 协议：MIT（继承上游）

---

## 在上游基础上做了什么

| 能力 | 说明 |
| --- | --- |
| **操作页面** | 单文件网页控制台（`app/static/index.html`，无 CDN 依赖）：上传（含型号/版本元数据）、文档管理、提问、回答 + 引用展示、markdown 渲染 |
| **子问题拆分** | 复合问题自动拆为最多 3 个子问题（三道防线：标点规则 → 疑问词计数 → 模型拆分，失败回退不拆），逐个检索回答并合并 |
| **结构化引用** | 引用（文件+页码+原文片段）由**程序从检索结果生成**，不经过模型——出处不存在"编造"环节 |
| **评测体系** | 开发集 18 题 / 封存集 12 题 / 裸模型对照 6 题 / 引用对抗校验 5 案例，四层各测各的（见下） |
| **可视化报告** | `make_report.py` 生成 HTML 报告：左栏预期、右栏实际回答与引用原文 |
| **交接体检** | `doctor.py` 23 项检查（环境/依赖/配置/端口/密钥存在性/模型连通性），每项异常附下一步命令 |

## 评测结果（截至 v0.1-rc）

| 测试 | 结果 | 证据 |
| --- | --- | --- |
| 开发集 18 题（回归） | 18/18 | `docs/eval/测试结果/成绩单_day6_20261113_1607.csv` |
| 封存集 12 题（未参与调试） | 12/12 | `docs/eval/测试结果/成绩单_sealed_20261114_1449.csv` |
| 裸模型对照 6 题（唯一变量=是否检索知识库） | RAG 6/6 解决问题 vs 裸模型 0/6，且更快 | `docs/eval/测试结果/裸模型对照_*.json` |
| 引用对抗校验（含 2 道库中不存在型号的对抗题） | 5 案例 0 违规 | `docs/eval/测试结果/引用校验_20261113_1645.json` |
| 独立第三方出题 3 题（隔离会话盲测） | 3/3，并借此发现并修复 1 个空回答 bug | `docs/eval/测试结果/成绩单_indep2_20261114_1604.csv` |

诚实备注：封存卷出题者与开发者同源（非完全独立第三方）；对照样本仅 6 题，为方向性证据。完整过程日志见 [`docs/STATUS.md`](docs/STATUS.md)。

## 快速开始（Windows）

```bat
git clone https://github.com/ll157/rag-chatbot-template-starter.git
cd rag-chatbot-template-starter

python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

copy .env.example .env        :: retrieval 模式无需任何密钥；要生成回答则填 DEEPSEEK_API_KEY 等

start.bat                     :: 一键启动（http://127.0.0.1:8000/）
check.bat                     :: 一键体检（先启动服务再跑 check）
```

> 首次运行会下载嵌入模型（约几百 MB，仅一次）；国内网络自动走 `hf-mirror.com` 镜像。

**导入演示语料**（10 份互相引用的虚构产品说明书，含故意设计的冲突与信息缺口）：

```bat
.venv\Scripts\python.exe scripts\make_corpus.py     :: 生成演示语料到 D:\RAG项目\产品说明书\（可改脚本内路径）
.venv\Scripts\python.exe scripts\upload_corpus.py   :: 幂等批量入库（需服务已启动）
```

也可以直接在网页上传自己的 PDF。

**跑评测 / 出报告 / 引用校验：**

```bat
.venv\Scripts\python.exe scripts\run_eval.py                      :: 默认开发集 18 题
.venv\Scripts\python.exe scripts\run_eval.py --file questions_sealed.json --tag sealed
.venv\Scripts\python.exe scripts\make_report.py
.venv\Scripts\python.exe scripts\check_citations.py
```

## API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/documents/upload` | 上传并索引 PDF（含型号/版本/类型选填字段） |
| `GET` | `/api/v1/documents` | 已索引文档清单 |
| `DELETE` | `/api/v1/documents/{document_id}` | 删除文档及其向量 |
| `POST` | `/api/v1/chat` | 提问（支持 `top_k`；复合问题自动拆分） |

```bash
curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d "{\"question\": \"A200 的整机保修多久？滤芯多久换？\", \"top_k\": 4}"
```

## 配置

全部在 `.env`（从 `.env.example` 复制）。核心项：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `LLM_PROVIDER` | `retrieval` | `retrieval`（只检索不调付费模型）/ `deepseek` / `openai` / `ollama` / `gemini` / `claude` |
| `DEEPSEEK_API_KEY` | — | 生成模式需要；模型 `deepseek-flash` |
| `EMBEDDING_MODEL` | multilingual MiniLM | 384 维多语言嵌入 |

## 项目结构

```
app/
  main.py            服务入口（FastAPI）
  routers/           chat、documents 接口层
  services/          检索、子问题拆分、LLM provider（工厂模式）、PDF 解析
  static/index.html  操作页面
scripts/
  doctor.py          23 项交接体检
  check_project.py   接口自检（上传自清理、404 路径）
  run_eval.py        评测（--file/--top-k/--tag/--limit/--ids）
  make_report.py     HTML 可视化报告
  check_citations.py 引用对抗校验
  upload_corpus.py   幂等批量入库
  make_corpus.py     演示语料生成（可复现）
  export_corpus_text.py  语料全文导出（独立出题盲测材料）
  ask_raw.py         裸模型对照（不查知识库直问）
docs/
  STATUS.md          全程开发日志（每日大白话说明+已验证证据）
  corpus_facts.md    语料事实表
  eval/              题库 + 成绩单 + 原始记录（证据链）
```

## License

MIT — 见 [LICENSE](LICENSE)。基于 [panutpl/rag-chatbot-template-starter](https://github.com/panutpl/rag-chatbot-template-starter)（MIT）二次开发，感谢原作者。

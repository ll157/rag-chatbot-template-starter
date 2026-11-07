# 项目状态日志（每日接力用）

## 2026-11-07 ｜ Day1（提前完成环境与基线部分）

**当前分支**：`feature/product-assistant`（基于上游基线提交 `a66e18c`）
**上游**：https://github.com/panutpl/rag-chatbot-template-starter （origin 暂指上游，Fork 完成后改为 origin=个人仓库 / upstream=上游）

### 今天已完成
1. 对齐文档：`D:\RAG项目\AI接力对齐文档.md`（含部署核查、环境实测、风险清单）。发布方式已确认：GitHub Fork 为主 + 发布时镜像 Gitee。
2. 克隆上游 → 检出 `a66e18c` → 新建 `feature/product-assistant` 分支。
3. 虚拟环境：**Python 3.12.15**（uv 托管解释器），项目内 `.venv`。
4. 依赖安装：requirements.txt 全部装成功（镜像：阿里云 `mirrors.aliyun.com/pypi/simple/`；清华源在本机不通）。实际版本锁定见 `requirements.lock.txt`（如 chromadb 1.5.9、sentence-transformers 6.2.0、torch 2.15.0、fastapi 0.162.0、pypdf 7.0.0）。
5. `.env.example` → `.env`（LLM_PROVIDER=retrieval，未配置任何密钥）。
6. 服务启动：`uvicorn app.main:app` 绑定 **127.0.0.1:8000**，`/health` 200。
7. 嵌入模型下载成功：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`（384 维），通过 **HF_ENDPOINT=https://hf-mirror.com** 镜像（直连 HuggingFace 在本机不通）。
8. 示例 PDF（虚构演示资料 `sample_A200_manual_demo.pdf`，1 页）上传入库成功：1 chunk 入 ChromaDB。
9. 检索验证通过：问 "What is the warranty period of the A200?"，返回 sources 含已知原文（filename + page=1 + text + distance≈0.60），retrieval 模式未调用付费 LLM。

### 运行环境记录
- OS：Windows 64 位 + PowerShell；git 2.56.0.windows.2
- Python：3.12.15（默认 `py` 是 3.14.4，未使用）
- 服务命令（当前目录=项目根）：
  `$env:HF_ENDPOINT='https://hf-mirror.com'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

### 已知问题 / 限制
- 接口字段与 README 一致已核对（upload 字段 `file`；ChatRequest 仅 `question`+`top_k`）。
- `.env` 无 OpenAI base_url 字段 → DeepSeek（OpenAI 兼容）接入需在 Day2 给 config 加 base_url 配置并单独测试。
- 清华 PyPI 源、raw.githubusercontent.com、HuggingFace 直连在本机均不通；用阿里云 PyPI + hf-mirror.com 规避。

### 未运行
- run_eval / check_project / doctor 脚本（尚不存在，属 Day2+ 任务）。
- 真实 LLM API 调用（无密钥，Day2 决策）。

### 下一步（Day2，11-08）
1. 用户决策：给 DeepSeek 充少量额度，或申请其他模型 API；我读 openai 适配代码补 base_url。
2. 整理虚构资料事实表（3 个型号，含易混淆型号、旧版、未写能力、受控冲突），用户逐行确认。
3. 30 题分组（18 开发 + 12 封存测试）。
4. doctor / check_project 最小骨架。

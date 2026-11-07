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

## 2026-11-07 ｜ 第二轮：手册作者反馈纠正（4 纠正 + 2 补充）已落地

**作者结论**：整体目标一致，可按计划继续，无需再次等待批准。

### 已执行
1. **写权限显式测试**：项目目录内临时文件 创建→写入→读回→删除 全部成功 → 写权限改为"已验证"（此前凭只读检查推断，系表述错误）。
2. **对齐文档升级 v2**（`D:\RAG项目\AI接力对齐文档.md`）：
   - 第 3 节改名"仓库与运行前提核查"，全文按 已验证/未验证/推测 分级；
   - 更正：GitHub raw 不通=实测；HF 直连=**未测**（此前误写"HF直连失败"）；HF 镜像下载模型成功=实测（Day1）；本机检索链路=已验证（Day1，证据见上）；
   - Git 远程推送权限=未验证（首次 push 时验证）；
   - 第 6 节补充：Gitee 同步规则（不阻塞 GitHub 交付、不未经检查用 `--mirror`、出问题先保 GitHub 与作品集）；12 道封存测试题隔离规则（调提示词/检索逻辑只用 18 道开发题；测试题不用于调试；据测试题修复即记录"已参与调试"）；
   - 克隆流程更正：origin=用户 Fork、upstream=原作者；上游 a66e18c 即基线，不再另造基线提交。
3. **remote 重接**：待用户完成 Fork 后执行（origin 暂指上游）。

### 未验证（如实记录）
- Git 推送权限；真实 LLM API 调用；跨机器复现；HF 直连。

### 下一步（Day2，11-08）
1. 用户决策：给 DeepSeek 充少量额度，或申请其他模型 API；我读 openai 适配代码补 base_url。
2. 整理虚构资料事实表（3 个型号，含易混淆型号、旧版、未写能力、受控冲突），用户逐行确认。
3. 30 题分组（18 开发 + 12 封存测试）。
4. doctor / check_project 最小骨架。

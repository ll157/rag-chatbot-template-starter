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
3. **remote 重接 + 首次推送（已完成，2026-11-07）**：
   - 用户 Fork：https://github.com/ll157/rag-chatbot-template-starter（其 main HEAD = a66e18c，与基线一致）
   - `origin` → ll157/rag-chatbot-template-starter；`upstream` → panutpl/rag-chatbot-template-starter
   - `git push -u origin feature/product-assistant` 成功 → **推送权限已验证**；分支已跟踪 origin/feature/product-assistant

### 未验证（如实记录）
- 真实 LLM API 调用；跨机器复现；HF 直连。

### 下一步（Day2，11-08）
1. 用户决策：给 DeepSeek 充少量额度，或申请其他模型 API；我读 openai 适配代码补 base_url。
2. 整理虚构资料事实表（3 个型号，含易混淆型号、旧版、未写能力、受控冲突），用户逐行确认。
3. 30 题分组（18 开发 + 12 封存测试）。
4. doctor / check_project 最小骨架。

## 2026-11-09 ｜ Day2（模型接入 + 事实表 + 语料 + 题库 + 检查脚本）

### 大白话版今日说明（每日固定结构，跨天与跨 AI 接力保留）
- **今天做了什么**：让 AI 第一次"开口说话"了（之前只会甩原文片段，现在会基于原文写出通顺回答）；编了一套 10 份互相引用、故意有矛盾和缺口的虚构说明书；出好了 30 道考题（18 道平时练习 + 12 道封存期末卷）；写好两个体检脚本并跑通。
- **为什么**：这四样合起来 = 简历上"我做过一个能检索、能生成、有测试成绩单的 RAG 项目"的每一块砖。
- **卡在哪**：第一次填的密钥无效（401，不是 sk- 开头，复制不完整）；用户重建密钥后一次通过。
- **你要做什么**：无（今天你已完成的动作：认可事实表、重建密钥）。明早开始 Day3。

### 已验证（附证据）
1. **DeepSeek 接入**（提交 31c04eb）：新增 `DeepSeekProvider`（chat.completions，因上游 openai 走 OpenAI Responses API 不兼容 DeepSeek）+ config 三项 + factory 注册。
   - 直连 provider 生成：输入 A200 保修问题 + 手册原文片段 → 输出"整机保修 24 个月……核心部件 36 个月"（正确）。
   - 端到端 HTTP（LLM_PROVIDER=deepseek）：上传《A200_用户手册_v3.pdf》（4 页 4 切片）→ POST /api/v1/chat → 中文回答正确，sources 全部指向该手册。
   - 模型：deepseek-flash；base_url https://api.deepseek.com（2026-11 官方文档核实；deepseek-chat 已不在现役文档）。
   - **模型还主动指出了 Day1 旧演示 PDF 与新语料的保修冲突**（正确的"报冲突"行为）→ 已删除旧演示 PDF 避免语料污染。
2. **事实表**：docs/corpus_facts.md（3 型号 9 项事实 + C1 受控冲突 + N1–N3 未涉及），用户已逐行认可。
3. **语料 10 份 20 页**：D:\RAG项目\产品说明书\（仓库外，按用户指定），互相引用网络与"乱序设计清单"见 index.md；生成脚本 scripts/make_corpus.py 可复现；pypdf 验证页数与文本提取。
4. **题库 30 道**：docs/eval/questions_dev.md（18 题，四类 4/5/4/5）+ docs/eval/sealed/questions_sealed.md（12 题，4/3/2/3，文件头写明隔离规则）。题面全部出自事实表。
5. **检查脚本**：scripts/doctor.py（19 项，0 需处理）、scripts/check_project.py（6 项，0 需处理，含上传自清理与 404 错误路径）。chat 检查项在付费 provider 下按设计跳过。

### 未验证 / 待办
- 30 题尚未在批量入库后的索引上运行（Day3：批量上传 10 份 → 检索对照 → Day5 提示词，Day7 冻结，Day8 跑封存题）。
- check_project 的 chat 检查在 retrieval 模式下的实跑（切换回 retrieval 时验证）。
- 跨机器复现、HF 直连（维持未测）。

### 环境备注（新增）
- 当前 .env：LLM_PROVIDER=retrieval（默认）；测试时用环境变量 `$env:LLM_PROVIDER='deepseek'` 临时覆盖，不改动 .env。
- 运行中的服务：deepseek 模式，127.0.0.1:8000，索引内现有 1 份文档（A200_用户手册_v3.pdf）。
- 服务启动命令不变，需生成模式时加：`$env:LLM_PROVIDER='deepseek'`。

## 2026-11-10 ｜ Day3（批量入库 + 自动评测基线 + 质检）

### 大白话版今日说明（每日固定结构）
- **今天做了什么**：10 份说明书全部喂进知识库（幂等脚本，重复跑不会重复入库）；把 18 道开发题转成机器可读格式并写了自动考试脚本；AI 第一次参加摸底考试——**18/18（100%，关键词宽判分）**；对全部脚本做了可靠性验收。
- **为什么**：先有基线分数，以后每次优化（Day5 提示词等）才有"改进了多少"的量化证据——这是简历上"效果评估"能力的起点。
- **卡在哪**：①用户端口冲突——两个服务抢 8000 端口导致全部超时（教训：一个端口只能一个服务）；②判分器冤案——AI 对 D-18 实际答对了（"无法从文档中找到"），但否定词库缺"无法从"这个说法，已补；③D-08 出现一次偶发生成截断（重试即复现正常，已记录在案）。
- **你要做什么**：无（已确认：今后 git push 全部由 AI 代劳；用户已亲手体验 3 次）。

### 已验证（附证据）
1. **批量入库**（提交 d8988aa）：`scripts/upload_corpus.py`（幂等设计：先查已入库清单再上传，失败可见+汇总+退出码）→ 10/10 入库成功（9 上传 + 1 跳过已入库）。索引现有 10 份文档。
2. **自动评测基线**（提交 9d4397a）：`docs/eval/questions_dev.json`（18 题机器化，三判分规则）+ `scripts/run_eval.py`（逐题调 /api/v1/chat → 判分 → CSV 成绩单 + JSONL 原始记录，utf-8-sig 防 Excel 乱码，文件名带时间戳）。
   - 第一次跑 16/18：D-08 偶发截断 + D-18 判分器漏词（两案均查实，原始记录 eval_20261110_1812_raw.jsonl）。
   - 修复后重跑 **18/18**（eval_20261110_1815.csv）；D-14 冲突题模型同时提到 24 与 36 并按资料裁决；4 道"无答案"题全部如实回答未编造。
   - 诚实备注：关键词判分为宽标准（只证"提到"，不证"语境全对"）；封存 12 题未考。
3. **脚本可靠性验收**：upload_corpus 重跑 → 10 跳过 0 上传 0 失败（幂等 ✅）；doctor.py 19 项 0 需处理；check_project.py 6 项全通过（含上传自清理，索引仍为 10 份）。

### 未验证 / 待办
- 100% 基线是"宽判分+开发集"结果：Day5 提示词优化后重跑对比；Day7 冻结、Day8 跑 12 道封存题见真章。
- 偶发截断根因未查（网络/生成抖动），暂记录现象；如再现在评测中会以 ERROR 可见。
- 跨机器复现、HF 直连、retrieval 模式 chat 实跑（维持未测）。

### 环境备注（新增）
- 服务改由 AI 后台方式管理（无窗口，日志 uvicorn.err.log / uvicorn.out.log），用户不再手动开服务。
- **端口冲突教训**：启动服务前必须确认旧进程已关（曾出现 venv 与 uv 全局 python 双进程抢 8000，全部假死）。
- 教学规则更新：git push 此后由 AI 代劳（用户已体验 3 次：94678f9 / d8988aa / 9d4397a 前）。
- 索引现状：10 份正式语料，无多余文档。



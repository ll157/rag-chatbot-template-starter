# -*- coding: utf-8 -*-
"""doctor.py —— 环境体检（骨架版）
用法：.\\.venv\\Scripts\\python.exe scripts\\doctor.py
输出中文三态：[通过] / [需处理] / [未检查]，不打印任何密钥内容。
"""
import importlib
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OK, WARN, SKIP = "[通过]  ", "[需处理]", "[未检查]"
results = []


def add(state, name, detail, next_step=""):
    results.append((state, name, detail, next_step))


# 1. Python 版本
v = sys.version_info
if (v.major, v.minor) == (3, 12):
    add(OK, "Python 版本", f"{v.major}.{v.minor}.{v.micro}")
else:
    add(WARN, "Python 版本", f"{v.major}.{v.minor}.{v.micro}（项目用 3.12.15 的 venv 运行，请确认使用 .venv）")

# 2. 关键依赖可导入
for mod in ["fastapi", "uvicorn", "chromadb", "sentence_transformers", "openai", "pypdf", "pydantic_settings"]:
    try:
        importlib.import_module(mod)
        add(OK, f"依赖 {mod}", "可导入")
    except Exception as e:
        add(WARN, f"依赖 {mod}", f"导入失败：{type(e).__name__}", "在 .venv 中重装该依赖")

# 3. 数据目录存在且可写
for d in ["数据/上传文件", "数据/向量库"]:
    p = ROOT / d
    if p.exists():
        try:
            probe = p / ".doctor_probe"
            probe.write_text("x", encoding="utf-8")
            probe.unlink()
            add(OK, f"目录 {d}", "存在且可写")
        except Exception as e:
            add(WARN, f"目录 {d}", f"不可写：{e}")
    else:
        add(WARN, f"目录 {d}", "不存在", "启动一次服务会自动创建")

# 4. 端口 8000
s = socket.socket()
s.settimeout(1)
port_busy = s.connect_ex(("127.0.0.1", 8000)) == 0
s.close()
add(OK if port_busy else SKIP, "端口 8000", "有服务在监听（先看 /health）" if port_busy else "无监听（服务未启动）",
    "" if port_busy else "启动：.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000")

# 5. 嵌入模型缓存
cache = Path.home() / ".cache" / "torch" / "sentence_transformers"
hf_cache = Path.home() / ".cache" / "huggingface"
if cache.exists() or hf_cache.exists():
    add(OK, "嵌入模型缓存", "本地已有缓存目录")
else:
    add(SKIP, "嵌入模型缓存", "未找到缓存目录", "首次上传文档时会自动下载（需 HF_ENDPOINT=https://hf-mirror.com）")

# 6. LLM_PROVIDER 与密钥（只显示 已配置/未配置）
try:
    from app.config import settings
    add(OK, "LLM_PROVIDER", settings.llm_provider)
    for label, val in [
        ("DEEPSEEK_API_KEY", settings.deepseek_api_key),
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("GEMINI_API_KEY", settings.gemini_api_key),
        ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
    ]:
        add(OK if val else SKIP, label, "已配置（长度 %d，不显示内容）" % len(val) if val else "未配置")
    if settings.llm_provider == "retrieval":
        add(SKIP, "生成模式", "当前为 retrieval（只用检索，不调模型）", "要生成回答请设 LLM_PROVIDER=deepseek")
except Exception as e:
    add(WARN, "配置读取", f"失败：{e}", "检查 .env 与 app/config.py")

# 7. .env 不入库复查
try:
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    add(OK if ".env" in gi else WARN, ".gitignore 含 .env", "已排除" if ".env" in gi else "未排除，存在泄密风险！")
except Exception as e:
    add(WARN, ".gitignore", f"读取失败：{e}")

print("=" * 62)
print("doctor 环境体检报告（%s）" % sys.platform)
print("=" * 62)
for state, name, detail, nxt in results:
    print(f"{state} {name:<28} {detail}")
    if nxt:
        print(f"         └ 下一步：{nxt}")
n_warn = sum(1 for r in results if r[0] == WARN)
print("-" * 62)
print(f"共 {len(results)} 项：需处理 {n_warn} 项；其余通过或未检查。")

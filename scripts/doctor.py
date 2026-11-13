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

# 4. 端口 8000：要能分清"自家服务在跑"还是"被别的程序占了"
s = socket.socket()
s.settimeout(1)
port_busy = s.connect_ex(("127.0.0.1", 8000)) == 0
s.close()
if not port_busy:
    add(SKIP, "端口 8000", "无监听（服务未启动）",
        "启动：.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
else:
    # 有监听，进一步问一句 /health：答得上来才是本项目服务
    try:
        import json as _json
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as resp:
            health = _json.loads(resp.read().decode("utf-8"))
        add(OK, "端口 8000", f"本项目服务在运行（/health: {health}）")
    except Exception:
        add(WARN, "端口 8000", "被占用但 /health 不响应（可能是别的程序/另一个 python 抢了端口）",
            "查占用：netstat -ano | findstr :8000 ；结束后重启本项目服务")

# 5. 嵌入模型缓存
cache = Path.home() / ".cache" / "torch" / "sentence_transformers"
hf_cache = Path.home() / ".cache" / "huggingface"
if cache.exists() or hf_cache.exists():
    add(OK, "嵌入模型缓存", "本地已有缓存目录")
else:
    add(SKIP, "嵌入模型缓存", "未找到缓存目录", "首次上传文档时会自动下载（需 HF_ENDPOINT=https://hf-mirror.com）")

# 6. LLM_PROVIDER 与密钥（只显示 是 / 否，不泄露任何内容）
try:
    from app.config import settings
    add(OK, "LLM_PROVIDER", settings.llm_provider)
    for label, val in [
        ("DEEPSEEK_API_KEY", settings.deepseek_api_key),
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("GEMINI_API_KEY", settings.gemini_api_key),
        ("ANTHROPIC_API_KEY", settings.anthropic_api_key),
    ]:
        add(OK if val else SKIP, label, "是（已配置）" if val else "否（未配置）")
    if settings.llm_provider == "retrieval":
        add(SKIP, "生成模式", "当前为 retrieval（只用检索，不调模型）", "要生成回答请设 LLM_PROVIDER=deepseek")

    # 6.1 路径一致性：.env 里如果写了旧路径会覆盖代码默认值（2026-11-10 踩过的坑）
    for label, path_str in [
        ("上传目录", settings.upload_dir),
        ("向量库目录", settings.chroma_dir),
        ("文档清单", settings.documents_metadata_path),
    ]:
        p = Path(path_str)
        p = p if p.is_absolute() else ROOT / p
        if p.exists():
            add(OK, f"配置路径 {label}", str(path_str))
        else:
            add(WARN, f"配置路径 {label}", f"{path_str} 不存在",
                "检查 .env 是否残留旧路径（.env 优先级高于代码默认值）")

    # 6.2 模型连通性：只测网络端口通不通，不花钱、不调用模型
    if settings.llm_provider == "deepseek" and settings.deepseek_api_key:
        import urllib.parse
        host = urllib.parse.urlparse(settings.deepseek_base_url).hostname or "api.deepseek.com"
        try:
            s2 = socket.create_connection((host, 443), timeout=5)
            s2.close()
            add(OK, "模型接口连通性", f"{host}:443 可连接")
        except Exception as e:
            add(WARN, "模型接口连通性", f"{host}:443 连接失败（{type(e).__name__}）",
                "检查网络/代理；离线时可用 LLM_PROVIDER=retrieval 降级")
except Exception as e:
    add(WARN, "配置读取", f"失败：{e}", "检查 .env 与 app/config.py")

# 6.3 知识库规模：文档清单里登记了几份
try:
    meta_path = Path(settings.documents_metadata_path)
    meta_path = meta_path if meta_path.is_absolute() else ROOT / meta_path
    import json as _json2
    _data = _json2.loads(meta_path.read_text(encoding="utf-8"))
    docs = _data if isinstance(_data, list) else _data.get("documents", [])
    add(OK if docs else WARN, "知识库文档数", f"已登记 {len(docs)} 份",
        "" if docs else "先跑 upload_corpus.py 批量入库")
except Exception as e:
    add(SKIP, "知识库文档数", f"读取失败：{type(e).__name__}")

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

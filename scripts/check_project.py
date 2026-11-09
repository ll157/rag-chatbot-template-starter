# -*- coding: utf-8 -*-
"""check_project.py —— 项目自检（骨架版）
用法：先启动服务，再运行 .\\.venv\\Scripts\\python.exe scripts\\check_project.py
检查：/health、文档列表、上传测试文档（自清理）、问答检索、错误路径(404)。
说明：LLM_PROVIDER=retrieval 时问答检查免费；为 deepseek 等付费模式时问答项跳过并说明。
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BASE = "http://127.0.0.1:8000"
OK, WARN, SKIP = "[通过]  ", "[需处理]", "[未检查]"
results = []


def add(state, name, detail):
    results.append((state, name, detail))


def req(method, path, body=None, headers=None, timeout=30):
    r = urllib.request.Request(BASE + path, method=method, headers=headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def upload_pdf(path: Path):
    boundary = "----doctorBoundary7f3a"
    payload = path.read_bytes()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{path.name}\"\r\nContent-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")
    r = urllib.request.Request(BASE + "/api/v1/documents/upload", data=body, method="POST")
    r.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(r, timeout=120) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


# 1. /health
try:
    st, data = req("GET", "/health", timeout=10)
    add(OK if st == 200 else WARN, "GET /health", f"HTTP {st} {data}")
except Exception as e:
    add(WARN, "GET /health", f"服务不可达：{e}", "先启动服务再运行本脚本")
    _print_and_exit = True
else:
    _print_and_exit = False

if not _print_and_exit:
    # 2. 文档列表
    try:
        st, docs = req("GET", "/api/v1/documents", timeout=10)
        n = len(docs if isinstance(docs, list) else docs.get("documents", []))
        add(OK if st == 200 else WARN, "GET /api/v1/documents", f"HTTP {st}，当前 {n} 份文档")
    except Exception as e:
        add(WARN, "GET /api/v1/documents", f"失败：{e}")

    # 3. 上传测试文档（用最小语料：宣传单页；完成后删除，自清理）
    test_pdf = Path(r"D:\RAG项目\产品说明书\A200_促销宣传单页.pdf")
    if test_pdf.exists():
        try:
            st, up = upload_pdf(test_pdf)
            doc_id = up.get("document_id")
            add(OK if st == 200 and doc_id else WARN, "POST 上传测试", f"HTTP {st}，document_id={str(doc_id)[:8]}…，切片 {up.get('chunk_count')}")
            # 4. 问答检索（retrieval 免费模式才做）
            try:
                from app.config import settings
                provider = settings.llm_provider
            except Exception:
                provider = "unknown"
            if provider == "retrieval":
                try:
                    st, chat = req("POST", "/api/v1/chat", body={"question": "A200 保修多久？", "top_k": 3}, timeout=60)
                    has_src = bool(chat.get("sources"))
                    add(OK if st == 200 and has_src else WARN, "POST /chat（retrieval）", f"HTTP {st}，引用 {len(chat.get('sources', []))} 条")
                except Exception as e:
                    add(WARN, "POST /chat（retrieval）", f"失败：{e}")
            else:
                add(SKIP, "POST /chat", f"当前 provider={provider}（会花钱），骨架阶段跳过；评测见 Day3/Day8")
            # 5. 自清理：删除测试文档
            try:
                st, _ = req("DELETE", f"/api/v1/documents/{doc_id}", timeout=30)
                add(OK if st == 200 else WARN, "DELETE 测试文档", f"HTTP {st}（索引已还原）")
            except urllib.error.HTTPError as e:
                add(WARN, "DELETE 测试文档", f"HTTP {e.code}", "请手动在 /docs 删除该测试文档")
        except Exception as e:
            add(WARN, "上传测试文档", f"失败：{e}")
    else:
        add(SKIP, "上传测试文档", f"未找到 {test_pdf}", "先运行 scripts/make_corpus.py 生成语料")

    # 6. 错误路径：不存在的 document_id → 404
    try:
        req("DELETE", "/api/v1/documents/00000000-0000-0000-0000-000000000000", timeout=10)
        add(WARN, "错误路径(404)", "删除不存在的文档未返回 404")
    except urllib.error.HTTPError as e:
        add(OK if e.code == 404 else WARN, "错误路径(404)", f"HTTP {e.code}（预期 404）")
    except Exception as e:
        add(WARN, "错误路径(404)", f"失败：{e}")

print("=" * 62)
print("check_project 自检报告")
print("=" * 62)
for state, name, detail in results:
    print(f"{state} {name:<26} {detail}")
n_warn = sum(1 for r in results if r[0] == WARN)
print("-" * 62)
print(f"共 {len(results)} 项：需处理 {n_warn} 项。")

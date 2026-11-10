"""批量上传语料到 RAG 服务（幂等：同名已入库则跳过，可重复运行）。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\upload_corpus.py

前置条件：
    服务已启动（127.0.0.1:8000），语料目录存在。
"""

import sys
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8000"
CORPUS_DIR = Path(r"D:\RAG项目\产品说明书")
UPLOAD_TIMEOUT = 300  # 单个文件上传+入库+嵌入 的超时（秒）


def check_server() -> None:
    """启动前先确认服务活着，失败就给出明确提示并退出。"""
    try:
        resp = requests.get(f"{BASE}/health", timeout=5)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[前置失败] 服务未就绪: {exc}")
        print("请先启动服务，再运行本脚本。")
        sys.exit(1)


def get_existing_filenames() -> set:
    """从服务取已入库的文件名集合，用于跳过重复上传。"""
    resp = requests.get(f"{BASE}/api/v1/documents", timeout=10)
    resp.raise_for_status()
    docs = resp.json()
    if isinstance(docs, dict):
        docs = docs.get("documents", [])
    return {d.get("original_filename", "") for d in docs}


def main() -> None:
    check_server()

    if not CORPUS_DIR.exists():
        print(f"[前置失败] 语料目录不存在: {CORPUS_DIR}")
        sys.exit(1)

    existing = get_existing_filenames()
    print(f"服务当前已入库 {len(existing)} 份: {sorted(existing)}\n")

    pdfs = sorted(CORPUS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[前置失败] 目录中没有 PDF: {CORPUS_DIR}")
        sys.exit(1)

    ok = skipped = failed = 0
    failed_names = []

    for pdf in pdfs:
        if pdf.name in existing:
            print(f"[跳过] {pdf.name} （已入库）")
            skipped += 1
            continue
        try:
            with pdf.open("rb") as fh:
                resp = requests.post(
                    f"{BASE}/api/v1/documents/upload",
                    files={"file": (pdf.name, fh, "application/pdf")},
                    timeout=UPLOAD_TIMEOUT,
                )
            resp.raise_for_status()
            info = resp.json()
            chunks = info.get("chunk_count") or info.get("chunks") or "?"
            print(f"[成功] {pdf.name} -> {chunks} 个切片")
            ok += 1
        except Exception as exc:
            # 失败必须看得见：记名字、继续传后面的，最后统一汇报
            detail = str(exc)[:150]
            print(f"[失败] {pdf.name}: {detail}")
            failed += 1
            failed_names.append(pdf.name)

    print("\n===== 汇总 =====")
    print(f"目录共 {len(pdfs)} 份 PDF | 成功 {ok} | 跳过 {skipped} | 失败 {failed}")
    if failed_names:
        print("失败清单:")
        for name in failed_names:
            print(f"  - {name}")
        sys.exit(2)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""export_corpus_text.py —— 导出语料全文（供"隔离式外包独立出题"盲测用）。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\export_corpus_text.py

产出：
    D:\\RAG项目\\独立出题材料.txt（仓库外，避免与代码混淆）

用途说明（教学）：
    独立第三方出题的铁律是"信息隔离"——出题 AI 只能看产品资料，
    不能看代码、开发题、调优记录。本脚本把语料 PDF 的文字抽成一个
    纯文本文件，作为给出题 AI 的唯一材料。
"""

import io
import json
import sys
from pathlib import Path

from pypdf import PdfReader

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "数据" / "文档清单.json"
OUT = Path(r"D:\RAG项目\独立出题材料.txt")

sys.path.insert(0, str(ROOT))
from app.config import settings  # noqa: E402

_upload_dir = Path(settings.upload_dir)
_upload_dir = _upload_dir if _upload_dir.is_absolute() else ROOT / _upload_dir


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    docs = data if isinstance(data, list) else data.get("documents", [])

    parts = []
    for doc in docs:
        original = doc.get("original_filename")
        pdf_path = _upload_dir / doc.get("saved_filename", "")
        if not pdf_path.exists():
            print(f"跳过（文件缺失）：{original}")
            continue
        text_parts = []
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
        body = "\n".join(text_parts).strip()
        parts.append(f"【资料：{original}】\n{body}")
        print(f"已抽取：{original}（{len(body)} 字）")

    OUT.write_text("\n\n".join(parts), encoding="utf-8")
    total = OUT.stat().st_size
    print(f"\n已生成：{OUT}（约 {total // 1024} KB）")
    print("交给独立出题 AI 时：只发这个文件的内容 + 出题指令，其他一概不说。")


if __name__ == "__main__":
    main()

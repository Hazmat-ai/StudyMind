import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from fastapi import HTTPException, UploadFile


async def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(422, "Choose a PDF file")
        data = await file.read(5 * 1024 * 1024 + 1)
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(413, "PDF files must be no larger than 5 MiB")
        if not data.startswith(b"%PDF-"):
            raise HTTPException(422, "The uploaded file is not a readable PDF")
        with tempfile.TemporaryDirectory(prefix="studymind-pdf-") as directory:
            path = Path(directory) / "source.pdf"
            path.write_bytes(data)
            worker = Path(__file__).with_name("pdf_worker.py")
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                str(worker),
                str(path),
                cwd=directory,
                env={"PATH": os.defpath, "LANG": "C.UTF-8"},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                output, _ = await asyncio.wait_for(process.communicate(), timeout=9)
            except (TimeoutError, asyncio.CancelledError):
                process.kill()
                await process.wait()
                raise HTTPException(
                    422, "PDF parsing timed out. Try fewer pages or paste text instead."
                )
            try:
                result = json.loads(output)
            except (ValueError, TypeError):
                raise HTTPException(
                    422, "This PDF could not be read within safety limits"
                )
            if process.returncode or "error" in result:
                raise HTTPException(
                    422, result.get("error", "This PDF could not be read")
                )
            return result["content"]
    finally:
        await file.close()

"""Invoked in a short-lived isolated subprocess, never imported by request handlers."""

import json
import sys


class PDFInputError(Exception):
    pass


def main():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        import pymupdf as fitz

        with fitz.open(sys.argv[1]) as document:
            if document.needs_pass:
                raise PDFInputError("Password-protected PDFs are not supported")
            if document.page_count > 40:
                raise PDFInputError("Use a PDF with at most 40 pages")
            chunks = []
            length = 0
            for page in document:
                chunk = page.get_text()
                length += len(chunk) + (1 if chunks else 0)
                if length > 12000:
                    raise PDFInputError(
                        "This PDF has more than 12,000 text characters. Upload selected pages or paste an excerpt."
                    )
                chunks.append(chunk)
            text = "\n".join(chunks).strip()
            if len(text) < 50:
                raise PDFInputError(
                    "This PDF has too little readable text. Scanned PDFs need OCR before upload."
                )
            print(json.dumps({"content": text}))
    except PDFInputError as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(2)
    except Exception:
        print(json.dumps({"error": "This PDF could not be read safely"}))
        sys.exit(2)


if __name__ == "__main__":
    main()

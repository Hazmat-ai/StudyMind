import pymupdf as fitz
from conftest import login


def make_pdf(
    text="Tables contain rows. Primary keys identify each row. Foreign keys reference related tables. "
    * 3,
):
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(30, 30, 560, 750), text)
    data = document.tobytes()
    document.close()
    return data


def test_pdf_extraction_and_malformed_files(client):
    auth = login(client)
    response = client.post(
        "/api/generate/extract-pdf",
        headers=auth,
        files={"file": ("NOTES.PDF", make_pdf(), "application/pdf")},
    )
    assert response.status_code == 200, response.text
    assert "Primary keys" in response.json()["content"]
    malformed = client.post(
        "/api/generate/extract-pdf",
        headers=auth,
        files={"file": ("notes.pdf", b"%PDF-not-valid", "application/pdf")},
    )
    assert malformed.status_code == 422
    assert "/tmp/" not in malformed.text
    fake = client.post(
        "/api/generate/extract-pdf",
        headers=auth,
        files={"file": ("notes.pdf", b"not a pdf", "application/pdf")},
    )
    assert fake.status_code == 422


def test_scanned_and_oversized_pdf_fail_with_recovery(client):
    auth = login(client)
    blank = client.post(
        "/api/generate/extract-pdf",
        headers=auth,
        files={"file": ("blank.pdf", make_pdf(""), "application/pdf")},
    )
    assert blank.status_code == 422
    assert "OCR" in blank.json()["detail"]
    huge = client.post(
        "/api/generate/extract-pdf",
        headers=auth,
        files={
            "file": ("huge.pdf", b"%PDF-" + b"x" * (5 * 1024 * 1024), "application/pdf")
        },
    )
    assert huge.status_code == 413


def test_encrypted_and_over_page_limit_are_rejected(client):
    auth = login(client)
    document = fitz.open()
    for _ in range(41):
        document.new_page()
    too_many = document.tobytes()
    document.close()
    document = fitz.open(stream=make_pdf(), filetype="pdf")
    encrypted = document.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner-secret",
        user_pw="reader-secret",
    )
    document.close()
    for name, data in [("long.pdf", too_many), ("locked.pdf", encrypted)]:
        result = client.post(
            "/api/generate/extract-pdf",
            headers=auth,
            files={"file": (name, data, "application/pdf")},
        )
        assert result.status_code == 422, result.text


def test_busy_parser_rejects_without_starting_another_process(client, application):
    auth = login(client)
    client.portal.call(application.state.pdf_slots.acquire)
    try:
        result = client.post(
            "/api/generate/extract-pdf",
            headers=auth,
            files={"file": ("notes.pdf", make_pdf(), "application/pdf")},
        )
        assert result.status_code == 429
        assert result.headers["retry-after"] == "5"
        assert client.get("/api/health").status_code == 200
    finally:
        client.portal.call(application.state.pdf_slots.release)

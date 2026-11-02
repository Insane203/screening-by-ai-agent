
import fitz


def extract_text_from_pdf(uploaded_file):
    """Extract text from an uploaded PDF resume."""

    document = fitz.open(
        stream=uploaded_file.getvalue(),
        filetype="pdf"
    )

    try:
        pages = []

        for page in document:
            pages.append(page.get_text())

        return "\n".join(pages).strip()

    finally:
        document.close()

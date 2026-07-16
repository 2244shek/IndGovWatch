import os
import tempfile
import httpx
import pdfplumber

async def parse_pdf_to_markdown(pdf_url: str) -> str:
    """
    Downloads a PDF from a URL to a local /tmp/ folder,
    parses its text content into clean Markdown using pdfplumber,
    and safely deletes the temporary file afterwards.
    """
    # Ensure local /tmp/ directory exists (creating it relative/absolute safely)
    tmp_dir = "/tmp"
    try:
        os.makedirs(tmp_dir, exist_ok=True)
    except Exception:
        # Fallback for Windows if /tmp cannot be created at drive root due to permissions
        tmp_dir = os.path.join(tempfile.gettempdir(), "tmp")
        os.makedirs(tmp_dir, exist_ok=True)

    # Generate a unique temp file path
    filename = f"temp_{os.urandom(8).hex()}.pdf"
    temp_file_path = os.path.join(tmp_dir, filename)

    try:
        # Download the file asynchronously
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0, verify=False) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            with open(temp_file_path, "wb") as f:
                f.write(resp.content)

        # Parse it into clean Markdown text using pdfplumber
        markdown_pages = []
        with pdfplumber.open(temp_file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # Basic cleaning/formatting to markdown
                    markdown_pages.append(f"## Page {i + 1}\n\n{text}")

        if not markdown_pages:
            return "No text content could be extracted from this PDF."

        return "\n\n".join(markdown_pages)

    finally:
        # Safely delete the file afterward
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"[pdf_handler] Warning: Failed to delete temp file {temp_file_path}: {e}")

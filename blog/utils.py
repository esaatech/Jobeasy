import html
import re


def normalize_blog_body(body: str) -> str:
    """
    Fix body HTML when raw markup was pasted into CKEditor and stored escaped
    (e.g. &lt;p&gt; instead of <p>).
    """
    if not body or not isinstance(body, str):
        return body or ""

    if "&lt;" not in body and "&gt;" not in body:
        return body

    normalized = html.unescape(body)
    # CKEditor sometimes wraps pasted HTML in <p>…</p> with <br> between blocks
    normalized = re.sub(r"<p>\s*<br>\s*", "<p>", normalized)
    normalized = re.sub(r"<br>\s*</p>", "</p>", normalized)
    normalized = re.sub(r"</p>\s*<p>\s*<h", "</p><h", normalized)
    return normalized

"""Step 8: word count of the submission manuscript against the Brief Article limit (Cognition and Emotion).

The journal's limit is 4,000 words INCLUDING abstract, references and footnotes (the stricter of its two wordings).
This script counts the compiled PDF (so every generated number is counted as printed): everything from the abstract to
the end of the reference list, i.e. abstract, keywords, main text, statements and references. The title page and the
figure pages at the end (figures and their captions) are not counted; they are reported separately.

Run after compiling:  cd manuscript && latexmk -pdf manuscript.tex  then  uv run python analysis/08_word_count.py
"""
import re
import sys
from pathlib import Path

from pypdf import PdfReader

PDF = Path(__file__).resolve().parent.parent / "manuscript" / "manuscript.pdf"
LIMIT = 4000
ABSTRACT_LIMIT = 200
RUNNING_HEAD = "MOMENT-TO-MOMENT AFFECT"


def page_texts(path):
    """Text of each page, without the running head and page number."""
    texts = []
    for page in PdfReader(path).pages:
        lines = [line for line in (page.extract_text() or "").splitlines()
                 if line.strip() and not line.strip().startswith(RUNNING_HEAD) and not line.strip().isdigit()]
        texts.append("\n".join(lines))
    return texts


def words(text):
    return len(re.findall(r"\S+", text))


def section(text, start, end):
    """Text between two headings (end None = to the end)."""
    begin = text.find(start)
    if begin < 0:
        return ""
    stop = text.find(end, begin + len(start)) if end else -1
    return text[begin:stop] if stop > 0 else text[begin:]


def main():
    texts = page_texts(PDF)
    # Page 1 is the title page. Figure pages start with "Figure N".
    body_pages, figure_pages = [], []
    for text in texts[1:]:
        (figure_pages if re.match(r"\s*Figure \d", text) else body_pages).append(text)
    body = "\n".join(body_pages)
    body = body[body.find("Abstract"):]

    parts = {
        "abstract + keywords": section(body, "Abstract", "Introduction"),
        "main text (Introduction to Discussion)": section(body, "Introduction", "Acknowledgements"),
        "statements": section(body, "Acknowledgements", "References"),
        "references": section(body, "References", None),
    }
    total = words(body)
    print(f"Counted from the abstract to the end of the references: {total} words (limit {LIMIT})")
    for name, text in parts.items():
        print(f"  {name:42s} {words(text):5d}")
    print(f"  (figure pages, not counted: {sum(words(t) for t in figure_pages)} words incl. captions)")
    abstract = words(section(body, "Abstract", "Keywords")) - 1  # minus the heading
    print(f"Abstract alone: {abstract} words (limit {ABSTRACT_LIMIT})"
          + ("" if abstract <= ABSTRACT_LIMIT else f"  OVER by {abstract - ABSTRACT_LIMIT}"))
    print("WITHIN LIMIT" if total <= LIMIT else f"OVER LIMIT by {total - LIMIT} words")
    return 0 if total <= LIMIT and abstract <= ABSTRACT_LIMIT else 1


if __name__ == "__main__":
    sys.exit(main())

"""Step 9: package the Cognition and Emotion submission (LaTeX route: compiled PDF + ZIP of the sources incl. .bib).

Copies the manuscript sources into submission/source/, test-compiles them there in isolation (so the ZIP is known to be
complete), and writes:
  submission/manuscript.pdf               compiled manuscript
  submission/manuscript_source.zip        manuscript.tex, references.bib, generated/numbers.tex, figures
  submission/supplementary_material.pdf   for Figshare
submission/ is git-ignored (it is rebuilt from the repository).

Run after compiling manuscript and supplement:  uv run python analysis/09_package_submission.py
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "manuscript"
OUT = ROOT / "submission"
SOURCE_FILES = ["manuscript.tex", "references.bib", "generated/numbers.tex", "figures/figure1.pdf",
                "figures/figure2.pdf"]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    source = OUT / "source"
    for name in SOURCE_FILES:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MANUSCRIPT / name, target)

    # Compile the copied sources on their own: if this works, nothing is missing from the ZIP.
    build = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "manuscript.tex"],
                           cwd=source, capture_output=True, text=True)
    if build.returncode != 0:
        print(build.stdout[-3000:])
        sys.exit("The packaged sources do not compile on their own; see the log above.")
    shutil.copy2(source / "manuscript.pdf", OUT / "manuscript.pdf")
    shutil.copy2(MANUSCRIPT / "supplement.pdf", OUT / "supplementary_material.pdf")

    with zipfile.ZipFile(OUT / "manuscript_source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in SOURCE_FILES:
            archive.write(source / name, name)
    print("wrote", *(p.name for p in sorted(OUT.glob("*.*"))))


if __name__ == "__main__":
    main()

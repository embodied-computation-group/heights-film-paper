#!/usr/bin/env bash
# Build the manuscript and supplement and keep a numbered copy of each draft:
#   builds/manuscript_r01.pdf, builds/supplement_r01.pdf, then r02, r03, ...
# Builds happen in builds/tmp/, so a PDF open in a viewer never blocks the build.
# builds/ is not committed. The committed manuscript.pdf and supplement.pdf are rebuilt separately
# (latexmk -pdf manuscript.tex supplement.tex) when a version is final.
#
# Run from anywhere:  bash manuscript/build.sh
set -e
cd "$(dirname "$0")"
mkdir -p builds/tmp
if ! latexmk -pdf -interaction=nonstopmode -outdir=builds/tmp manuscript.tex supplement.tex \
        > builds/tmp/latexmk_log.txt 2>&1; then
    echo "Build failed: see manuscript/builds/tmp/latexmk_log.txt"
    exit 1
fi
n=1
while [ -e "builds/manuscript_r$(printf %02d "$n").pdf" ]; do n=$((n + 1)); done
r=$(printf %02d "$n")
cp builds/tmp/manuscript.pdf "builds/manuscript_r$r.pdf"
cp builds/tmp/supplement.pdf "builds/supplement_r$r.pdf"
echo "Wrote manuscript/builds/manuscript_r$r.pdf and manuscript/builds/supplement_r$r.pdf"

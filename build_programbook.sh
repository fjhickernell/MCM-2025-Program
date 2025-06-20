#!/bin/bash

# This script compiles the MCM program book and generates schedule PDFs.
# 
# You can run it directly with:
#   bash build_programbook.sh
#
# If you see a "Permission denied" error, you may need to make it executable:
#   chmod +x build_programbook.sh
#
# Alternatively, use the Makefile target:
#   make pgm

echo "*** Compiling LaTeX files in MCM_ProgramBook_TEX directory..."

USE_TIMESTAMP=$1
if [ "$USE_TIMESTAMP" = "dated" ]; then
    timestamp=$(date +%Y_%m_%d_%H_%M_%S)
    suffix="_${timestamp}"
else
    suffix=""
fi

TEXYEAR=${2:-2025}  # Default to 2025 if not provided
TEXBIN=/usr/local/texlive/${TEXYEAR}/bin/universal-darwin


echo "Using filename suffix: $suffix"

cp preprocess/out/*.tex MCM_ProgramBook_TEX || exit 1
cd MCM_ProgramBook_TEX || exit 1

# Compile LaTeX with specified pdflatex
PATH="$TEXBIN:$PATH" pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 || tail -n 100 MCM2025_book.log
PATH="$TEXBIN:$PATH" pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1

# Rename with suffix
mv MCM2025_book.pdf "MCM2025_Book${suffix}.pdf"

# Generate schedules
/opt/homebrew/bin/pdftk MCM2025_book${suffix}.pdf cat 25-26 output MCM2025_schedule1sheet${suffix}.pdf
/opt/homebrew/bin/pdftk MCM2025_book${suffix}.pdf cat 24-27 28-36east output MCM2025_schedule${suffix}.pdf
/opt/homebrew/bin/pdftk MCM2025_book${suffix}.pdf cat 24-27 28-36east 37-227 output MCM2025_schedule_abstracts${suffix}.pdf

# Rotate pages 12-20 clockwise 90 degrees
/opt/homebrew/bin/pdftk "MCM2025_Book${suffix}.pdf" cat 1-27 28-36east 37-end output "MCM2025_Book${suffix}_rotated.pdf"
mv "MCM2025_Book${suffix}_rotated.pdf" "MCM2025_Book${suffix}.pdf"

# Open PDFs
open MCM2025_Book${suffix}.pdf
#open MCM2025_schedule1sheet${suffix}.pdf
#open MCM2025_schedule${suffix}.pdf
#open MCM2025_schedule_abstracts${suffix}.pdf

cd ..
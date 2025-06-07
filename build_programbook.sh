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

timestamp=$(date +%Y_%m_%d_%H_%M_%S)
echo "Current timestamp: $timestamp"

cp preprocess/out/sess*.tex MCM_ProgramBook_TEX || exit 1
cd MCM_ProgramBook_TEX || exit 1

# Compile LaTeX
pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 || tail -n 100 MCM2025_book.log
pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1

# Rename with timestamp
cp MCM2025_book.pdf "MCM2025_Book_${timestamp}.pdf"

# Generate schedules
/opt/homebrew/bin/pdftk MCM2025_book_${timestamp}.pdf cat 10-11 output MCM2025_schedule1sheet_${timestamp}.pdf
/opt/homebrew/bin/pdftk MCM2025_book_${timestamp}.pdf cat 10-11 12-20east output MCM2025_schedule_${timestamp}.pdf
/opt/homebrew/bin/pdftk MCM2025_book_${timestamp}.pdf cat 10-183 output MCM2025_schedule_abstracts_${timestamp}.pdf

# Open PDFs
open "MCM2025_Book_${timestamp}.pdf"
open MCM2025_schedule1sheet_${timestamp}.pdf
open MCM2025_schedule_${timestamp}.pdf
open MCM2025_schedule_abstracts_${timestamp}.pdf

cd ..
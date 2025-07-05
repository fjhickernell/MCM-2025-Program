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
echo "Running first LaTeX pass..."
if ! PATH="$TEXBIN:$PATH" pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1; then
    echo "LaTeX compilation failed. Last 100 lines of log:"
    tail -n 100 MCM2025_book.log
    exit 1
fi

echo "Running second LaTeX pass..."
if ! PATH="$TEXBIN:$PATH" pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1; then
    echo "Second LaTeX pass failed. Last 100 lines of log:"
    tail -n 100 MCM2025_book.log
    exit 1
fi

# Check if PDF was created and rename with suffix
if [ -f "MCM2025_book.pdf" ]; then
    mv MCM2025_book.pdf "MCM2025_Book${suffix}.pdf"
    echo "Successfully created MCM2025_Book${suffix}.pdf"
else
    echo "Error: MCM2025_book.pdf was not created"
    exit 1
fi

# Generate schedules
echo "Generating schedule PDFs..."
if ! /opt/homebrew/bin/pdftk "MCM2025_Book${suffix}.pdf" cat 25-26 output "MCM2025_schedule1sheet${suffix}.pdf"; then
    echo "Failed to generate schedule1sheet PDF"
    exit 1
fi

if ! /opt/homebrew/bin/pdftk "MCM2025_Book${suffix}.pdf" cat 24-26 27-35east output "MCM2025_schedule${suffix}.pdf"; then
    echo "Failed to generate schedule PDF"
    exit 1
fi

if ! /opt/homebrew/bin/pdftk "MCM2025_Book${suffix}.pdf" cat 24-26 27-35east 36-227 output "MCM2025_schedule_abstracts${suffix}.pdf"; then
    echo "Failed to generate schedule_abstracts PDF"
    exit 1
fi

# Rotate pages 27-35 clockwise 90 degrees (east)
echo "Rotating schedule pages..."
if ! /opt/homebrew/bin/pdftk "MCM2025_Book${suffix}.pdf" cat 1-26 27-35east 36-end output "MCM2025_Book${suffix}_rotated.pdf"; then
    echo "Failed to rotate pages"
    exit 1
fi

if [ -f "MCM2025_Book${suffix}_rotated.pdf" ]; then
    mv "MCM2025_Book${suffix}_rotated.pdf" "MCM2025_Book${suffix}.pdf"
    echo "Successfully rotated schedule pages"
else
    echo "Error: Rotated PDF was not created"
    exit 1
fi

# Open PDFs
open MCM2025_Book${suffix}.pdf
#open MCM2025_schedule1sheet${suffix}.pdf
#open MCM2025_schedule${suffix}.pdf
#open MCM2025_schedule_abstracts${suffix}.pdf

cd ..
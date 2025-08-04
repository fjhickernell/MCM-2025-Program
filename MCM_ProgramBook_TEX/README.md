# MCM 2025 Program Book - LaTeX Sources

This directory contains the LaTeX source files for generating the MCM 2025 conference program book.

## Main Files

- `MCM2025_book.tex`: Main LaTeX file (created from MCQMC2024_book_final.tex)
- Generated PDF output will be placed in this directory

## Building the Program Book

From the root directory, use:

- `make pgm`: Generate the program book PDF with timestamp in filename


## Requirements

- LaTeX distribution (TeX Live or MiKTeX)
- Preprocessed data files (run `make pp` first if needed)

## Reference

A good reference is the [MCQMC2022 program book](https://www.ricam.oeaw.ac.at/events/conferences/mcqmc2022/schedule/MCQMC2022_book_final_version.pdf).
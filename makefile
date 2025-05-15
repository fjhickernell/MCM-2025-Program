# filepath: ./makefile

.PHONY: cleanpdf cleanpy tex pgm

cleanpdf:
	@echo "Cleaning up pdflatex outputs..."
	rm -f MCM_ProgramBook_TEX/*.aux
	rm -f MCM_ProgramBook_TEX/*.bbl
	rm -f MCM_ProgramBook_TEX/*.blg
	rm -f MCM_ProgramBook_TEX/*.log
	rm -f MCM_ProgramBook_TEX/*.pdf

cleanpy:
	@echo "Cleaning up Python outputs..."
	rm -f README_and_Scripts/*.pyc
	rm -f README_and_Scripts/__pycache__/*.pyc

tex: cleantex
	@echo "Compiling Python files in README_and_Scripts directory..."
	python -m compileall README_and_Scripts/*.py

pgm: cleanpdf
	@echo "Compiling LaTeX files in MCM_ProgramBook_TEX directory..."
	@cd MCM_ProgramBook_TEX && pdflatex MCM2025_book.tex && pdflatex MCM2025_book.tex && open MCM2025_Book.pdf && cd ..
# filepath: ./makefile

.PHONY: cleanpdf cleanpy tex pgm

cleanpdf:
	@echo "Cleaning up pdflatex outputs..."
	rm -f MCM_ProgramBook_TEX/*.aux
	rm -f MCM_ProgramBook_TEX/*.bbl
	rm -f MCM_ProgramBook_TEX/*.blg
	rm -f MCM_ProgramBook_TEX/*.log
	rm -f MCM_ProgramBook_TEX/*.pdf
	rm -f MCM_ProgramBook_TEX/input/*

cleanpy:
	@echo "Cleaning up Python outputs..."
	rm -f README_and_Scripts/*.pyc
	rm -f README_and_Scripts/__pycache__/*.pyc
	rm -f README_and_Scripts/sess*.tex
	rm -f README_and_Scripts/listabstract.tex
	rm -f README_and_Scripts/Schedule.tex
	rm -f README_and_Scripts/TableSchedule.html
	rm -f README_and_Scripts/Participants.tex
	rm -f README_and_Scripts/out/*


tex: cleanpy
	@echo "Compiling Python files in README_and_Scripts directory..."
	python README_and_Scripts/MCMBookSessionDesc.py
	python README_and_Scripts/MakeLatexScheduleMCM.py
	python README_and_Scripts/BuildHtmlScheduleMCM.py
	python README_and_Scripts/MakeListPart.py

pgm: cleanpdf
	@echo "Compiling LaTeX files in MCM_ProgramBook_TEX directory..."
	@cp README_and_Scripts/out/* MCM_ProgramBook_TEX/input/
	@cd MCM_ProgramBook_TEX && \
		pdflatex MCM2025_book.tex && \
		pdflatex MCM2025_book.tex && \
		open MCM2025_Book.pdf && \
		cd ..
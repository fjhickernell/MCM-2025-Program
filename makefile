# filepath: ./makefile

.PHONY: cleanpdf cleanpy clean_pp tex pgm pp

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
	rm -f README_and_Scripts/sess*.tex
	rm -f README_and_Scripts/listabstract.tex
	rm -f README_and_Scripts/Schedule.tex
	rm -f README_and_Scripts/TableSchedule.html
	rm -f README_and_Scripts/Participants.tex
	rm -f README_and_Scripts/out/*

clean_pp:
	@echo "Cleaning up preprocess directories..."
	rm -f preproces/out/Schedule.tex

pp: clean_pp
	@echo "Compiling Python files in preprocess directory..."
	python preprocess/schedule_1sheet.py

tex: cleanpy
	@echo "Compiling Python files in README_and_Scripts directory..."
	python README_and_Scripts/MCMBookSessionDesc.py
	python README_and_Scripts/MakeLatexScheduleMCM.py
	python README_and_Scripts/BuildHtmlScheduleMCM.py
	python README_and_Scripts/MakeListPart.py

pgm: cleanpdf
	@echo "Compiling LaTeX files in MCM_ProgramBook_TEX directory..."
	@cd MCM_ProgramBook_TEX && \
		pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 || tail -n 100 MCM2025_book.log && \
		pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 && \
		open MCM2025_Book.pdf && \
		cd ..
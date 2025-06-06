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
	@echo "\n*** Cleaning up preprocess directories..."
	rm -f preprocess/interim/*
	rm -f preproces/out/*
	rm -f preprocess/input/abstracts/*.gz 
	rm -f preprocess/input/abstracts/*.pdf
	rm -f preprocess/input/abstracts/*.log
	rm -f preprocess/input/abstracts/*.aux
	rm -f preprocess/input/abstracts/*.fls
	rm -f preprocess/input/abstracts/*.fdb*
	

pp: clean_pp
	@echo "\n*** Compiling Python files in preprocess directory..."
	@echo "\n--- Running preprocess/download_sheets.py" && python preprocess/download_sheets.py && \
	echo "\n--- Running preprocess/schedule_1sheet.py" && python preprocess/schedule_1sheet.py && \
	echo "\n--- Running preprocess/session_list.py" && python preprocess/session_list.py && \
	echo "\n--- Running preprocess/participants.py" && python preprocess/participants.py && \
	echo "\n--- Running preprocess/download_abstracts.py" && python preprocess/download_abstracts.py && \
	echo "\n--- Running preprocess/gen_talks.py" && python preprocess/gen_talks.py && \
	echo "\n--- Running preprocess/gen_sess.py" && python preprocess/gen_sess.py  && \
	echo "\n--- Running preprocess/schedule.py" && python preprocess/schedule.py 
	@for f in preprocess/input/abstracts/*.tex; do \
		dest="preprocess/input/modfied_abstracts/$$(basename $$f)"; \
		if [ ! -e "$$dest" ]; then \
			cp "$$f" "$$dest"; \
		fi \
	done

tex: cleanpy
	@echo "*** Compiling Python files in README_and_Scripts directory..."
	@echo "\n--- Running MCMBookSessionDesc.py" && python README_and_Scripts/MCMBookSessionDesc.py
	@echo "\n--- Running MakeLatexScheduleMCM.py" && python README_and_Scripts/MakeLatexScheduleMCM.py
	@echo "\n--- Running BuildHtmlScheduleMCM.py" && python README_and_Scripts/BuildHtmlScheduleMCM.py
	@echo "\n--- Running MakeListPart.py" && python README_and_Scripts/MakeListPart.py


pgm: cleanpdf    # brew install pdftk-java, need to manually adjust pages that are taken out
	@echo "*** Compiling LaTeX files in MCM_ProgramBook_TEX directory..."
	@cp preprocess/out/sess*.tex MCM_ProgramBook_TEX && \
	cd MCM_ProgramBook_TEX && \
	pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 || tail -n 100 MCM2025_book.log && \
	pdflatex -interaction=nonstopmode -halt-on-error MCM2025_book.tex > /dev/null 2>&1 && \
	/opt/homebrew/bin/pdftk MCM2025_book.pdf cat 10-11 output MCM2025_schedule1sheet.pdf && \
	/opt/homebrew/bin/pdftk MCM2025_book.pdf cat 10-20 output MCM2025_schedule.pdf && \
	/opt/homebrew/bin/pdftk MCM2025_book.pdf cat 10-186 output MCM2025_schedule_abstracts.pdf &&  \
	open MCM2025_Book.pdf && \
	open MCM2025_schedule1sheet.pdf && \
	open MCM2025_schedule.pdf && \
	open MCM2025_schedule_abstracts.pdf && \
	cd ..

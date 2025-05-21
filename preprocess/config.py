import os

cwd = os.getcwd() + os.sep + "preprocess" + os.sep
indir = f"{cwd}input{os.sep}"
outdir = f"{cwd}out{os.sep}"
interimdir = f"{cwd}interim{os.sep}"

no_plenary_sessions = 8
no_special_sessions = 29
no_technical_sessions = 16
no_sessions = no_plenary_sessions + no_special_sessions + no_technical_sessions

# dictionary describing all Google Sheets and their columns to be selected
gsheets = {
    "schedule": {
        "sheet_id": "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4",
        "sheet_name": "Form Responses 1",
        "columns": None
    },
    "plenary_abstracts": {
        "sheet_id": "1xNO88DO2COTkJ1vOzCXQiTrxKa7_pxW3a2yU06JoDEY",
        "sheet_name": "Form Responses 1",
        "columns": [
            "First or given name(s) of presenter", "Last or family name of presenter",
            "Institution of presenter", #"Email of presenter", 
            "Talk Title"
            #"FirstNameLastNameAbstract.tex file with Talk Title and Abstract"
        ]
    },
    "special_session_submissions": {
        "sheet_id": "1i6OUgAZSI_evTy0E8X5NUB0IzGwLIjwtu_cSnGwl960",
        "sheet_name": "Form Responses 1",
        "columns": [
            "First or given name(s) of first organizer", "Last or family name(s) of first organizer",
            "Institution of first organizer", #"Email of first organizer",
            "First or given name(s) of second organizer", "Last or family name(s) of second organizer",
            "Institution of second organizer",
            "First or given name(s) of third organizer", "Last or family name(s) of third organizer",
            "Institution of third organizer",
            "Presenter 1 first or given name(s)", "Presenter 1 last or family name(s)",
            "Presenter 1 institution", "Presenter 1 email", 
            "Presenter 2 first or given name(s)", "Presenter 2 last or family name(s)",
            "Presenter 2 institution", "Presenter 2 email",
            "Presenter 3 first or given name(s)", "Presenter 3 last or family name(s)",
            "Presenter 3 institution", "Presenter 3 email",
            "Presenter 4 first or given name(s)", "Presenter 4 last or family name(s)",
            "Presenter 4 institution", "Presenter 4 email",
            "Session Title",
            #"FirstNameLastNameSession.tex file with Session Title and Description"
        ]
    },
    "special_session_abstracts": {
        "sheet_id": "10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI",
        "sheet_name": "Form Responses 1",
        "columns": [
            "First or given name(s) of presenter", "Last or family name of presenter",
            "Institution of presenter", #"Email of presenter", 
            "Talk Title",
            #"FirstNameLastNameAbstract.tex file with Talk Title and Abstract", 
            "Special Session Title"
        ]
    },
    "contributed_talk_submissions": {
        "sheet_id": "1o1WeviV-MTGQMFHqsiAkZwMVOO0_h3GNekgCS2fojGM",
        "sheet_name": "Form Responses 1",
        "columns": [
            "First or given name(s) of presenter", "Last or family name of presenter",
            "Institution of presenter", #"Email of presenter", 
            "Talk Title", "SESSION", "Topic",
            #"FirstNameLastNameAbstract.tex file with Talk Title and Abstract", 
            "Acceptance"
        ]
    }
}
 
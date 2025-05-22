import os

cwd = os.getcwd() + os.sep + "preprocess" + os.sep
indir = f"{cwd}input{os.sep}"
outdir = f"{cwd}out{os.sep}"
interimdir = f"{cwd}interim{os.sep}"

no_plenary_sessions = 8
no_special_sessions = 29
no_technical_sessions = 16
no_sessions = no_plenary_sessions + no_special_sessions + no_technical_sessions

min_talks = no_plenary_sessions+ no_special_sessions*3 + no_technical_sessions*3
max_talks = no_plenary_sessions+ no_special_sessions*4 + no_technical_sessions*4
max_organizers = no_special_sessions
max_organizers = no_special_sessions * 3

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
            "Talk Title",
            "FirstNameLastNameAbstract.tex file with Talk Title and Abstract"
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
            "FirstNameLastNameSession.tex file with Session Title and Description"
        ]
    },
    "special_session_abstracts": {
        "sheet_id": "10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI",
        "sheet_name": "Form Responses 1",
        "columns": [
            "First or given name(s) of presenter", "Last or family name of presenter",
            "Institution of presenter", #"Email of presenter", 
            "Talk Title",
            "FirstNameLastNameAbstract.tex file with Talk Title and Abstract", 
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
            "FirstNameLastNameAbstract.tex file with Talk Title and Abstract", 
            "Acceptance"
        ]
    }
}
 
# Map for organizations:
org_dict = {
        "Academy of Mathematics and Systems Science, Chinese Academy of Sciences": "Chinese Academy of Sciences",
        "Work done during C. Huang's Ph.D. studies at Georgia Institute of Technology": "Georgia Institute of Technology",
        "INESC-ID, Rua Alves Redol 9, Lisbon, Portugal 1000-029": "INESC-ID",
        "Department of Mathematical Sciences, Tsinghua University": "Tsinghua University",
        "Illinois Institute of Technology, Department of Applied Mathematics. Sandia National Laboratories.": "Illinois Institute of Technology and Sandia National Laboratories.",
        "Department of Statistics, Columbia University": "Columbia University",
        "Department of Mathematics, Univeristy of Washington": "University of Washington",
        "KAUST: King Abdullah University of Science and Technology (KAUST)": "King Abdullah University of Science and Technology",
        "Istituto Nazionale di Fisica Nucleare (INFN), Laboratori Nazionali del Sud (LNS), Catania, Italy": "Laboratori Nazionali del Sud",
        "Chair of Mathematics for Uncertainty Quantification, Department of Mathematics, RWTH- Aachen University": "RWTH Aachen University",
        "Rwth--Aachen": "RWTH Aachen",
        "Rwth": "RWTH",
        "rwth": "RWTH",
        "Mit": "MIT",
        "Oden Institute for Computational Engineering and Sciences, University of Texas at Austin": "University of Texas at Austin",
        "Ricam, Austrian Academy of Sciences": "Austrian Academy of Sciences",
        "Archimedes/athena Research Centre": "Athena Research Centre",
        "Bcam - Basque Center for Applied Mathematics": "Basque Center for Applied Mathematics",
        "Comsats University Islamabad-Lahore": "COMSATS University Islamabad, Lahore",
        "Ensae Paris": "ENSAE Paris",
        "Institute of Mathematics, Epfl": "EPFL",
        "Epfl": "EPFL",
        "Eth Zurich": "ETH Zurich",
        "Fu Berlin": "Free University of Berlin",
        "Ibm Research": "IBM Research",
        "Ku Leuven": "KU Leuven",
        "Illinois Tech": "Illinois Institute of Technology",
        "King Abdullah University of Science and Technology (kaust)": "King Abdullah University of Science and Technology",
        "Kaust": "King Abdullah University of Science and Technology",
        "University of Warwick, Uk": "University of Warwick",
        "Uc Berkeley": "University of California, Berkeley",
        "The University of Tokyo": "University of Tokyo",
        "Tu Bergakademie Freiberg": "TU Bergakademie Freiberg",
        ", Shanghai, China": "",
        ", Sweden": "",
        ", Brazil": "",
        "Kth ": "KTH ",
        ", Uk": "",
        "Infn": "INFN",
        "infn": "INFN",
        "Lut University":"LUT University",
        "Courant Institute of Mathematical Sciences, ":"",
        ", Laboratori Nazionali del Sud (lns), Catania, Italy":"",
        ", Kaohsiung, Taiwan":"",
        "Institute of Statistics, ":"",
        "Rptu ": "RPTU ",
        ", Institut de Mathématiques de Bordeaux":"",
        "University of Maryland Baltimore County":"University of Maryland, Baltimore",
        "MIT":"Massachusetts Institute of Technology",
        "Mgimo Tashkent Branch":"MGIMO, Tashkent",
        " - Section of Catania": " Catania",
        "Inesc-Id, Rua Alves Redol 9, Lisbon, Portugal 1000-029":"INESC-ID"
    }
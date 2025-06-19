#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from config import *
from util import clean_tex_content

if __name__ == '__main__':

    #vector giving the nb of parallel sessions in each slot
    #a slot is a spot in the schedule where we have parallel sessions
    #we have 9 slots in the schedule, so this vector would have 9 components
    NbParallel = [4,4,4,4,4,4,4,4,4]
    #order of the plenary talks: need to have for each a file Plxx.tex
    PrintPlenary = True #set to true when ready with files
    PlSched = ["Kr","Fo","Ow","Ol","Oa","Ku","Go","La","30"]
    rows = []
    SessionNumber = 0
    SlotNumber = 0
    #counter for the nb of sessions in a slot
    WhichSess = 0
    NewSlot = True
    #keeps track of how many talks have been listed so far in the schedule
    NbTalkListed = 0
    StartListTalk = False
    
    # Initialize latex_content instead of opening file
    latex_content = ""
  #  print("\\begin{sideways}\n\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",file=fsched)
    
    #we assume SessionList contains the list of sessions in order of time, with sessions happening at the same
    #time ordered by "room number", e.g., columns in the schedule
    ##################IMPORTANT
    latex_content += "\\chapter{List of Participants}\n"
    latex_content += "\\setlength{\\columnsep}{1cm}\n"
    latex_content += "\\begin{multicols}{2}\n"
    latex_content += "\\small\\raggedright\n"
    
    # Read all participants and group by name
    from collections import defaultdict
    participants = defaultdict(list)
    with open(f"{outdir}Participants.csv", 'r') as file:
        reader = csv.reader(file, delimiter=',')
        for val in reader:
            key = (val[0].strip(), val[1].strip(), val[4].strip())  # (FirstName, LastName, Organization)
            participants[key].append(val)

    for (first, last, org), vals in participants.items():
        # Collect all session IDs for this participant
        session_ids = [v[2] for v in vals if v[2]]
        # Use the first session as the main one, up to 6 more as extra braces
        main_session = session_ids[0] if session_ids else ''
        extra_sessions = session_ids[1:5] if len(session_ids) > 1 else []
        extra_sessions += [''] * (6 - len(extra_sessions))
        org_str = "Unknown org" if not org else org
        partstrng = f"\\participantne{{{first} {last}}}\n{{{org_str}}}\n"
        partstrng += f"{{{main_session}}}"
        for s in extra_sessions:
            partstrng += f"\n{{{s}}}"
        latex_content += partstrng + "\n"

    latex_content += "\\end{multicols}\n"
    latex_content= clean_tex_content(latex_content)  # Apply common text fixes
    
    # Write all LaTeX content to file once
    with open(f"{outdir}Participants.tex", 'w') as fpart:
        fpart.write(latex_content)
    
    print(f"Output: {outdir}Participants.tex")
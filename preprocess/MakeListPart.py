#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from config import *

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
    
    fpart = open(f"{outdir}Participants.tex",'w')
  #  print("\\begin{sideways}\n\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",file=fsched)
    
    #we assume SessionList contains the list of sessions in order of time, with sessions happening at the same
    #time ordered by "room number", e.g., columns in the schedule
    ##################IMPORTANT
    print("\\chapter{List of Participants}\n",file=fpart)
    print("\\setlength{\columnsep}{1cm}\n",file=fpart)
    print("\\begin{multicols}{2}\n",file=fpart)
    print("\\small\\raggedright\n",file=fpart)
    #with open(f"{indir}PARTICIPANTSJULY5.csv", 'r') as file:
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
        print(partstrng, file=fpart)

    print("\\end{multicols}\n", file=fpart)
    fpart.close()
    print(f"Output: {outdir}Participants.tex")
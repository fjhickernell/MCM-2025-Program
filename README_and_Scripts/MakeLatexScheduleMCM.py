#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import csv
from config import *

if __name__ == '__main__':

    #vector giving the nb of parallel sessions in each slot
    #a slot is a spot in the schedule where we have parallel sessions
    #we have 9 slots in the schedule, so this vector would have 9 components
    ##INPUT NEEDED HERE
    NbParallel = [4,4,4,4,4,4,4,4,4]
    #order of the plenary talks: need to have for each a file Plxx.tex
    PrintPlenary = True #set to true when ready with files
    ##INPUT NEEDED HERE
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
    
    fsched = open(f"{outdir}Schedule.tex",'w')
    #  print("\\begin{sideways}\n\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",file=fsched)
    #we assume SessionList contains the list of sessions in order of time, with sessions happening at the same
    #time ordered by "room number", e.g., columns in the schedule
    ##################IMOPORTANT
    #open MCQMC2024Data on the sheet ChronTalkList.csv
    with open(f"{indir}SessionListMCM.csv", 'r') as file:
        reader= csv.reader(file, delimiter=',')
        NbSession = NbParallel[SlotNumber]
        
        #loop reads line by line, where val represents current line
        #each line represents a session
        for val in reader:
            #if we are at the beginning of a slot we need to write something different
            if(NewSlot):
                if(NbTalkListed>0):
                    print("\\\\\\hline\n",file=fsched)
                    if(SlotNumber%2==1 and SlotNumber<9):
                        print("\\TableEvent{12:30 -- 14:00}{Lunch}\\\\\n",file=fsched)
                    if(SlotNumber==2):   
                        print("\\TableEvent{18:00 -- 19:30}{Reception}\\\\\n",file=fsched)
                    if(SlotNumber==6):     
                        print("\\TableEvent{17:30 -- 17:45}{Conference Photo}\\\\\n",file=fsched) 
                        print("\\TableEvent{18:30 -- 21:00}{Banquet (Engineering 7 (E7) Building); Doors open at 18:00}\\\\\n",file=fsched)
                    print("\\end{tabularx}\n",file=fsched)
                    print("\\end{sideways}\n",file=fsched)
                
                    #if PrintPlenary:
                    #    print(
                myplen="\\input{PL"+PlSched[SlotNumber]+".tex}"   
                if(SlotNumber%2==0):
                    print("\\hspace*{-1.2cm}",file=fsched)
                print("\\begin{sideways}\\small\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",file=fsched)
                print("\\TableHeading{",val[7],"}",file=fsched)
                print("\\\\\\hline\n",myplen,file=fsched)
                if(SlotNumber%2==0):
                    print("\\TableEvent{10:00 -- 10:30}{Coffee break -- STC lower level atrium}\\\\",file=fsched)
                else:
                    print("\\TableEvent{15:00 -- 15:30}{Coffee break -- STC lower level atrium}\\\\",file=fsched)
                print("\\rowcolor{\\SessionTitleColor}\\cellcolor{\EmptyColor}",file=fsched)

            #val[2] is 1 if special session and 0 otherwise
            #val[7] is the room

            if(val[2]=='1'):
                print("&\\tableSpecialCL{",val[8],"}",file=fsched) #location
            else:
                print("&\\tableContributedCL{",val[8],"}",file=fsched)

            print("{",val[1],"}",file=fsched) #title
            if(val[2]=='1'):
                sessidstrng="{"+val[0]+"}"
                print(sessidstrng,file=fsched) #sessionid
            print("{",val[6],"}",file=fsched) #chair
            
            WhichSess += 1
            #checks to see if we are done with a timeslot; we need to put all the session info on the top part
            if(WhichSess == NbSession):
                WhichSess=0
                NewSlot = True
                SlotNumber+=1
                StartListTalk = True                
            else:
                NewSlot = False    
            if StartListTalk: # ready to start putting the talks below the session desc    
                startbuildslot = False
                donebuildslot = False
                NbTalkSlot = 0
                #assumes the rows of the talks spreadsheet are listed in chronological order of the conference
                # ——— read Excel ———
                excel_file = f"{indir}MCM2025Data.xlsx"
                sheet_name = "TalkListAsValue"                 
                if not os.path.exists(excel_file):
                    raise FileNotFoundError(f"Couldn't find {excel_file}")
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                talkdata = df.values.tolist()
                rownumber = 0
                #indicates the subslot within a slot, e.g., 11-11:30am in morning slot
                subslot = 0
                #indicates the column in the schedule: needed for subslot 3 in case less than 4 talks
                colnb=0
                #needs to find the talks for this session
                for row in talkdata:                        
                    if rownumber==NbTalkListed and not startbuildslot and not donebuildslot:
                        startbuildslot = True
                    if startbuildslot:  
                        #row[5] is the rank in the session
                        if row[5]=='1' and subslot>1:
                            #we're back on a subslot 1 so this means we are done with slot
                            startbuildslot = False
                            donebuildslot = True
                            StartListTalk = False
                            NbTalkListed = NbTalkListed + NbTalkSlot
                        else:    
                            #we are at the beginning of a subslot so need to print subslot info
                            if row[5]!=str(subslot):
                                if (subslot % 2 == 0):
                                    #alternate color between subslots
                                    print("\\\\\\hline\n",file=fsched) 
                                    print("\\rowcolor{\\SessionLightColor}",file=fsched)
                                    #gets the correct time depending on subslot and slotnumber(am/pm)
                                    if(SlotNumber % 2 ==1):
                                        if(subslot == 0):
                                            print("\\tableTime{10:30}{11:00}",file=fsched)
                                        
                                        if(subslot == 2):
                                            print("\\tableTime{11:30}{12:00}",file=fsched) 
                                        
                                    else:
                                        if(subslot == 0):
                                            print("\\tableTime{15:30}{16:00}",file=fsched)
                                        if(subslot == 2):
                                            print("\\tableTime{16:30}{17:00}",file=fsched) 
                                else:
                                    print("\\\\\\hline\n",file=fsched) 
                                    print("\\rowcolor{\\SessionDarkColor}",file=fsched)
                                    if(SlotNumber % 2 ==1):
                                        
                                        if(subslot == 1):
                                            print("\\tableTime{11:00}{11:30}",file=fsched) 
                                        
                                        if(subslot == 3):
                                            print("\\tableTime{12:00}{12:30}",file=fsched) 
                                    else:
                                        if(subslot == 1):
                                            print("\\tableTime{16:00}{16:30}",file=fsched)
                                        if(subslot == 3):
                                            print("\\tableTime{17:00}{17:30}",file=fsched) 
                                            
                                subslot +=1
                                
                                colnb=0
                            #if we are in startbuildslot mode we print the talk info 
                            #but first need to check for empty column in last subslot
                            gap = ((int(row[7])-1) % 4)-colnb
                
                            if gap>0:
                                for j in range(0,gap):
                                    print("&",file=fsched)
                                    #print(rownumber,gap,colnb,int(row[7]))
                                colnb=colnb+gap  
                            colnb=colnb+1    
                            print("&\\tableTalk{",row[0]," ", row[1],"}",file=fsched) #speaker                    
                            print("{",row[2]," ","}",file=fsched) #title
                            #same talk id as in the other program
                            talkidstrng="{"+row[3]+'-'+str(row[5])+"}"
                            print(talkidstrng,file=fsched) #talkid                                 
                            #keeps track of hoy many talks there are in the slots so we can
                            #find the correct row number when we build the next slot
                            NbTalkSlot += 1
                    rownumber+=1             
                    
    print("\\\\\\hline\n",file=fsched) 
    print("\\end{tabularx}\n",file=fsched)
    print("\\end{sideways}\n",file=fsched)            
   
    fsched.close()
    print(f"Output: {outdir}Schedule.tex")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""



import numpy as np
import pandas as pd
import os
import csv


##IMPORTANT NOTE
##NEED TO MANUALLY REMOVE SPACE BY OPENING HTML IN PYTHON 


#<p>10h-12h: Parallel sessions</p>
#<ul>
#<li><a href="#8.1a">Numerical approximation of SDEs under non-standard assumptions (1)</a></li>
#<li><a href="#8.2a">Non-Reversible Markov Chain Monte Carlo (1)</a></li>
#<li><a href="#8.3a">Construction of QMC point sets and sequences</a></li>
#<li><a href="#C4.1">Nuclear applications</a></li>
#<li><a href="#12.2a">Forward and inverse UQ with hierarchical models (1)</a></li>
#</ul>


if __name__ == '__main__':
    cwd = os.getcwd() + "/README_and_Scripts/"
    
    #vector giving the nb of parallel sessions in each slot
    #a slot is a spot in the schedule where we have parallel sessions
    #we have 9 slots in the schedule, so this vector would have 9 components
    ##INPUT NEEDED HERE
    NbParallel = [4,4,4,4,4,4,4,4,4]
    WhichDay = ["Monday","Monday","Tuesday","Tuesday","Wednesday","Wednesday","Thursday","Thursday","Friday"]
    PlenSpkr = ["David Krieg:","Gersende Fort:","Art Owen:","Mariana Olvera-Cravioto:","Chris Oates:","Frances Kuo:","Takashi Goda:","Henry Lam:","30 Years of MCQMC"]
    #initialization
    rows = []
    SessionNumber = 0
    SlotNumber = 1
    #counter for the nb of sessions in a slot
    WhichSess = 0
    NewSlot = True
    #keeps track of how many talks have been listed so far in the schedule
    NbTalkListed = 0
    StartListTalk = False
    
    with open(f'{cwd}PlenTitle.csv', 'r') as f:
        reader = csv.reader(f)
        dataTitle = list(reader)
        
    f.close()    
        
    Title_array = np.array(dataTitle, dtype=str)    
    
    fsched = open("TableSchedule.html",'w')
    #print("\\begin{sideways}\n\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",file=fsched)
    print("<h2> Sunday August 18</h2>",file=fsched)
    print("<p>14:15-15:45: Tutorial: Fred Hickernell:",Title_array[0,1],"</p>",file=fsched)
    print("<p>16:00-17:30: Tutorial: Peter Frazier:",Title_array[1,1],"</p>",file=fsched)
    
    #we assume SessionList contains the list of sessions in order of time, with sessions happening at the same
    #time ordered by "room number", e.g., columns in the schedule
    with open(f"{cwd}SessionListMCQMC.csv", 'r') as file:
        reader= csv.reader(file, delimiter=',')
        NbSession = NbParallel[SlotNumber]
        
        #loop reads csv file line by line, where val represents current line
        #each line represents a session
        for val in reader:
            #if we are at the beginning of a slot we need to write something different
            if(NewSlot):
                if(SlotNumber % 2 == 1):
                    print("<h2>",WhichDay[SlotNumber-1],"August ",18+int((SlotNumber+1)/2),"</h2>",file=fsched)
                    if(SlotNumber<9):
                        print("<p>9:00-10:00: Plenary Talk:",PlenSpkr[SlotNumber-1],Title_array[SlotNumber+1,1],"</p>",file=fsched)
                    else:
                        print("<p>9:00-10:00: Panel Discussion:",PlenSpkr[SlotNumber-1],"</p>",file=fsched)
                    print("<p>",WhichDay[SlotNumber-1],"10h30-12h30: Parallel Sessions</p>", file=fsched)
                else:
                    print("<p>14:00-15:00: Plenary Talk:",PlenSpkr[SlotNumber-1],Title_array[SlotNumber+1,1],"</p>",file=fsched)
                    print("<p>",WhichDay[SlotNumber-1],"15h30-17h30: Parallel Sessions</p>", file=fsched)
                print("<ul>",file=fsched)        

            #val[2] is 1 if special session and 0 otherwise
            #val[7] is the room
            
            if(val[2]=='1'):
                mystr='<li><a href="#'+val[0]+'">Special Session:'
                print(mystr, val[1],"</a></li>", file=fsched)                
            else:
                mystr='<li><a href="#'+val[0]+'">'
                print(mystr, val[1],"</a></li>", file=fsched)

   
            
            WhichSess += 1
            #checks to see if we are done with a timeslot; we need to put all the session info on the top part
            if(WhichSess == NbSession):
                WhichSess=0
                NewSlot = True
                SlotNumber+=1
                StartListTalk = True
                print("</ul>",file=fsched)
            else:
                NewSlot = False  
    
    print("</li>",file=fsched)
    print("</ul>",file=fsched)
    print("</li>",file=fsched)
    print("</ul>",file=fsched)
    print("<p>&nbsp;</p>",file=fsched)
                
 #   fsched.close()          

 #   fsched = open("SessionDesc.html",'w')    
   
    print("<p>&nbsp;</p>", file=fsched)
    print("<h1>Sessions Description:</h1>", file=fsched)
                

    #assumes the rows of the talks spreadsheet are listed by session
    #doesn't really matter in what order since this will be tagged from the schedule
    #####################IMPORTANT
    # ——— read Excel sheet ———
    excel_file = f"{cwd}MCQMC2024Data.xlsx"        
    sheet_name = "TalkListAsValue"                 
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Couldn't find {excel_file}")
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    talkdata = df.values.tolist()
    rownumber = 0
    currsess=""
    #needs to find the talks for this session
    for row in talkdata:               
        sess = row[3]
        if sess!=currsess or currsess=="":
            #must finish the list of talks in a session
            if currsess!="":
                print('</ul>',file=fsched)
                print('</li>',file=fsched)
                print('</ul>',file=fsched)
                print('</li>',file=fsched)
                print('</ul>',file=fsched)
            currsess = sess
            #next few lines are what we put at the beginning of a session description
            mystr='<h4><a name="'+currsess+'"></a>'
            print(mystr, row[8],"</h4>",file=fsched)
            print("<ul>",file=fsched)
            print('<li style="list-style-type: none;">',file=fsched)
            print('<ul>',file=fsched)
            print('<li style="list-style-type: none;">',file=fsched)
            print("<ul>",file=fsched)
        
        #and now we are just printing the info for each talk             
        print("<li>",row[0],row[1]+":",row[2],"</li>",file=fsched)
    print("</ul>",file=fsched)
    print("</li>",file=fsched)
    print("</ul>",file=fsched)
                   
                    
    fsched.close()           
   
   
           
        
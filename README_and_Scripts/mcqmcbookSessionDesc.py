#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""



import numpy as np
import pandas as pd
import csv
import os.path
import os



if __name__ == '__main__':
    cwd = os.getcwd() + "/README_and_Scripts/"

    rows = []
    talknumber = 0
    
    #for this program we assume MCQMC2024Data.csv is open on TalkList sheet
    #which is sorted by session order (column H) and then by speaker in session (column F)
    #############IMPORTANT
    #open MCQMC2024Data.csv on TalkListAsValue sheet
    #with open("MCQMC2024Data.csv", 'r') as file:
        #reader= csv.reader(file, delimiter=',')
    # ——— read Excel instead of CSV ———
    excel_file = f"{cwd}MCQMC2024Data.xlsx"        # your workbook
    sheet_name = "TalkListAsValue"                 # the exact sheet/tab name
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Couldn't find {excel_file}")
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    rows = df.values.tolist()
    foundbegintalk = 0
    #loop reads csv file line by line, where val represents current line
    #each line represents a talk
    #for val in reader:
    for val in rows:
        #this first part will create one latex file per session with the info
        #needed to describe the session
        #it also assigns a talk id to each talk
        #column 0 first name; column 1 last name; column 2 title of the talk
        #column 3 label of the session (e.g., SS1 or CS4); column 4 path with abstract file
        #column 5 order of the talk within its session; column 6 1 if SS and 0 otherwise
        talknumber += 1
        talkid=""
        #reads the talk info and first finds the correct session description latex file
        myfilename="sess"+val[3]+".tex"
        # if it's the first reader, open in write mode
        if(val[5]=='1'):
            f = open(myfilename,'w')
            print("\\sessionPart{}% [1] part",file=f)
            sessString = "{"+"\\hfill"+"\\timeslot{"+val[11]+"}"
            #print("{","\\hfill","\\timeslot{",val[11],"}",file=f)
            print(sessString,file=f)
            if "orning" in val[11]:
                print("{10:30}{12:30}",file=f)
            else:
                print("{15:30}{17:30}",file=f)
            print("{",val[12],"}}",file=f)    

        else:
            f = open(myfilename,'a')
        #write the title and name of speaker    
        print("\sessionTalk{",val[2],"}",file=f)
        spkstring="{"+val[0]+" "+val[1]+"}"
        print(spkstring,file=f)
        #assigns a talk id given by session label and rank of talk
        talkid=val[3]+'-'+str(val[5])
        #then writes in the talk id
        talkidstrng="{"+talkid+"}"
        print(talkidstrng,file=f)
        f.close()
        
        if(talknumber>1):
            fpart = open("SpeakerList.txt",'a')
        else:
            fpart = open("SpeakerList.txt",'w')
        print(val[0]+ " " + val[1],talkid,file=fpart)   
        fpart.close()
                
        #This part will open the latex abstract file, add the required lines (session id, talk id etc)
        #then it outputs the part between \begin{talk} and \end{talk} (including the new info)
        #into a file called listabstract.tex
        #This part should be run with the talks listed in whatever order we want them in the list of
        #abstracts
    
        res = ""
        ###first we need to grab the filename and path
        ###assume column 10 has the folder number for the abstract
        oldfile = val[4]
        justlatex = oldfile[oldfile.rindex('/')+1:]
        newfile = cwd+'TalksDir/submission-'+str(val[9])+'/'+justlatex
        #and then we would do -  
        with open(os.path.abspath(newfile),"r") as ft:
        ###with open(val[4], "r") as ft:
        ### THIS WORKS
        ###with open(os.path.abspath('./TalksDir/submission-1/template_abstract_talk.tex'),"r") as ft:   
        #with open("JunLuo.tex", "r") as ft:   
            data = ft.readlines() # Read the file line by line

        ft.close()
        #boolean to indcate the spot where we need to add the session id and talk id
        #because we found the six fields (and replaced the 6th one)
        found = False
        #boolean to indicate we are within the talk environment
        InTalkEnv = False
        
        CountFields=0   
        
        for line in data:
            if "\\begin{talk}" in line:
                InTalkEnv = True
                #i think this is useless so shd probably remove
                foundbegintalk = foundbegintalk +  1
            #may8 if InTalkEnv and not "field empty" in line:  
            if InTalkEnv and "}" in line and not found:     
                CountFields += 1
            if InTalkEnv and (CountFields< 7 or found ):    
                    res += line # Insert the line we just read    
            #may8 if "field empty" in line:
            if CountFields == 7 and not found:    
                if val[6]=='1':
                    res += "{"+val[8]+"}\n"
                else:
                    res += "{}"
                res += "{"+"\\timeslot{"+val[11]+"}"
                if "orning" in val[11] and val[5]=='1':
                    res+="{10:30}{11:00}"
                if "orning" in val[11] and val[5]=='2':
                    res+="{11:00}{11:30}"  
                if "orning" in val[11] and val[5]=='3':
                    res+="{11:30}{12:00}"      
                if "orning" in val[11] and val[5]=='4':
                    res+="{12:00}{12:30}"    
                if "ernoon" in val[11] and val[5]=='1':
                    res+="{15:30}{16:00}"
                if "ernoon" in val[11] and val[5]=='2':
                    res+="{16:00}{16:30}"  
                if "ernoon" in val[11] and val[5]=='3':
                    res+="{16:30}{17:00}"      
                if "ernoon" in val[11] and val[5]=='4':
                    res+="{17:00}{17:30}"        
                res+= "{"+val[12]+"}}"  
            #may8 if "you were invited to give a talk in a special session" in line and not found:
                res += "{"+talkid+"}" # Insert talkid                    
                res += "{"+val[3]+"}\n\n"

                #means we found the 6th entry and replaced it
                found = True
            #foundbegintalk = foundbegintalk +  1
            if "\\end{talk}" in line:
                #res += line
                InTalkEnv = False
            #print(res)        

#              with open(val[4], "w") as ft:
#              ft.write(res) # Write the answer in the same file
        #appends if not the first talk, write if first talk
        if(talknumber>1):            
            fa = open("listabstract.tex",'a')
        else:
            fa = open("listabstract.tex",'w')
        print(res,file=fa)
        fa.close()

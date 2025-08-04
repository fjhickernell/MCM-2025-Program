# Resolved Issues

## File Permissions 
* Permissions for the above files have been changed to _Anyone with the link can view_ for reading purposes.
* SC has problems accessing some tex files, e.g., [Toni Karvonen.tex](https://drive.google.com/file/d/1Jg6RZ_j6psSOBVT5bbJ_cX-ye_6cM2ar/view) and [this](https://drive.google.com/file/d/1CKia3hkFZGXL_-eN_rgsoJ9GJSQvbdPT/view?usp=sharing)

## Input Data Issues with Google Sheets 
* [Schedule](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/schedule.csv):
	- The second-to-last row contains "//". SC has programmatically removed such rows.
	- Choi has two sessions, each with two parts. Currently, there is only one part, and the part number "Part I" is missing. Two Part II sessions are added. 
	- Jing Dong's session is added. 
	- Missing time for RECEPTION and BANQUET — DONE.
	- Parallel talks on Friday in the schedule has only 1.5 hours as opposed to 2 hours for 4 talks. May need to move sessions with 4 talks. — DONE.
* [Plenary Talk Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/plenary_abstracts.csv):
* [Special Session Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_submissions.csv):
	- The last row contains only "SCHEDULED (by Nathan Kirk)" — this row is removed programmatically by SC.
	- Added Jing Dong's session to the Google Sheet manually.
	- Jing Dong's session is missing the abstract .tex source, waiting for Chang-Hang — DONE
	- Added two of Sou-Cheng Choi's Part II sessions
	- **NOTE**: S9, S13, S27, S19, S20 has only 3 speakers in each session.
* [Special Session Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_abstracts.csv):
	- Some values are empty in the last column, `Special Session Title`. Zexin's SS title was filled in manually by Fred. SC added the values for Chih-Li,Sung and Mao, Cai. Mao has a duplicate talk.  It is deduplicated programmatically. 
	- Some special sessions have only two speakers who have sent abstracts: —  Fred and Mikhail have sent them reminders. DONE. 
		* Stochastic Optimization 
		* Recent Progress on Algorithmic Discrepancy Theory and Applications
		* Recent Advances in Stochastic Gradient Descent 
    - The special talk abstract of Shyam Mohan Subbiah Pillai has been overwritten by a session proposal. It seems to be a mistake. — DONE.
* [Contributed Talk Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/contributed_talk_submissions.csv):
	- Six talks are not assigned to a Technical Session in column `SESSION` or contain missing or unusual values like `ADD TO SHANE H. SESSION` and  `//` — Fred has asked Mikhail to handle these and also filled in column `Paid`.  DONE.
	- **NOTE**: T1, T8, and T9 has only 3 speakers in each session.
	- SC programmatically filtered out rows with `Acceptance` == `Yes`.

  
## Missing Output Data

- SessionList.csv
	* Session IDs are created programmatically
	* Chair names are missing — fill in column `Chair` in Schedule by Chang-Han or program committee — DONE
	* Room numbers are missing — DONE
- Participants.csv
	* Missing organizing committee members and scientific committee members — DONE
	* Not sure how to get `PageNumber` — DONE.
	* Student helpers — DONE.
	* Paid registered participants who are not presenters/organizers — Fred will extract from Mail Chimp. DONE.

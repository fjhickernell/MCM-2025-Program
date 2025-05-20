# README

## Goal

The following are input Google Sheets for MCM 2025. We need to convert them into the input format required by 
`MCM2025Data.xlsx`:

*   MCM 2025 Schedule: [https://tinyurl.com/4pj6dez7](https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0)
*   Plenary Talk Abstracts: [https://tinyurl.com/2ttw4t4c](https://docs.google.com/spreadsheets/d/1xNO88DO2COTkJ1vOzCXQiTrxKa7_pxW3a2yU06JoDEY/edit?usp=sharing)
*   Special Session Submissions: [https://tinyurl.com/569kcufm](https://docs.google.com/spreadsheets/d/1i6OUgAZSI_evTy0E8X5NUB0IzGwLIjwtu_cSnGwl960/edit?usp=sharing)
	- _First tab, "Form Responses 1"_
	- `Session Title`, column AE
*   Special Session Abstracts: [https://tinyurl.com/n3b6xu48](https://docs.google.com/spreadsheets/d/10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI/edit?usp=sharing)
	- `Special Session Title`, column Z
*   Contributed Talk Submissions: [https://tinyurl.com/383y2kue](https://docs.google.com/spreadsheets/d/1o1WeviV-MTGQMFHqsiAkZwMVOO0_h3GNekgCS2fojGM/edit?gid=429679292#gid=429679292)
	- `SESSION`, column X

## Issues

### File Permissions 
Permissions for the above files have been changed to _Anyone with the link can view_ for reading purposes.

### Input Data Issues with Google Sheets 
* [Schedule](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/schedule.csv):
	- The second-to-last row contains "//". SC has programmatically removed such rows.
	- Choi has two sessions, each with two parts. Currently, there is only one part, and the part number "Part I" is missing. Two Part II sessions are added. 
	- Jing Dong's session is added. 
* [Plenary Talk Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/plenary_abstracts.csv):
	- So far, there are only five plenary talk abstracts. <mark>***Fred needs to remind them***</mark>
* [Special Session Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_submissions.csv):
	- Some rows do not look correct, as they have no first or last names of presenters — <mark>TODO</mark>
	- The last row contains only "SCHEDULED (by Nathan Kirk)" — this row is removed programmatically by SC.
	- Added Jing Dong's session to the Google Sheet manually.
	- Jing Dong's session is missing the abstract URL and email address — <mark>TODO</mark>
	- Added two of Sou-Cheng Choi's Part II sessions
* [Special Session Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_abstracts.csv):
	- Some values are empty in the last column, `Special Session Title`. Zexin's SS title was filled in manually by Fred. SC added the values for Chih-Li,Sung and Mao,Cai. <mark>— TODO Mao has a duplicate talk. Remove it?<mark>
	-  Some special sessions has only one or two speakers — <mark>TODO</mark>
      	* Advances in Adaptive Hamiltonian Monte Carlo has 2 participants
		* Stochastic Optimization has 2 participants
		* Recent Progress on Algorithmic Discrepancy Theory and Applications has 1 participants
		* Monte Carlo Applications in High-performance Computing, Computer Graphics, and Computational Science has 2 participants
		* Nested expectations: models and estimators, Part II has 2 participants
		* Nested expectations: models and estimators, Part I has 2 participants
		* Computational Methods for Low-discrepancy Sampling and Applications has 2 participants
* [Contributed Talk Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/contributed_talk_submissions.csv):
	- Four talks are not assigned to a Technical Session in column `SESSION` or contain unusual values like `ADD TO SHANE H. SESSION` and 
`//` — <mark>Fred will handle these</mark>
	- SC programmatically filtered out rows with `Acceptance` == `Yes`.
  
### Missing Output Data

- SessionList.csv
  * Session IDs are created programmatically
  * Chair names are missing — <mark>TODO</mark>
  * Room numbers are missing — <mark>TODO</mark>
- Participants.csv
  * Missing organizing committee members and scientific committee members — <mark>TODO</mark>
  * Not sure how to get `PageNumber` — <mark>TODO</mark>

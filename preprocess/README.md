# README

## Goal

The following are input Google sheets for MCM 2025. We need to morph them into Excel file formats required by 
`MCM2025Data.xlsx`:

*   MCM 2025 Draft Schedule,[https://tinyurl.com/4pj6dez7](https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0)
*   Plenary Talk Abstracts: [https://tinyurl.com/2ttw4t4c](https://docs.google.com/spreadsheets/d/1xNO88DO2COTkJ1vOzCXQiTrxKa7_pxW3a2yU06JoDEY/edit?usp=sharing)
*   Special Session Submissions: [https://tinyurl.com/569kcufm](https://docs.google.com/spreadsheets/d/1i6OUgAZSI_evTy0E8X5NUB0IzGwLIjwtu_cSnGwl960/edit?usp=sharing)
	- `Session Title`, column AE
*   Special Session Abstracts: [https://tinyurl.com/n3b6xu48](https://docs.google.com/spreadsheets/d/10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI/edit?usp=sharing)
	- `Special Session Title`, column Z
*   Contributed Talk Submissions: [https://tinyurl.com/383y2kue](https://docs.google.com/spreadsheets/d/1o1WeviV-MTGQMFHqsiAkZwMVOO0_h3GNekgCS2fojGM/edit?gid=429679292#gid=429679292)
	- `SESSION`, column X


## Issues

### File permission 
Permission of the above files have been changed to _Anyone with the link can view_ for reading purposes.

### Input data issues
* [Schedule](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/schedule.csv)
	- Second last row contain "//"
*  [Plenary Talk Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/plenary_abstracts.csv):
	- So far there are only 5 plenary talk abstracts
* [Special Session Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_submissions.csv):
	- Last few rows do not look right as they have no first and last names of presenters and contains "SCHEDULED (by Nathan Kirk)"
*  [Special Session Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_abstracts.csv):
   	- Some values are empty in the last column, `Special Session Title`
* [Contributed Talk Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/contributed_talk_submissions.csv)
    - Some talks are not assigned to a Technical Session in column `SESSION`
  
### Missing output data
  
* Need to find session IDs or create them
* Chair names are missing
* Where are the room numbers? 



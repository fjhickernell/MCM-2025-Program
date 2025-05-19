# README

## Goal

The following are input Google Sheets for MCM 2025. We need to convert them into the input format as required by 
`MCM2025Data.xlsx`:

*   MCM 2025 Draft Schedule: [https://tinyurl.com/4pj6dez7](https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0)
*   Plenary Talk Abstracts: [https://tinyurl.com/2ttw4t4c](https://docs.google.com/spreadsheets/d/1xNO88DO2COTkJ1vOzCXQiTrxKa7_pxW3a2yU06JoDEY/edit?usp=sharing)
*   Special Session Submissions:  [https://tinyurl.com/569kcufm](https://docs.google.com/spreadsheets/d/1i6OUgAZSI_evTy0E8X5NUB0IzGwLIjwtu_cSnGwl960/edit?usp=sharing) _First tab, "Form Responses 1"_
	- `Session Title`, column AE
*   Special Session Abstracts: [https://tinyurl.com/n3b6xu48](https://docs.google.com/spreadsheets/d/10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI/edit?usp=sharing)
	- `Special Session Title`, column Z
*   Contributed Talk Submissions: [https://tinyurl.com/383y2kue](https://docs.google.com/spreadsheets/d/1o1WeviV-MTGQMFHqsiAkZwMVOO0_h3GNekgCS2fojGM/edit?gid=429679292#gid=429679292)
	- `SESSION`, column X

## Issues

### File permissions 
Permissions for the above files have been changed to _Anyone with the link can view_ for reading purposes.

### Input data issues with Google Sheets 
* [Schedule](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/schedule.csv):
	- The second-to-last row contains "//". SC has programmatically removed such rows.
* [Plenary Talk Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/plenary_abstracts.csv):
	- So far, there are only five plenary talk abstracts, <mark>***Fred needs to remind them***<mark>
* [Special Session Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_submissions.csv):
	- Some rows do not look correct, as they have no first or last names of presenters --- <mark>TODO<mark>
	- The last row contains only "SCHEDULED (by Nathan Kirk)" --- this row is removed programmatically by SC
	- Add Jing Don's session to Google Sheet manually --- <mark>SC<mark>
	- Add two of Sou-Cheng Choi's Part II sessions  --- <mark>SC<mark>
* [Special Session Abstracts](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/special_session_abstracts.csv):
	- Some values are empty in the last column, `Special Session Title` --- Zexin's title filled in manually by Fred. <mark>SC to work on others.<mark>
* [Contributed Talk Submissions](https://github.com/fjhickernell/MCM-2025-Program/blob/main/preprocess/input/contributed_talk_submissions.csv):
	- 4 talks are not assigned to a Technical Session in column `SESSION` or contains funny values like `ADD TO SHANE H. SESSION` and 
`//` --- <Mark>Fred will handle these</mark>
	- SC filtered out programmatically rows with `Acceptance` == `Yes`
  
### Missing output data
  
* Created session IDs programmatically
* Chair names are missing --- <mark>TODO<mark>
* Where are the room numbers?  --- <mark>TODO<mark>



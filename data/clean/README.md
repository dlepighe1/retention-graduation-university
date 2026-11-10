# Data dictionary

Every file here is built by `notebooks/01_clean.ipynb`. All data is aggregate and public.

## dair_rates.csv
One row per college × entering cohort × metric. Source: UIUC DAIR Retention and Graduation Rates. Population: first-time, full-time, degree-seeking undergraduates (adjusted cohorts).

| Column | Unit | Meaning |
| --- | --- | --- |
| college | text | College at entry as DAIR names it, or "All campus". DAIR's spelling "Explatory" is kept so keys match the source |
| college_short | text | Short label for charts, e.g. Gies, LAS |
| cohort | year | Fall the students entered |
| metric | text | First-year retention, 4-year graduation, 5-year graduation or 6-year graduation |
| cohort_size | students | Adjusted cohort size |
| count | students | Students retained, or graduated by that year |
| rate_pct | % | 100 × count / cohort_size |

- Retention covers cohorts 2021–2025; graduation covers 2016–2020.
- Cumulative graduation counts add DAIR's non-cumulative year groups: 4-year = groups 3 + 4, and so on. Blank groups are zero; the groups reproduce DAIR's own cumulative count for all 51 college × cohort rows.
- "All campus" is the sum of the 11 entering units and includes Gies. Its retention counts match DAIR's campus totals exactly for all five cohorts.
- The School of Information Sciences has no graduation rows before the 2020 cohort, because no such cohort exists.

## dair_enrollment.csv
One row per college × fall × level. Source: UIUC DAIR Student Enrollment, Historical Table.

| Column | Unit | Meaning |
| --- | --- | --- |
| college | text | College, using the first name in DAIR's historical label |
| fall_year | year | Fall term, 2016 onward |
| level | text | Undergraduate, Graduate or Professional |
| headcount | students | Fall headcount |

- DAIR labels the year columns "Calendar Year". They are treated as fall terms because campus totals land within 0.3–0.8% of IPEDS fall enrollment for 2019–2023.
- 81 of 2,926 college × level × year cells were blank and are dropped. Colleges that no longer exist, or that belong to UIC, stay in the file and can be filtered out.

## ipeds_peers.csv
One row per institution × IPEDS year. Source: NCES IPEDS complete data files (HD, EF A, EF D, GR). Set: public universities with Carnegie 2021 Basic = 15, fixed from the 2023 directory.

| Column | Unit | Meaning |
| --- | --- | --- |
| unitid | id | IPEDS institution ID |
| institution | text | Institution name |
| state | text | Two-letter state |
| year | year | IPEDS collection year |
| retention_rate | % | Full-time first-year retention (`RET_PCF`), reported by IPEDS as a whole number |
| grad_rate_6yr | % | Completers within 150% of normal time ÷ adjusted cohort (GR file, GRTYPE 3 / GRTYPE 2) |
| enrollment | students | Grand total fall enrollment (`EFTOTLT`, EF A, EFALEVEL 1) |
| big_ten | text | "Big Ten" or "Other public R1" |
| is_uiuc | text | "UIUC" or "Peer" |

- 16 of the 18 Big Ten schools are flagged. Northwestern and USC are private, so they fall outside this public-only set.
- Institution-years with a blank rate or enrollment are dropped: 7 retention, 7 graduation and 2 enrollment blanks, leaving 105–106 schools per year.
- In year Y, retention follows students who entered in fall Y−1, and graduation follows the cohort that entered about six years earlier.
- 2019–2022 use NCES's revised `_rv` files. 2023 had no revised file at download, so it uses the latest posted file.

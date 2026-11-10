# Gies Retention, Graduation and Enrollment

**Question:** How do Gies retention and graduation compare with all of campus? Across public research universities, how closely is first-year retention associated with six-year graduation?

**Answer:** Gies ranks first of 11 Illinois entering units, with a 92.7% six-year graduation rate against 85.0% for campus, and across 106 public research universities each extra point of first-year retention goes with about 1.7 more points of six-year graduation.

**Dashboard:** [Open the interactive dashboard on Tableau Public](https://public.tableau.com/app/profile/david.lepighe/viz/gies_dashboard/GiesRetentionandGraduation)

**Tableau workbook:** [Download the packaged workbook](dashboard/gies_dashboard.twbx) with the three data extracts included.

**Memo:** [memo/findings.pdf](memo/findings.pdf)

*Independent project using public data. Not affiliated with the Gies College of Business or DAIR.*

## Key numbers

| Measure | Latest cohort | Gies | All campus | Gap (points) |
| --- | --- | --- | --- | --- |
| First-year retention | Fall 2025 | 97.33% | 94.88% | 2.45 |
| 4-year graduation | Fall 2020 | 88.10% | 74.21% | 13.89 |
| 6-year graduation | Fall 2020 | 92.72% | 85.04% | 7.68 |

- **Trend:** the 4-year gap held between 12.7 and 14.0 points over five cohorts, and the 6-year gap between 6.2 and 7.7. The retention gap ranged from 0.2 to 3.1 points with no clear direction.
- **Hypothesis test:** in the fall 2025 cohort, Gies retained 97.33% (n = 787) against 94.65% for the rest of campus (n = 8,408). The difference is 2.68 points (95% CI 1.46 to 3.91), z = 3.27, p = 0.0011.
- **Enrollment:** Gies graduate headcount rose from 1,093 in fall 2016 to 6,443 in fall 2026, almost six times as many. Undergraduate headcount rose 18%, from 3,102 to 3,652. Fall 2026 is the current term as DAIR reported it on Nov 2, 2026.

## Regression

OLS on 2023 IPEDS data, one row per institution. Outcome: six-year graduation rate.

| Model | Slope on retention | 95% CI | p | R² | n |
| --- | --- | --- | --- | --- | --- |
| Model 1: retention only | 1.681 | [1.561, 1.8] | 3.5e-50 | 0.883 | 106 |
| Model 2: retention + log(enrollment) | 1.675 | [1.536, 1.814] | 9.7e-44 | 0.883 | 106 |

UIUC's predicted rate is 84.5% and its actual rate is 84.9%, a residual of +0.4 points (residual SD 4.4), so it sits on the line. Adding enrollment does not change the fit. The slope stays between 1.66 and 1.98 across 2019–2023, and at 1.73 after removing high-influence schools.

**Limits:** this is institution-level and correlational, not causal. Selective schools have high retention and high graduation for shared reasons. With about 100 rows the estimate is rough. Rates come from different cohorts: in the 2023 files, retention follows the fall 2022 entrants and graduation the 2017 entrants.

## Dashboard views

Use the dashboard to compare a college and outcome measure against campus, explore fall enrollment by college and student level, and switch the IPEDS comparison by year and peer group. The peer view starts with the 2023 data for all 106 public research universities. The orange point is the University of Illinois Urbana-Champaign as a whole.

[![Published Tableau dashboard showing outcomes, enrollment, and IPEDS peers](dashboard/preview/dashboard_public.png)](https://public.tableau.com/app/profile/david.lepighe/viz/gies_dashboard/GiesRetentionandGraduation)

See the [Tableau workbook guide](dashboard/TABLEAU_GUIDE.md) for the release settings and validation checks.

## Data sources

| Source | URL | Downloaded | Filters | Years covered |
| --- | --- | --- | --- | --- |
| DAIR retention | https://dair.illinois.edu/access-data/retention-and-graduation-rates/ | Nov 2, 2026 | Retention Data Table, Crosstab CSV, default filters, Compare = None | 2021–2025 cohorts |
| DAIR graduation | same page | Nov 2, 2026 | Graduation Rate Data Table, cumulative and non-cumulative sheets, Crosstab CSV, default filters | 2016–2020 cohorts |
| DAIR enrollment | https://dair.illinois.edu/access-data/student-enrollment/ | Nov 2, 2026 | Historical Data, Historical Table, Crosstab CSV, default filters | File covers 1870–2026; used fall 2016–2026 |
| IPEDS | https://nces.ed.gov/ipeds/datacenter/data/ (complete data files HD, EF A, EF D, GR) | Nov 2, 2026 | Public, Carnegie 2021 Basic = 15 (107 schools before blanks) | 2019–2023 collections |

The DAIR dashboards default to these cohort ranges; earlier cohorts were not pulled. The sex breakdown and Degrees Awarded were not used in this analysis. The 2019–2022 IPEDS data uses revised files; 2023 uses the latest posted file because no revised file existed at download.

Full column definitions: [data/clean/README.md](data/clean/README.md).

## How to reproduce

```
pip install -r requirements.txt
python scripts/download_ipeds.py
```

Then run `notebooks/01_clean.ipynb`, `02_trends.ipynb` and `03_regression.ipynb` in order, and `python scripts/build_memo.py` for the PDF. The DAIR CSVs are already in `data/raw/dair/`.

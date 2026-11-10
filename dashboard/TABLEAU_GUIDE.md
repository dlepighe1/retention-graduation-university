# Tableau workbook guide

Open [the dashboard on Tableau Public](https://public.tableau.com/app/profile/david.lepighe/viz/gies_dashboard/GiesRetentionandGraduation) in a browser or open [`gies_dashboard.twbx`](gies_dashboard.twbx) in Tableau Desktop or Tableau Public Edition. The package includes the DAIR outcomes, DAIR enrollment, and IPEDS peer extracts, as well as the matching CSVs from `data/clean/`.

The opening view shows Gies, four-year graduation, all Gies student levels, and 2023 IPEDS data for all public research peers. The outcome axes adapt to the selected measure and college. The peer scatterplot fits one linear regression to all institutions in the selected group, including UIUC. The DAIR comparisons are college-level; the IPEDS comparison is institution-level.

## Refresh or republish

1. Rerun the analysis notebooks in order to refresh `data/clean/`. In Tableau Desktop, point the three text connections to those CSVs and refresh the full extracts. The headline cards and parameter-specific readouts describe a fixed data snapshot; update those fields, the cohort/source dates, and the year choices if the input data changes.
2. Restore the opening selections. Export a packaged workbook in Tableau Desktop and ensure all three extracts are enabled. `scripts/prepare_tableau.py` can apply the release defaults and portable paths to an extracted package; open its output in Tableau Public Edition to check the results. `scripts/build_twb.py` generates the earlier starter workbook, rather than this layout.
3. In Tableau Public Edition, choose **File → Save to Tableau Public**. Open the dashboard's share URL in a signed-out browser to check that it loads and the controls respond.

## Release checks

| View | Expected check for this snapshot |
| --- | --- |
| Gies four-year graduation | All five cohorts from 2016–2020 are visible. Fall 2020 is 88.10% versus 74.21% campus, a 13.89-point gap. |
| Gies first-year retention | Switching measures shows the 2021–2025 cohorts and a 2.45-point gap for fall 2025. |
| Gies enrollment | All levels shows 3,652 undergraduates and 6,443 graduate students in fall 2026. Professional shows a no-data message. |
| IPEDS 2023 | All peers shows 106 universities and R² 0.88; Public Big Ten shows 16 universities and R² 0.91. |

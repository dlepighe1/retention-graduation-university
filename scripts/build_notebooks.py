"""Write notebooks 01-03 from the cell text below. Run from the repo root, then execute them."""
import nbformat as nbf

def nb(path, cells):
    book = nbf.v4.new_notebook()
    book.cells = [nbf.v4.new_markdown_cell(c[3:]) if c.startswith("#md") else nbf.v4.new_code_cell(c.strip())
                  for c in cells]
    book.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(book, path)

CLEAN = [
"""#md# 01. Clean
Tidies the raw DAIR crosstabs and IPEDS files into the CSVs in `data/clean/`. Blank-cell counts and sanity checks are printed so nothing is dropped silently.""",
"""
from pathlib import Path
import re
import pandas as pd

ROOT = Path.cwd() if (Path.cwd() / "data").exists() else Path.cwd().parent
RAW, CLEAN = ROOT / "data/raw", ROOT / "data/clean"
UNZ = RAW / "ipeds/unz"
CLEAN.mkdir(exist_ok=True)

SHORT = {
    "Agricultural, Consumer, & Environmental Sciences (ACES)": "ACES",
    "Applied Health Sciences (AHS)": "AHS", "College of Media": "Media",
    "Division of Explatory Studies (DES)": "DES",  # DAIR's spelling, kept so the key matches the source
    "Education": "Education", "Fine & Applied Arts (FAA)": "FAA",
    "Gies College of Business": "Gies", "Grainger College of Engineering": "Grainger",
    "Liberal Arts & Sciences (LAS)": "LAS", "School of Information Sciences": "iSchool",
    "School of Social Work (SSW)": "SSW",
}
def num(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.strip(), errors="coerce")
""",
"""#md## DAIR retention
First-fall to second-fall retention by college at entry. Cohort size and number retained are kept so rates can be recomputed.""",
"""
ret = pd.read_csv(RAW / "dair/dair_retention_by_college.csv", sep="\\t", encoding="utf-16", header=1)
ret.columns = ["college", "measure"] + [c.split()[0] for c in ret.columns[2:]]
ret["measure"] = ret["measure"].str.strip()
ret = ret.melt(["college", "measure"], var_name="cohort", value_name="value")
print("retention blank cells:", ret["value"].isna().sum())
ret["value"] = num(ret["value"].astype(str).str.rstrip("%"))
ret = ret.pivot_table(index=["college", "cohort"], columns="measure", values="value").reset_index()
retention = pd.DataFrame({"college": ret["college"], "cohort": ret["cohort"].astype(int),
    "metric": "First-year retention", "cohort_size": ret["Size of Adjusted Cohort"],
    "count": ret["Number Retained"]})
""",
"""#md## DAIR graduation
The non-cumulative file reports graduates in each year group. Cumulative rates are built from it: 4-year = groups 3 + 4, 5-year adds group 5, 6-year adds group 6. A blank group is treated as zero graduates, and the check below proves that against DAIR's own cumulative file. Each group has a stray fourth row mislabeled "Size of Adjusted Cohort" (no trailing spaces) that repeats the graduate count, so it is dropped.""",
"""
grad = pd.read_csv(RAW / "dair/dair_graduation_noncumulative_by_college.csv", sep="\\t", encoding="utf-16")
grad.columns = ["college", "group", "raw_measure"] + [c.split()[0] for c in grad.columns[3:]]
grad = grad[grad["raw_measure"].isin(["Size of Adjusted Cohort  ", "Graduate Count "])].copy()
grad["measure"] = grad["raw_measure"].str.strip()
grad = grad.drop(columns="raw_measure").melt(["college", "group", "measure"], var_name="cohort", value_name="value")
blank_groups = grad[(grad["measure"] == "Graduate Count") & grad["value"].isna()]
print("blank graduate-count cells (treated as 0):", len(blank_groups))
print(blank_groups[["college", "group", "cohort"]].to_string(index=False))
grad["value"] = num(grad["value"])
grads = grad[grad["measure"] == "Graduate Count"].fillna({"value": 0}).pivot_table(
    index=["college", "cohort"], columns="group", values="value", aggfunc="sum").fillna(0)

official = pd.read_csv(RAW / "dair/dair_graduation_6yr_by_college.csv", sep="\\t", encoding="utf-16", header=1)
official.columns = ["college", "measure"] + [c.split()[0] for c in official.columns[2:]]
official["measure"] = official["measure"].str.strip()
official = official.melt(["college", "measure"], var_name="cohort", value_name="value")
official["value"] = num(official["value"].astype(str).str.rstrip("%"))
official = official.pivot_table(index=["college", "cohort"], columns="measure", values="value")
sizes = official["Size of Adjusted Cohort"]

# The School of Information Sciences has no entering cohort before 2020, so those rows do not exist.
no_cohort = grads.index.difference(official.index)
print("college x cohort rows with no cohort, dropped:", list(no_cohort))
assert all(college == "School of Information Sciences" for college, _ in no_cohort)
grads = grads.drop(no_cohort)
six = grads.sum(axis=1)
assert (six == official["Graduate Count"].reindex(six.index)).all(), "year groups do not sum to DAIR's cumulative count"
print("year groups sum to DAIR's cumulative graduate count for all", len(six), "college x cohort rows")

parts = []
for metric, groups in {"4-year graduation": ["3-Year", "4-Year"],
                       "5-year graduation": ["3-Year", "4-Year", "5-Year"],
                       "6-year graduation": ["3-Year", "4-Year", "5-Year", "6-Year"]}.items():
    part = grads[groups].sum(axis=1).rename("count").reset_index()
    part["metric"] = metric
    part["cohort"] = part["cohort"].astype(int)
    parts.append(part)
graduation = pd.concat(parts).merge(
    sizes.rename("cohort_size").reset_index().assign(cohort=lambda d: d["cohort"].astype(int)), on=["college", "cohort"])
""",
"""#md## Combine and add the campus row
DAIR's download has no campus row, so "All campus" is the sum of the 11 entering units. The retention total is checked against the campus figures on DAIR's dashboard (2021: 8,273 / 7,720; 2025: 9,195 / 8,724).""",
"""
rates = pd.concat([retention, graduation], ignore_index=True)
rates["college_short"] = rates["college"].map(SHORT)
assert rates["college_short"].notna().all()
campus = rates.groupby(["cohort", "metric"], as_index=False)[["cohort_size", "count"]].sum()
campus["college"] = campus["college_short"] = "All campus"
rates = pd.concat([rates, campus], ignore_index=True)
rates["rate_pct"] = (100 * rates["count"] / rates["cohort_size"]).round(2)
rates["cohort_size"] = rates["cohort_size"].astype(int)
rates["count"] = rates["count"].astype(int)
rates = rates[["college", "college_short", "cohort", "metric", "cohort_size", "count", "rate_pct"]].sort_values(
    ["metric", "college_short", "cohort"])

check = rates[(rates["college"] == "All campus") & (rates["metric"] == "First-year retention")].set_index("cohort")
dashboard_totals = {2021: (8273, 7720), 2022: (7943, 7492), 2023: (8314, 7882), 2024: (9002, 8582), 2025: (9195, 8724)}
for cohort, (size, kept) in dashboard_totals.items():
    print(cohort, "sum of colleges", check.loc[cohort, "cohort_size"], check.loc[cohort, "count"], "| DAIR campus", size, kept)
    assert abs(check.loc[cohort, "cohort_size"] - size) <= 0.01 * size

assert rates["rate_pct"].between(0, 100).all()
assert not rates.duplicated(["college", "cohort", "metric"]).any()
assert rates.loc[rates["metric"] == "First-year retention", "cohort"].between(2021, 2025).all()
assert rates.loc[rates["metric"] != "First-year retention", "cohort"].between(2016, 2020).all()
rates.to_csv(CLEAN / "dair_rates.csv", index=False)
rates.shape
""",
"""#md## DAIR enrollment
Fall headcount by college and level, from the Historical Table crosstab. Skipped with a message if the raw file is not present yet.""",
"""
enroll_path = RAW / "dair/dair_enrollment_historical.csv"
if enroll_path.exists():
    enr = pd.read_csv(enroll_path, sep="\\t", encoding="utf-16", header=None, dtype=str)
    years = enr.iloc[0, 2:].str.extract(r"(\\d{4})")[0]
    header_row = 0
    if years.notna().sum() < 5:
        header_row = 1
        years = enr.iloc[1, 2:].str.extract(r"(\\d{4})")[0]
    body = enr.iloc[header_row + 1:].copy()
    body.columns = ["college_raw", "level"] + years.tolist()
    body["college_raw"] = body["college_raw"].ffill()
    long = body.melt(["college_raw", "level"], var_name="fall_year", value_name="headcount").dropna(subset=["fall_year"])
    print("blank enrollment cells:", long["headcount"].isna().sum(), "of", len(long))
    long["headcount"] = num(long["headcount"])
    long = long.dropna(subset=["headcount"])
    long["fall_year"] = long["fall_year"].astype(int)
    long = long[long["fall_year"] >= 2016]
    long["college"] = long["college_raw"].str.split("/").str[0].str.strip()
    long = long[long["level"].isin(["Undergraduate", "Graduate", "Professional"])]
    enrollment = long.groupby(["college", "fall_year", "level"], as_index=False)["headcount"].sum()
    enrollment["headcount"] = enrollment["headcount"].astype(int)
    assert not enrollment.duplicated(["college", "fall_year", "level"]).any()
    assert (enrollment["headcount"] >= 0).all()
    enrollment.to_csv(CLEAN / "dair_enrollment.csv", index=False)
    print(enrollment[enrollment["college"].str.startswith("Gies")].tail(8).to_string(index=False))
else:
    print("MISSING RAW FILE: data/raw/dair/dair_enrollment_historical.csv, so dair_enrollment.csv was not built")
""",
"""#md## IPEDS peers
One row per institution per year, for 2019-2023. The institution set is fixed from the 2023 directory: public universities with Carnegie 2021 Basic = 15 (doctoral, very high research). Revised `_rv` files are used wherever NCES has published them. Graduation rate is completers within 150% of normal time over the adjusted cohort (GRTYPE 3 / GRTYPE 2), which is the definition of "Graduation rate, total cohort".""",
"""
def read(stem):
    revised = UNZ / f"{stem}_rv.csv"
    path = revised if revised.exists() else next(p for p in UNZ.iterdir() if p.name.lower() == f"{stem}.csv")
    frame = pd.read_csv(path, encoding="latin1", low_memory=False)
    frame.columns = frame.columns.str.strip().str.replace("ï»¿", "")
    return frame, path.name

hd, hd_name = read("hd2023")
base = hd[(hd["C21BASIC"] == 15) & (hd["CONTROL"] == 1)][["UNITID", "INSTNM", "STABBR"]]
base.columns = ["unitid", "institution", "state"]

# 16 of the 18 Big Ten members are public. Northwestern and USC are private, so they fall outside this set.
BIG_TEN = {145637: "Illinois", 151351: "Indiana", 153658: "Iowa", 163286: "Maryland", 170976: "Michigan",
           171100: "Michigan State", 174066: "Minnesota", 181464: "Nebraska", 204796: "Ohio State", 209551: "Oregon",
           214777: "Penn State", 243780: "Purdue", 186380: "Rutgers", 110662: "UCLA", 236948: "Washington", 240444: "Wisconsin"}
print(base[base["unitid"].isin(BIG_TEN)]["institution"].to_string(index=False))
assert base["unitid"].isin(BIG_TEN).sum() == 16

rows, files = [], []
for year in range(2019, 2024):
    ef_d, n1 = read(f"ef{year}d"); ef_a, n2 = read(f"ef{year}a"); gr, n3 = read(f"gr{year}")
    files.append({"year": year, "files": ", ".join([n1, n2, n3])})
    total = ef_a[ef_a["EFALEVEL"] == 1].set_index("UNITID")["EFTOTLT"]
    cohort = gr[gr["GRTYPE"] == 2].set_index("UNITID")["GRTOTLT"]
    done = gr[gr["GRTYPE"] == 3].set_index("UNITID")["GRTOTLT"]
    frame = base.copy()
    frame["year"] = year
    frame["retention_rate"] = frame["unitid"].map(ef_d.set_index("UNITID")["RET_PCF"])
    frame["grad_cohort"] = frame["unitid"].map(cohort)
    frame["grad_completers"] = frame["unitid"].map(done)
    frame["grad_rate_6yr"] = (100 * frame["grad_completers"] / frame["grad_cohort"]).round(1)
    frame["enrollment"] = frame["unitid"].map(total)
    rows.append(frame)
peers = pd.concat(rows, ignore_index=True)
print(pd.DataFrame(files).to_string(index=False))

blank = peers[["retention_rate", "grad_rate_6yr", "enrollment"]].isna().sum()
print("blank IPEDS cells:", blank.to_dict())
peers = peers.dropna(subset=["retention_rate", "grad_rate_6yr", "enrollment"]).copy()
peers["enrollment"] = peers["enrollment"].astype(int)
peers["big_ten"] = peers["unitid"].isin(BIG_TEN).map({True: "Big Ten", False: "Other public R1"})
peers["is_uiuc"] = (peers["unitid"] == 145637).map({True: "UIUC", False: "Peer"})
peers = peers.drop(columns=["grad_cohort", "grad_completers"])

assert peers["retention_rate"].between(0, 100).all() and peers["grad_rate_6yr"].between(0, 100).all()
assert not peers.duplicated(["unitid", "year"]).any()
assert peers["year"].between(2019, 2023).all()
peers.to_csv(CLEAN / "ipeds_peers.csv", index=False)
print(peers.groupby("year").size().to_string())
print(peers[peers["unitid"] == 145637].to_string(index=False))
""",
]

TRENDS = [
"""#md# 02. Trends
Gies against all campus on retention and graduation, plus the Gies enrollment trend. "All campus" includes Gies. Retention covers the 2021-2025 cohorts and graduation the 2016-2020 cohorts, because a cohort needs six years to finish, so the two series describe different students.""",
"""
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm, linregress

ROOT = Path.cwd() if (Path.cwd() / "data").exists() else Path.cwd().parent
rates = pd.read_csv(ROOT / "data/clean/dair_rates.csv")
FIG = ROOT / "dashboard/preview"; FIG.mkdir(parents=True, exist_ok=True)
ACCENT, GRAY = "#D9480F", "#8A8F98"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})

wide = rates[rates["college_short"].isin(["Gies", "All campus"])].pivot_table(
    index=["metric", "cohort"], columns="college_short", values="rate_pct")
wide["gap_pts"] = (wide["Gies"] - wide["All campus"]).round(2)
print(wide.to_string())
""",
"""#md## Is the gap widening or narrowing?
Slope of the Gies-minus-campus gap per cohort. Five points is a thin basis, so this is a description of direction, not a test.""",
"""
trend = {}
for metric, part in wide.reset_index().groupby("metric"):
    fit = linregress(part["cohort"], part["gap_pts"])
    trend[metric] = {"first_gap": float(part["gap_pts"].iloc[0]), "last_gap": float(part["gap_pts"].iloc[-1]),
                     "largest_gap": float(part["gap_pts"].max()), "smallest_gap": float(part["gap_pts"].min()),
                     "slope_pts_per_cohort": round(float(fit.slope), 2)}
print(pd.DataFrame(trend).T.to_string())
""",
"""#md## How Gies ranks among colleges (latest cohort)""",
"""
latest = {"First-year retention": 2025, "4-year graduation": 2020, "6-year graduation": 2020}
ranks = {}
for metric, cohort in latest.items():
    part = rates[(rates["metric"] == metric) & (rates["cohort"] == cohort) & (rates["college"] != "All campus")]
    ordered = part.sort_values("rate_pct", ascending=False).reset_index(drop=True)
    ranks[metric] = int(ordered.index[ordered["college_short"] == "Gies"][0] + 1)
    print(metric, cohort, "| Gies rank", ranks[metric], "of", len(ordered), "|",
          ", ".join(f"{a} {b:.1f}" for a, b in zip(ordered["college_short"], ordered["rate_pct"])))
""",
"""#md## Two-proportion z-test, latest retention cohort
DAIR gives counts, so the test can run. Gies is compared with the rest of campus (everyone except Gies) because the two groups must not overlap. The unit is the whole cohort rather than a random sample, so the p-value is a guide to how large the gap is against ordinary year-to-year chance, not a survey margin of error.""",
"""
ret = rates[(rates["metric"] == "First-year retention") & (rates["cohort"] == 2025)].set_index("college_short")
x1, n1 = ret.loc["Gies", "count"], ret.loc["Gies", "cohort_size"]
x2 = ret.loc["All campus", "count"] - x1; n2 = ret.loc["All campus", "cohort_size"] - n1
p1, p2, pooled = x1 / n1, x2 / n2, (x1 + x2) / (n1 + n2)
se = (pooled * (1 - pooled) * (1 / n1 + 1 / n2)) ** 0.5
z = (p1 - p2) / se
p_value = 2 * norm.sf(abs(z))
se_diff = (p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2) ** 0.5
ztest = {"gies_pct": round(100 * p1, 2), "rest_of_campus_pct": round(100 * p2, 2), "diff_pts": round(100 * (p1 - p2), 2),
         "ci_low": round(100 * (p1 - p2 - 1.96 * se_diff), 2), "ci_high": round(100 * (p1 - p2 + 1.96 * se_diff), 2),
         "z": round(z, 2), "p_value": float(f"{p_value:.2g}"), "n_gies": int(n1), "n_rest": int(n2)}
print(ztest)
""",
"""#md## Gies enrollment""",
"""
path = ROOT / "data/clean/dair_enrollment.csv"
enrollment_note = "not available"
if path.exists():
    enr = pd.read_csv(path)
    gies = enr[enr["college"].str.startswith("Gies")].pivot_table(index="fall_year", columns="level", values="headcount").fillna(0).astype(int)
    print(gies.to_string())
    enrollment_note = gies.iloc[[0, -1]].to_dict()
else:
    print("Enrollment file not built yet")
""",
"""#md## Preview chart and saved numbers
A preview of dashboard view 1, used until the Tableau export exists.""",
"""
fig, axes = plt.subplots(1, 3, figsize=(10, 3), sharey=False)
for ax, metric in zip(axes, ["First-year retention", "4-year graduation", "6-year graduation"]):
    part = wide.loc[metric]
    ax.plot(part.index, part["All campus"], color=GRAY, lw=2, marker="o", ms=4)
    ax.plot(part.index, part["Gies"], color=ACCENT, lw=2, marker="o", ms=4)
    ax.set_title(metric, loc="left", fontsize=10)
    ax.set_xticks(part.index); ax.tick_params(labelsize=8); ax.grid(axis="y", color="#E6E6E3", lw=.7)
    ax.annotate(f"Gies {part['Gies'].iloc[-1]:.1f}%", (part.index[-1], part["Gies"].iloc[-1]), xytext=(0, 7),
                textcoords="offset points", ha="right", fontsize=8, color="#333")
    ax.annotate(f"Campus {part['All campus'].iloc[-1]:.1f}%", (part.index[-1], part["All campus"].iloc[-1]), xytext=(0, -13),
                textcoords="offset points", ha="right", fontsize=8, color="#333")
    span = part[["Gies", "All campus"]]
    ax.set_ylim(span.min().min() - 3, span.max().max() + 3)
axes[0].set_ylabel("Rate (%)", fontsize=9)
for ax in axes: ax.set_xlabel("Entering cohort (fall)", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "view1_gies_vs_campus.png", dpi=200); plt.show()

(ROOT / "notebooks/trends_numbers.json").write_text(json.dumps(
    {"trend": trend, "ranks": ranks, "ztest": ztest,
     "latest": {m: wide.loc[m].iloc[-1].to_dict() for m in latest}}, indent=2))
""",
]

REG = [
"""#md# 03. Regression
Does first-year retention predict six-year graduation across public research universities? OLS on the most recent year, one row per institution.""",
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

ROOT = Path.cwd() if (Path.cwd() / "data").exists() else Path.cwd().parent
peers = pd.read_csv(ROOT / "data/clean/ipeds_peers.csv")
year = peers["year"].max()
d = peers[peers["year"] == year].copy()
d["log_enrollment"] = np.log(d["enrollment"])
m1 = smf.ols("grad_rate_6yr ~ retention_rate", d).fit()
m2 = smf.ols("grad_rate_6yr ~ retention_rate + log_enrollment", d).fit()
print(year, len(d)); print(m1.summary()); print(m2.summary())
""",
"""#md## Fit checks
Heteroskedasticity-robust errors and leave-out checks show whether a few low-retention schools drive the slope.""",
"""
robust = m1.get_robustcov_results("HC3")
print("HC3 slope CI:", robust.conf_int()[1].round(3))
influence = m1.get_influence().cooks_distance[0]
d["cooks"] = influence
print(d.nlargest(5, "cooks")[["institution", "retention_rate", "grad_rate_6yr", "cooks"]].to_string(index=False))
trim = smf.ols("grad_rate_6yr ~ retention_rate", d[d["cooks"] < 4 / len(d)]).fit()
print("slope without high-influence schools:", round(trim.params["retention_rate"], 3), "n", int(trim.nobs))
by_year = {int(y): round(smf.ols("grad_rate_6yr ~ retention_rate", g).fit().params["retention_rate"], 3)
           for y, g in peers.groupby("year")}
print("slope by year:", by_year)
""",
"""#md## Where UIUC sits
Residual is actual minus predicted graduation rate.""",
"""
d["predicted"] = m1.fittedvalues
d["residual"] = m1.resid
d["predicted_m2"] = m2.fittedvalues
d["residual_m2"] = m2.resid
uiuc = d[d["unitid"] == 145637].iloc[0]
d["resid_rank"] = d["residual"].rank(ascending=False).astype(int)
print(d[d["unitid"] == 145637][["institution", "retention_rate", "grad_rate_6yr", "enrollment", "predicted", "residual", "residual_m2", "resid_rank"]].T.to_string())
print("residual SD:", round(m1.resid.std(), 2))
print(d[d["big_ten"] == "Big Ten"].sort_values("grad_rate_6yr", ascending=False)[["institution", "retention_rate", "grad_rate_6yr", "residual"]].round(1).to_string(index=False))
""",
"""
ROWS = []
for name, model in (("Model 1: retention only", m1), ("Model 2: retention + log(enrollment)", m2)):
    ci = model.conf_int().loc["retention_rate"]
    ROWS.append({"model": name, "slope": round(model.params["retention_rate"], 3), "ci_low": round(ci[0], 3), "ci_high": round(ci[1], 3),
                 "p_value": f"{model.pvalues['retention_rate']:.2g}", "r_squared": round(model.rsquared, 3), "n": int(model.nobs)})
table = pd.DataFrame(ROWS)
print(table.to_string(index=False))
lines = ["| Model | Slope on retention | 95% CI | p | R² | n |", "| --- | --- | --- | --- | --- | --- |"]
lines += [f"| {r.model} | {r.slope} | [{r.ci_low}, {r.ci_high}] | {r.p_value} | {r.r_squared} | {r.n} |" for r in table.itertuples()]
(ROOT / "notebooks/regression_table.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")

(ROOT / "notebooks/regression_numbers.json").write_text(json.dumps({
    "year": int(year), "n": int(m1.nobs), "models": ROWS,
    "log_enrollment_coef": round(m2.params["log_enrollment"], 3), "log_enrollment_p": f"{m2.pvalues['log_enrollment']:.2g}",
    "uiuc": {k: round(float(uiuc[k]), 2) for k in ["retention_rate", "grad_rate_6yr", "predicted", "residual", "residual_m2"]},
    "uiuc_resid_rank": int(d.loc[d["unitid"] == 145637, "resid_rank"].iloc[0]), "residual_sd": round(float(m1.resid.std()), 2),
    "trim_slope": round(float(trim.params["retention_rate"]), 3), "slope_by_year": by_year}, indent=2))

fig, ax = plt.subplots(figsize=(6.5, 4.2))
others = d[d["unitid"] != 145637]
ax.scatter(others["retention_rate"], others["grad_rate_6yr"], s=22, color="#8A8F98", alpha=.7, linewidth=0)
xs = np.linspace(d["retention_rate"].min(), d["retention_rate"].max(), 50)
ax.plot(xs, m1.params["Intercept"] + m1.params["retention_rate"] * xs, color="#55595F", lw=1.5)
ax.scatter([uiuc["retention_rate"]], [uiuc["grad_rate_6yr"]], s=70, color="#D9480F", zorder=3)
ax.annotate("UIUC", (uiuc["retention_rate"], uiuc["grad_rate_6yr"]), xytext=(18, -30), textcoords="offset points", ha="left", fontsize=9, color="#222",
            arrowprops={"arrowstyle": "-", "color": "#555", "lw": .8})
ax.set_xlabel("First-year retention rate (%)"); ax.set_ylabel("Six-year graduation rate (%)")
ax.set_title(f"Retention tracks graduation across {int(m1.nobs)} public research universities, {year}", loc="left", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#E6E6E3", lw=.6)
fig.tight_layout(); fig.savefig(ROOT / "dashboard/preview/view3_peer_scatter.png", dpi=200); plt.show()
""",
"""#md## Limits
- Institution-level and correlational. It does not show that raising retention at one school would raise its graduation rate, and it says nothing about individual students.
- Selective schools have high retention and high graduation for shared reasons such as student preparation and resources.
- With about 100 schools the estimate is rough.
- Rates come from different cohorts. In the 2023 files, retention follows students who entered in fall 2022 and graduation follows students who entered in 2017.
- Retention is capped near 100, so the relationship is compressed among top schools.""",
]

nb("notebooks/01_clean.ipynb", CLEAN)
nb("notebooks/02_trends.ipynb", TRENDS)
nb("notebooks/03_regression.ipynb", REG)

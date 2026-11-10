"""Write dashboard/gies_dashboard.twb, a Tableau workbook wired to the CSVs in data/clean.

Run from the repo root: python scripts/build_twb.py
The CSV folder is written as an absolute path, so rerun this script if the repo moves.
"""
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
import uuid

import pandas as pd

ROOT = Path.cwd()
CLEAN = (ROOT / "data/clean").resolve().as_posix()
ACCENT, GRAY, LIGHT = "#d9480f", "#8a8f98", "#c9ccd1"
W, H = 1200, 1100


def q(text):
    """Tableau string literal inside an attribute, e.g. "Gies"."""
    return '"' + text + '"'


def a(value):
    return quoteattr(str(value))


rates = pd.read_csv(ROOT / "data/clean/dair_rates.csv")
colleges = sorted(c for c in rates["college_short"].unique() if c != "All campus")
metrics = ["First-year retention", "4-year graduation", "5-year graduation", "6-year graduation"]

# ---------- data sources ----------
TYPES = {"string": ("129", "string"), "integer": ("20", "integer"), "real": ("5", "real")}


def datasource(key, caption, filename, columns, extra_columns="", style=""):
    meta, rel = [], []
    for i, (name, dtype) in enumerate(columns):
        remote, local = TYPES[dtype]
        rel.append(f"<column datatype={a(dtype)} name={a(name)} ordinal={a(i)} />")
        meta.append(
            "<metadata-record class='column'>"
            f"<remote-name>{escape(name)}</remote-name><remote-type>{remote}</remote-type>"
            f"<local-name>[{escape(name)}]</local-name><parent-name>[{escape(filename)}]</parent-name>"
            f"<remote-alias>{escape(name)}</remote-alias><ordinal>{i}</ordinal><local-type>{local}</local-type>"
            f"<aggregation>{'Count' if dtype == 'string' else 'Sum'}</aggregation><contains-null>true</contains-null>"
            "</metadata-record>")
    table = "[" + filename.replace(".", "#") + "]"
    return f"""
    <datasource caption={a(caption)} inline='true' name={a('federated.' + key)} version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption={a(caption)} name={a('textscan.' + key)}>
            <connection class='textscan' directory={a(CLEAN)} filename={a(filename)} password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection={a('textscan.' + key)} name={a(filename)} table={a(table)} type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
            {''.join(rel)}
          </columns>
        </relation>
        <metadata-records>{''.join(meta)}</metadata-records>
      </connection>
      <aliases enabled='yes' />
      {extra_columns}
      {style}
    </datasource>"""


PARAM_COLLEGE = "[Parameter 1]"
PARAM_METRIC = "[Parameter 2]"


def param_column(name, caption, current, values):
    members = "".join(f"<member value={a(q(v))} />" for v in values)
    return (f"<column caption={a(caption)} datatype='string' name={a(name)} param-domain-type='list' role='measure' "
            f"type='nominal' value={a(q(current))}><calculation class='tableau' formula={a(q(current))} />"
            f"<members>{members}</members></column>")


PARAMS = (param_column(PARAM_COLLEGE, "Pick a college", "Gies", colleges)
          + param_column(PARAM_METRIC, "Pick a metric", "4-year graduation", metrics))

line_role = ('IF [college_short] = "All campus" THEN "All campus"\n'
             'ELSEIF [college_short] = [Parameters].[Parameter 1] THEN "Selected college"\nEND')
keep_row = ('[metric] = [Parameters].[Parameter 2] AND\n'
            '([college_short] = "All campus" OR [college_short] = [Parameters].[Parameter 1])')

RATES_COLS = [("college", "string"), ("college_short", "string"), ("cohort", "integer"), ("metric", "string"),
              ("cohort_size", "integer"), ("count", "integer"), ("rate_pct", "real")]
RATES_EXTRA = f"""
      <column datatype='integer' name='[cohort]' role='dimension' type='ordinal' />
      <column caption='Rate (%)' datatype='real' name='[rate_pct]' role='measure' type='quantitative' />
      <column caption='Line Role' datatype='string' name='[Calculation_LineRole]' role='dimension' type='nominal'>
        <calculation class='tableau' formula={a(line_role)} />
      </column>
      <column caption='Keep Row' datatype='boolean' name='[Calculation_KeepRow]' role='dimension' type='nominal'>
        <calculation class='tableau' formula={a(keep_row)} />
      </column>"""
RATES_STYLE = f"""
      <style>
        <style-rule element='mark'>
          <encoding attr='color' field='[none:Calculation_LineRole:nk]' type='palette'>
            <map to={a(ACCENT)}><bucket>{escape(q('Selected college'))}</bucket></map>
            <map to={a(GRAY)}><bucket>{escape(q('All campus'))}</bucket></map>
          </encoding>
        </style-rule>
      </style>"""

ENR_COLS = [("college", "string"), ("fall_year", "integer"), ("level", "string"), ("headcount", "integer")]
ENR_EXTRA = """
      <column datatype='integer' name='[fall_year]' role='dimension' type='ordinal' />
      <column caption='Headcount' datatype='integer' name='[headcount]' role='measure' type='quantitative' />"""
ENR_STYLE = f"""
      <style>
        <style-rule element='mark'>
          <encoding attr='color' field='[none:level:nk]' type='palette'>
            <map to={a(ACCENT)}><bucket>{escape(q('Undergraduate'))}</bucket></map>
            <map to={a(GRAY)}><bucket>{escape(q('Graduate'))}</bucket></map>
            <map to={a(LIGHT)}><bucket>{escape(q('Professional'))}</bucket></map>
          </encoding>
        </style-rule>
      </style>"""

PEER_COLS = [("unitid", "integer"), ("institution", "string"), ("state", "string"), ("year", "integer"),
             ("retention_rate", "real"), ("grad_rate_6yr", "real"), ("enrollment", "integer"),
             ("big_ten", "string"), ("is_uiuc", "string")]
PEER_EXTRA = """
      <column datatype='integer' name='[unitid]' role='dimension' type='ordinal' />
      <column datatype='integer' name='[year]' role='dimension' type='ordinal' />
      <column caption='First-year retention rate (%)' datatype='real' name='[retention_rate]' role='measure' type='quantitative' />
      <column caption='Six-year graduation rate (%)' datatype='real' name='[grad_rate_6yr]' role='measure' type='quantitative' />"""
PEER_STYLE = f"""
      <style>
        <style-rule element='mark'>
          <encoding attr='color' field='[none:is_uiuc:nk]' type='palette'>
            <map to={a(ACCENT)}><bucket>{escape(q('UIUC'))}</bucket></map>
            <map to={a(GRAY)}><bucket>{escape(q('Peer'))}</bucket></map>
          </encoding>
        </style-rule>
      </style>"""

DATASOURCES = f"""
  <datasources>
    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>
      <aliases enabled='yes' />
      {PARAMS}
    </datasource>
    {datasource('rates', 'dair_rates', 'dair_rates.csv', RATES_COLS, RATES_EXTRA, RATES_STYLE)}
    {datasource('enroll', 'dair_enrollment', 'dair_enrollment.csv', ENR_COLS, ENR_EXTRA, ENR_STYLE)}
    {datasource('peers', 'ipeds_peers', 'ipeds_peers.csv', PEER_COLS, PEER_EXTRA, PEER_STYLE)}
  </datasources>"""


# ---------- worksheets ----------
def title(lines):
    runs = []
    for i, (text, bold, size) in enumerate(lines):
        if i:
            runs.append("<run>Æ&#10;</run>")
        runs.append(f"<run{' bold=' + a('true') if bold else ''} fontsize={a(size)}>{escape(text)}</run>")
    return f"<layout-options><title><formatted-text>{''.join(runs)}</formatted-text></title></layout-options>"


def axis_title(field, scope, text):
    return f"<format attr='title' class='0' field={a(field)} scope={a(scope)} value={a(text)} />"


def worksheet(name, layout, sources, deps, filters, slices, aggregate, mark, encodings, rows, cols, axes):
    src = "".join(f"<datasource {'caption=' + a(c) + ' ' if c else ''}name={a(n)} />" for n, c in sources)
    slice_xml = f"<slices>{''.join(f'<column>{s}</column>' for s in slices)}</slices>" if slices else ""
    return f"""
    <worksheet name={a(name)}>
      {layout}
      <table>
        <view>
          <datasources>{src}</datasources>
          {deps}
          {filters}
          {slice_xml}
          <aggregation value={a('true' if aggregate else 'false')} />
        </view>
        <style><style-rule element='axis'>{axes}</style-rule></style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view><breakdown value='auto' /></view>
            <mark class={a(mark)} />
            <encodings>{encodings}</encodings>
          </pane>
        </panes>
        <rows>{rows}</rows>
        <cols>{cols}</cols>
      </table>
    </worksheet>"""


R = "[federated.rates]"
V1 = worksheet(
    "Retention and graduation",
    title([("Gies beats the campus rate on every measure, most on 4-year graduation", True, 13),
           ("<[Parameters].[Parameter 1]> vs all campus: <[Parameters].[Parameter 2]>", False, 10)]),
    # The real data source must come first: Tableau treats the first entry as the
    # sheet's primary source, and Parameters cannot be one.
    [("federated.rates", "dair_rates"), ("Parameters", None)],
    f"""<datasource-dependencies datasource='Parameters'>{PARAMS}</datasource-dependencies>
          <datasource-dependencies datasource='federated.rates'>
            <column datatype='string' name='[college_short]' role='dimension' type='nominal' />
            <column datatype='string' name='[metric]' role='dimension' type='nominal' />
            <column datatype='integer' name='[cohort]' role='dimension' type='ordinal' />
            <column caption='Rate (%)' datatype='real' name='[rate_pct]' role='measure' type='quantitative' />
            <column caption='Line Role' datatype='string' name='[Calculation_LineRole]' role='dimension' type='nominal'>
              <calculation class='tableau' formula={a(line_role)} />
            </column>
            <column caption='Keep Row' datatype='boolean' name='[Calculation_KeepRow]' role='dimension' type='nominal'>
              <calculation class='tableau' formula={a(keep_row)} />
            </column>
            <column-instance column='[cohort]' derivation='None' name='[none:cohort:ok]' pivot='key' type='ordinal' />
            <column-instance column='[rate_pct]' derivation='Sum' name='[sum:rate_pct:qk]' pivot='key' type='quantitative' />
            <column-instance column='[Calculation_LineRole]' derivation='None' name='[none:Calculation_LineRole:nk]' pivot='key' type='nominal' />
            <column-instance column='[Calculation_KeepRow]' derivation='None' name='[none:Calculation_KeepRow:nk]' pivot='key' type='nominal' />
          </datasource-dependencies>""",
    f"""<filter class='categorical' column='{R}.[none:Calculation_KeepRow:nk]'>
            <groupfilter function='member' level='[none:Calculation_KeepRow:nk]' member='true' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />
          </filter>""",
    [f"{R}.[none:Calculation_KeepRow:nk]"], True, "Line",
    f"<color column='{R}.[none:Calculation_LineRole:nk]' />",
    f"{R}.[sum:rate_pct:qk]", f"{R}.[none:cohort:ok]",
    axis_title(f"{R}.[sum:rate_pct:qk]", "rows", "Rate (%)") + axis_title(f"{R}.[none:cohort:ok]", "cols", "Entering cohort (fall)"))

E = "[federated.enroll]"
V2 = worksheet(
    "Enrollment",
    title([("Gies graduate enrollment grew almost sixfold since fall 2016, while undergraduate enrollment rose 18%", True, 13)]),
    [("federated.enroll", "dair_enrollment")],
    """<datasource-dependencies datasource='federated.enroll'>
            <column datatype='string' name='[college]' role='dimension' type='nominal' />
            <column datatype='string' name='[level]' role='dimension' type='nominal' />
            <column datatype='integer' name='[fall_year]' role='dimension' type='ordinal' />
            <column caption='Headcount' datatype='integer' name='[headcount]' role='measure' type='quantitative' />
            <column-instance column='[college]' derivation='None' name='[none:college:nk]' pivot='key' type='nominal' />
            <column-instance column='[level]' derivation='None' name='[none:level:nk]' pivot='key' type='nominal' />
            <column-instance column='[fall_year]' derivation='None' name='[none:fall_year:ok]' pivot='key' type='ordinal' />
            <column-instance column='[headcount]' derivation='Sum' name='[sum:headcount:qk]' pivot='key' type='quantitative' />
          </datasource-dependencies>""",
    f"""<filter class='categorical' column='{E}.[none:college:nk]'>
            <groupfilter function='member' level='[none:college:nk]' member={a(q('Gies College of Business'))} user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />
          </filter>
          <filter class='categorical' column='{E}.[none:level:nk]'>
            <groupfilter function='level-members' level='[none:level:nk]' user:ui-enumeration='all' user:ui-marker='enumerate' />
          </filter>""",
    [f"{E}.[none:college:nk]", f"{E}.[none:level:nk]"], True, "Bar",
    f"<color column='{E}.[none:level:nk]' />",
    f"{E}.[sum:headcount:qk]", f"{E}.[none:fall_year:ok]",
    axis_title(f"{E}.[sum:headcount:qk]", "rows", "Headcount") + axis_title(f"{E}.[none:fall_year:ok]", "cols", "Fall term"))

P = "[federated.peers]"
V3 = worksheet(
    "Peer comparison",
    title([("Illinois graduates about what its first-year retention predicts", True, 13)]),
    [("federated.peers", "ipeds_peers")],
    """<datasource-dependencies datasource='federated.peers'>
            <column datatype='string' name='[institution]' role='dimension' type='nominal' />
            <column datatype='string' name='[big_ten]' role='dimension' type='nominal' />
            <column datatype='string' name='[is_uiuc]' role='dimension' type='nominal' />
            <column datatype='integer' name='[year]' role='dimension' type='ordinal' />
            <column caption='First-year retention rate (%)' datatype='real' name='[retention_rate]' role='measure' type='quantitative' />
            <column caption='Six-year graduation rate (%)' datatype='real' name='[grad_rate_6yr]' role='measure' type='quantitative' />
            <column-instance column='[institution]' derivation='None' name='[none:institution:nk]' pivot='key' type='nominal' />
            <column-instance column='[big_ten]' derivation='None' name='[none:big_ten:nk]' pivot='key' type='nominal' />
            <column-instance column='[is_uiuc]' derivation='None' name='[none:is_uiuc:nk]' pivot='key' type='nominal' />
            <column-instance column='[year]' derivation='None' name='[none:year:ok]' pivot='key' type='ordinal' />
            <column-instance column='[retention_rate]' derivation='None' name='[none:retention_rate:qk]' pivot='key' type='quantitative' />
            <column-instance column='[grad_rate_6yr]' derivation='None' name='[none:grad_rate_6yr:qk]' pivot='key' type='quantitative' />
          </datasource-dependencies>""",
    f"""<filter class='categorical' column='{P}.[none:year:ok]'>
            <groupfilter function='member' level='[none:year:ok]' member='2023' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />
          </filter>
          <filter class='categorical' column='{P}.[none:big_ten:nk]'>
            <groupfilter function='level-members' level='[none:big_ten:nk]' user:ui-enumeration='all' user:ui-marker='enumerate' />
          </filter>""",
    [f"{P}.[none:year:ok]", f"{P}.[none:big_ten:nk]"], False, "Circle",
    f"<color column='{P}.[none:is_uiuc:nk]' /><size column='{P}.[none:is_uiuc:nk]' /><lod column='{P}.[none:institution:nk]' />",
    f"{P}.[none:grad_rate_6yr:qk]", f"{P}.[none:retention_rate:qk]",
    axis_title(f"{P}.[none:grad_rate_6yr:qk]", "rows", "Six-year graduation rate (%)")
    + axis_title(f"{P}.[none:retention_rate:qk]", "cols", "First-year retention rate (%)"))

# ---------- dashboard ----------
ids = iter(range(2, 100))


def box(x, y, w, h):
    return (f"floating='true' h={a(round(h * 100000 / H))} id={a(next(ids))} "
            f"w={a(round(w * 100000 / W))} x={a(round(x * 100000 / W))} y={a(round(y * 100000 / H))}")


def text(x, y, w, h, body, size=9, bold=False, color="#333333"):
    run = f"<run{' bold=' + a('true') if bold else ''} fontcolor={a(color)} fontsize={a(size)}>{escape(body)}</run>"
    return f"<zone {box(x, y, w, h)} type-v2='text'><formatted-text>{run}</formatted-text></zone>"


def sheet(x, y, w, h, name):
    return f"<zone {box(x, y, w, h)} name={a(name)} />"


def param(x, y, w, h, worksheet_name, name):
    return f"<zone {box(x, y, w, h)} mode='compact' name={a(worksheet_name)} param={a('[Parameters].' + name)} type-v2='paramctrl' />"


def flt(x, y, w, h, worksheet_name, field, mode):
    return f"<zone {box(x, y, w, h)} mode={a(mode)} name={a(worksheet_name)} param={a(field)} type-v2='filter' values='database' />"


HOW = ("How to read this: Retention is the share of new full-time students who come back the next fall. Graduation is the share who "
       "finish within four or six years of starting. Use the dropdowns to change the college or measure. Orange is the selected college "
       "or Illinois, and gray is the comparison. In the bottom chart each dot is a university; dots above the line graduate more students "
       "than their retention predicts. These charts show patterns, not causes.")
SRC1 = ("Source: UIUC DAIR Retention and Graduation Rates, downloaded Nov 2, 2026. Population: first-time, full-time, "
        "degree-seeking undergraduates. All campus is the sum of the 11 entering units.")
SRC2 = "Source: UIUC DAIR Student Enrollment, downloaded Nov 2, 2026. Population: all students, fall headcount. Fall 2026 is the current term."
SRC3 = ("Source: NCES IPEDS, downloaded Nov 2, 2026. 106 public research universities in 2023, including 16 public Big Ten schools. "
        "A pattern across schools, not a cause.")

L, SW, CX, CW = 16, 900, 932, 252
ZONES = "".join([
    text(L, 8, 1168, 56, "How do Gies retention and graduation compare with campus and peer universities, and how strongly "
         "does first-year retention predict graduation?", 15, True, "#222222"),
    text(L, 66, 1168, 66, HOW, 9, False, "#444444"),
    sheet(L, 138, SW, 290, "Retention and graduation"),
    param(CX, 150, CW, 56, "Retention and graduation", PARAM_COLLEGE),
    param(CX, 212, CW, 56, "Retention and graduation", PARAM_METRIC),
    text(L, 430, 1168, 22, SRC1, 8, False, "#666666"),
    sheet(L, 458, SW, 270, "Enrollment"),
    flt(CX, 470, CW, 56, "Enrollment", f"{E}.[none:college:nk]", "dropdown"),
    flt(CX, 532, CW, 100, "Enrollment", f"{E}.[none:level:nk]", "checkdropdown"),
    text(L, 730, 1168, 22, SRC2, 8, False, "#666666"),
    sheet(L, 758, SW, 310, "Peer comparison"),
    flt(CX, 770, CW, 56, "Peer comparison", f"{P}.[none:year:ok]", "dropdown"),
    flt(CX, 832, CW, 100, "Peer comparison", f"{P}.[none:big_ten:nk]", "checkdropdown"),
    text(L, 1070, 1168, 24, SRC3, 8, False, "#666666"),
])

DASH = f"""
  <dashboards>
    <dashboard name='Gies Retention and Graduation'>
      <style />
      <size maxheight={a(H)} maxwidth={a(W)} minheight={a(H)} minwidth={a(W)} />
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
          {ZONES}
        </zone>
      </zones>
    </dashboard>
  </dashboards>"""


def window(cls, name, extra=""):
    if cls == "dashboard":
        views = "".join(f"<viewpoint name={a(s)}><zoom type='entire-view' /></viewpoint>"
                        for s in ("Retention and graduation", "Enrollment", "Peer comparison"))
        return f"<window class='dashboard' maximized='true' name={a(name)}><viewpoints>{views}</viewpoints><active id='-1' /></window>"
    return (f"<window class='worksheet' name={a(name)}{extra}><cards>"
            "<edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
            "<edge name='top'><strip size='2147483647'><card type='columns' /></strip>"
            "<strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge>"
            "</cards></window>")


WINDOWS = ("<windows source-height='30'>"
           + window("worksheet", "Retention and graduation")
           + window("worksheet", "Enrollment")
           + window("worksheet", "Peer comparison")
           + window("dashboard", "Gies Retention and Graduation")
           + "</windows>")

TWB = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='18.1' source-build='2026.3.0 (20263.26.1022.1645)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  {DATASOURCES}
  <worksheets>{V1}{V2}{V3}
  </worksheets>
  {DASH}
  {WINDOWS}
</workbook>
"""

out = ROOT / "dashboard/gies_dashboard.twb"
out.write_text(TWB, encoding="utf-8")
print("wrote", out)

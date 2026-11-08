# build_excel.py
# makes the excel workbook: nfl_draft_analysis.xlsx
# all the summary numbers are excel formulas that read from the data sheet
# run: python build_excel.py (after clean_data.py and analysis.py)

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.chart import BarChart, ScatterChart, Reference, Series

data = pd.read_csv("data/picks_clean.csv")
steals = pd.read_csv("outputs/q7_steals.csv")
busts = pd.read_csv("outputs/q8_busts.csv")
team_list = pd.read_csv("outputs/q6_team_ranking.csv")["team"].tolist()
position_list = ["OL", "LB", "DL", "QB", "RB", "DB", "WR", "TE"]

last = len(data) + 1  # last row on the data sheet

bold = Font(bold=True)
header_font = Font(bold=True, color="ffffff")
header_fill = PatternFill("solid", fgColor="1f2a44")
big = Font(bold=True, size=18)


def add_header(ws, row, names):
    for i in range(len(names)):
        cell = ws.cell(row=row, column=i + 1, value=names[i])
        cell.font = header_font
        cell.fill = header_fill


# ranges on the data sheet that the formulas use
draft_round = f"data!$B$2:$B${last}"
pick = f"data!$C$2:$C${last}"
team = f"data!$D$2:$D${last}"
group = f"data!$G$2:$G${last}"
value = f"data!$M$2:$M${last}"
starter = f"data!$N$2:$N${last}"
pro_bowler = f"data!$O$2:$O${last}"
over_expected = f"data!$Q$2:$Q${last}"

wb = Workbook()

# dashboard (filled in at the end) 
dash = wb.active
dash.title = "dashboard"

#  about 
about = wb.create_sheet("about")
notes = [
    ["question", "which draft picks, positions, and teams get the most value from the nfl draft?"],
    ["data", "every nfl draft pick from 2000-2019 (5,095 players), from nflverse / pro football reference"],
    ["career value", "pro football reference's weighted approximate value. one number for a whole career. players who never played = 0"],
    ["expected value", "what a player taken at that pick usually turns into (see the pick curve sheet)"],
    ["value over expected", "career value minus expected value. above 0 means the player beat his draft spot"],
    ["started 3+ seasons", "1 if the player started at least 3 seasons, otherwise 0"],
]
about["A1"] = "about this workbook"
about["A1"].font = big
for i in range(len(notes)):
    about.cell(row=i + 3, column=1, value=notes[i][0]).font = bold
    about.cell(row=i + 3, column=2, value=notes[i][1])
about.column_dimensions["A"].width = 20
about.column_dimensions["B"].width = 100

# data 
ws = wb.create_sheet("data")
add_header(ws, 1, ["season", "round", "pick", "team", "player", "position", "position group", "college",
                   "games", "seasons started", "pro bowls", "all-pro", "career value",
                   "started 3+ seasons", "pro bowler", "expected value", "value over expected"])
columns = ["season", "draft_round", "pick", "team", "player", "position", "position_group", "college",
           "games", "seasons_started", "probowls", "allpro", "career_value", "starter_3plus", "pro_bowler"]
rows = data[columns].values.tolist()
for i in range(len(rows)):
    r = i + 2
    for j in range(len(columns)):
        ws.cell(row=r, column=j + 1, value=rows[i][j])
    # look up the expected value for this pick on the pick curve sheet
    ws.cell(row=r, column=16, value=f"=INDEX('pick curve'!$D$2:$D$263,MATCH(C{r},'pick curve'!$A$2:$A$263,0))")
    ws.cell(row=r, column=17, value=f"=M{r}-P{r}")
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:Q{last}"
ws.column_dimensions["E"].width = 22
ws.column_dimensions["H"].width = 16

#  pick curve 
pc = wb.create_sheet("pick curve")
add_header(pc, 1, ["pick", "players", "average value", "expected value"])
for p in range(1, 263):
    r = p + 1
    pc.cell(row=r, column=1, value=p)
    pc.cell(row=r, column=2, value=f"=COUNTIF({pick},A{r})")
    pc.cell(row=r, column=3, value=f"=AVERAGEIFS({value},{pick},A{r})")
    if p <= 4:
        # top 4 picks just use their own average
        pc.cell(row=r, column=4, value=f"=C{r}")
    else:
        # average with the 4 picks before and after
        top = max(2, r - 4)
        bottom = min(263, r + 4)
        pc.cell(row=r, column=4, value=f"=AVERAGE(C{top}:C{bottom})")
    pc.cell(row=r, column=3).number_format = "0.0"
    pc.cell(row=r, column=4).number_format = "0.0"
pc.freeze_panes = "A2"
pc.column_dimensions["C"].width = 14
pc.column_dimensions["D"].width = 14

# by round 
br = wb.create_sheet("by round")
br["A1"] = "value and hit rate by round"
br["A1"].font = big
add_header(br, 3, ["round", "picks", "avg career value", "% started 3+ seasons", "% made pro bowl"])
for rd in range(1, 8):
    r = rd + 3
    br.cell(row=r, column=1, value=rd)
    br.cell(row=r, column=2, value=f"=COUNTIF({draft_round},A{r})")
    br.cell(row=r, column=3, value=f"=AVERAGEIFS({value},{draft_round},A{r})")
    br.cell(row=r, column=4, value=f"=AVERAGEIFS({starter},{draft_round},A{r})")
    br.cell(row=r, column=5, value=f"=AVERAGEIFS({pro_bowler},{draft_round},A{r})")
    br.cell(row=r, column=3).number_format = "0.0"
    br.cell(row=r, column=4).number_format = "0%"
    br.cell(row=r, column=5).number_format = "0%"
for col in ["B", "C", "D", "E"]:
    br.column_dimensions[col].width = 20

# by position 
bp = wb.create_sheet("by position")
bp["A1"] = "which positions beat their draft spot?"
bp["A1"].font = big
add_header(bp, 3, ["position", "picks", "avg career value", "avg value over expected",
                   "% started 3+ (all)", "% started 3+ (round 1)", "% started 3+ (rounds 4-7)"])
for i in range(len(position_list)):
    r = i + 4
    bp.cell(row=r, column=1, value=position_list[i])
    bp.cell(row=r, column=2, value=f"=COUNTIF({group},A{r})")
    bp.cell(row=r, column=3, value=f"=AVERAGEIFS({value},{group},A{r})")
    bp.cell(row=r, column=4, value=f"=AVERAGEIFS({over_expected},{group},A{r})")
    bp.cell(row=r, column=5, value=f"=AVERAGEIFS({starter},{group},A{r})")
    bp.cell(row=r, column=6, value=f"=AVERAGEIFS({starter},{group},A{r},{draft_round},1)")
    bp.cell(row=r, column=7, value=f"=AVERAGEIFS({starter},{group},A{r},{draft_round},\">=4\")")
    bp.cell(row=r, column=3).number_format = "0.0"
    bp.cell(row=r, column=4).number_format = "0.0"
    for col in [5, 6, 7]:
        bp.cell(row=r, column=col).number_format = "0%"
last_position = len(position_list) + 3
for col in ["B", "C", "D", "E", "F", "G"]:
    bp.column_dimensions[col].width = 22

# by team
bt = wb.create_sheet("by team")
bt["A1"] = "which teams drafted best? (2000-2019)"
bt["A1"].font = big
add_header(bt, 3, ["rank", "team", "picks", "avg value over expected", "pro bowlers drafted"])
first_team = 4
last_team = len(team_list) + 3
for i in range(len(team_list)):
    r = i + 4
    bt.cell(row=r, column=2, value=team_list[i])
    bt.cell(row=r, column=3, value=f"=COUNTIF({team},B{r})")
    bt.cell(row=r, column=4, value=f"=AVERAGEIFS({over_expected},{team},B{r})")
    bt.cell(row=r, column=5, value=f"=SUMIFS({pro_bowler},{team},B{r})")
    bt.cell(row=r, column=1, value=f"=RANK(D{r},$D${first_team}:$D${last_team})")
    bt.cell(row=r, column=4).number_format = "0.00"
for col in ["D", "E"]:
    bt.column_dimensions[col].width = 22

# steals and busts
sb = wb.create_sheet("steals and busts")
sb["A1"] = "biggest steals and top 10 busts"
sb["A1"].font = big
sb["A2"] = "copied from the sql queries q7_steals and q8_busts"

sb["A4"] = "biggest steals"
sb["A4"].font = bold
add_header(sb, 5, ["season", "round", "pick", "team", "player", "position",
                   "career value", "expected", "over expected"])
steal_rows = steals[["season", "draft_round", "pick", "team", "player", "position_group",
                     "career_value", "expected_value", "value_over_expected"]].values.tolist()
for i in range(len(steal_rows)):
    for j in range(len(steal_rows[i])):
        sb.cell(row=i + 6, column=j + 1, value=steal_rows[i][j])

start = len(steal_rows) + 8
sb.cell(row=start, column=1, value="biggest top 10 busts").font = bold
add_header(sb, start + 1, ["season", "pick", "team", "player", "position",
                           "career value", "expected", "over expected", "games"])
bust_rows = busts[["season", "pick", "team", "player", "position_group", "career_value",
                   "expected_value", "value_over_expected", "games"]].values.tolist()
for i in range(len(bust_rows)):
    for j in range(len(bust_rows[i])):
        sb.cell(row=start + 2 + i, column=j + 1, value=bust_rows[i][j])
sb.column_dimensions["D"].width = 20
sb.column_dimensions["E"].width = 20

#  dashboard 
dash["A1"] = "nfl draft value dashboard (2000-2019)"
dash["A1"].font = big
dash["A2"] = "career value = pro football reference's weighted approximate value"

numbers = [
    ["picks analyzed", f"=COUNTA(data!$E$2:$E${last})", "#,##0"],
    ["round 1 picks who started 3+ seasons", "='by round'!D4", "0%"],
    ["round 7 picks who started 3+ seasons", "='by round'!D10", "0%"],
    ["best position", f"=INDEX('by position'!A4:A{last_position},MATCH(MAX('by position'!D4:D{last_position}),'by position'!D4:D{last_position},0))", "@"],
    ["best drafting team", f"=INDEX('by team'!B{first_team}:B{last_team},MATCH(1,'by team'!A{first_team}:A{last_team},0))", "@"],
]
for i in range(len(numbers)):
    col = i * 3 + 1
    dash.cell(row=4, column=col, value=numbers[i][0])
    cell = dash.cell(row=5, column=col, value=numbers[i][1])
    cell.font = big
    cell.number_format = numbers[i][2]

# chart 1: expected value by pick
chart1 = ScatterChart()
chart1.title = "expected career value by pick"
chart1.x_axis.title = "pick"
chart1.y_axis.title = "career value"
xs = Reference(pc, min_col=1, min_row=2, max_row=263)
ys = Reference(pc, min_col=4, min_row=1, max_row=263)
line = Series(ys, xs, title_from_data=True)
line.marker.symbol = "none"
chart1.series.append(line)
chart1.legend = None
chart1.x_axis.delete = False
chart1.y_axis.delete = False
dash.add_chart(chart1, "A7")

# chart 2: starter and pro bowl rate by round
chart2 = BarChart()
chart2.title = "started 3+ seasons vs made a pro bowl"
chart2.add_data(Reference(br, min_col=4, max_col=5, min_row=3, max_row=10), titles_from_data=True)
chart2.set_categories(Reference(br, min_col=1, min_row=4, max_row=10))
chart2.x_axis.title = "round"
chart2.x_axis.delete = False
chart2.y_axis.delete = False
dash.add_chart(chart2, "J7")

# chart 3: value over expected by position
chart3 = BarChart()
chart3.title = "value over expected by position"
chart3.add_data(Reference(bp, min_col=4, min_row=3, max_row=last_position), titles_from_data=True)
chart3.set_categories(Reference(bp, min_col=1, min_row=4, max_row=last_position))
chart3.legend = None
chart3.x_axis.tickLblPos = "low"  # puts the labels at the bottom so they don't cover the bars
chart3.x_axis.delete = False
chart3.y_axis.delete = False
dash.add_chart(chart3, "A23")

# chart 4: value over expected by team
chart4 = BarChart()
chart4.title = "value over expected by team"
chart4.add_data(Reference(bt, min_col=4, min_row=3, max_row=last_team), titles_from_data=True)
chart4.set_categories(Reference(bt, min_col=2, min_row=first_team, max_row=last_team))
chart4.legend = None
chart4.x_axis.tickLblPos = "low"
chart4.width = 24
chart4.x_axis.delete = False
chart4.y_axis.delete = False
dash.add_chart(chart4, "J23")

for col in ["A", "D", "G", "J", "M"]:
    dash.column_dimensions[col].width = 18

wb.save("nfl_draft_analysis.xlsx")
print("saved nfl_draft_analysis.xlsx")

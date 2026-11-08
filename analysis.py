# analysis.py
# runs the sql queries, saves the results, and makes charts
# run: python analysis.py (after clean_data.py)

import os
import re
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
os.makedirs("charts", exist_ok=True)

blue = "#2a78d6"
orange = "#eb6834"
gray = "#b8b7b0"

# run every query in analysis.sql and save each one as a csv
con = sqlite3.connect("data/nfl_draft.db")
sql = open("sql/analysis.sql").read()
queries = re.findall(r"-- name: (\w+)\n(.*?)(?=-- name:|\Z)", sql, re.S)

results = {}
for name, query in queries:
    results[name] = pd.read_sql(query, con)
    results[name].to_csv("outputs/" + name + ".csv", index=False)
    print("ran", name)
con.close()

# chart 1: value by pick
curve = results["q2_pick_value_curve"]
plt.figure(figsize=(8, 4))
plt.scatter(curve["pick"], curve["avg_value"], s=10, color=gray, label="average at that pick")
plt.plot(curve["pick"], curve["expected_value"], color=blue, linewidth=2, label="expected value (smoothed)")
plt.title("value drops fastest in the first round")
plt.xlabel("pick number")
plt.ylabel("career value")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("charts/value_curve.png")
plt.close()

# chart 2: starter and pro bowl rate by round
rounds = results["q1_value_by_round"]
x = rounds["draft_round"]
plt.figure(figsize=(8, 4))
plt.bar(x - 0.2, rounds["pct_started_3plus"], width=0.4, color=blue, label="started 3+ seasons")
plt.bar(x + 0.2, rounds["pct_pro_bowlers"], width=0.4, color=orange, label="made a pro bowl")
plt.title("chance a pick becomes a starter or pro bowler")
plt.xlabel("round")
plt.ylabel("% of picks")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("charts/hit_rate_by_round.png")
plt.close()

# chart 3: value over expected by position
pos = results["q4_position_value"].sort_values("avg_value_over_expected")
colors = [blue if v >= 0 else orange for v in pos["avg_value_over_expected"]]
plt.figure(figsize=(7, 4))
plt.barh(pos["position_group"], pos["avg_value_over_expected"], color=colors)
plt.axvline(0, color="black", linewidth=1)
plt.title("offensive linemen beat their draft spot, tight ends don't")
plt.xlabel("career value above or below expected")
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("charts/position_value.png")
plt.close()

# chart 4: team ranking
teams = results["q6_team_ranking"].sort_values("avg_value_over_expected")
colors = [blue if v >= 0 else orange for v in teams["avg_value_over_expected"]]
plt.figure(figsize=(7, 7))
plt.barh(teams["team"], teams["avg_value_over_expected"], color=colors)
plt.axvline(0, color="black", linewidth=1)
plt.title("which teams drafted best (2000-2019)")
plt.xlabel("career value above or below expected, per pick")
plt.yticks(fontsize=8)
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig("charts/team_ranking.png")
plt.close()

print("saved csvs to outputs/ and charts to charts/")

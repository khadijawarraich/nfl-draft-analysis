# clean_data.py
# loads nfl draft picks from nflverse, cleans them, and saves them to a sqlite database
# run: python clean_data.py

import os
import sqlite3
import nflreadpy as nfl
import pandas as pd

os.makedirs("data/raw", exist_ok=True)

# load every draft pick (nflreadpy gives a polars table so turn it into pandas)
df = nfl.load_draft_picks().to_pandas()
df.to_csv("data/raw/draft_picks.csv", index=False)
print("raw data:", len(df), "picks")

# only keep 2000-2019 drafts
# players drafted after 2019 are still playing, so their careers aren't done yet
df = df[(df["season"] >= 2000) & (df["season"] <= 2019)]

# players who never played have no value, so count them as 0
df["games"] = df["games"].fillna(0)
df["career_value"] = df["w_av"].fillna(0)

# teams that moved cities count as one team
df["team"] = df["team"].replace({"OAK": "LVR", "SDG": "LAC", "STL": "LAR"})

# put positions into groups
groups = {
    "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
    "T": "OL", "OT": "OL", "G": "OL", "OG": "OL", "C": "OL", "OL": "OL",
    "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL",
    "LB": "LB", "OLB": "LB", "ILB": "LB",
    "DB": "DB", "CB": "DB", "S": "DB", "SAF": "DB", "FS": "DB",
    "K": "K/P", "P": "K/P", "LS": "K/P",
}
df["position_group"] = df["position"].map(groups)

# 1 or 0 columns so we can count hits
df["starter_3plus"] = (df["seasons_started"] >= 3).astype(int)
df["pro_bowler"] = (df["probowls"] >= 1).astype(int)
df["played"] = (df["games"] > 0).astype(int)

# keep the columns we need
df = df.rename(columns={"pfr_player_name": "player", "round": "draft_round"})
df = df[["season", "draft_round", "pick", "team", "player", "position", "position_group", "college",
         "games", "seasons_started", "probowls", "allpro", "career_value",
         "starter_3plus", "pro_bowler", "played"]]

# save to sqlite and make the views
con = sqlite3.connect("data/nfl_draft.db")
df.to_sql("picks", con, if_exists="replace", index=False)
con.executescript(open("sql/views.sql").read())

# save a csv with expected value added (used for the excel file)
clean = pd.read_sql("select * from v_picks order by season, pick", con)
clean.to_csv("data/picks_clean.csv", index=False)
con.close()

print("clean data:", len(clean), "picks from 2000-2019")

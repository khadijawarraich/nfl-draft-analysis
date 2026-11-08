-- analysis.sql
-- questions about the nfl draft (2000-2019)
-- each query starts with "-- name:" so analysis.py can run them one by one
-- career_value is pro football reference's weighted approximate value (higher = better career)

-- name: q1_value_by_round
-- how good are picks in each round?
select draft_round,
       count(*) as picks,
       round(avg(career_value), 1) as avg_career_value,
       round(100.0 * avg(played), 1) as pct_played,
       round(100.0 * avg(starter_3plus), 1) as pct_started_3plus,
       round(100.0 * avg(pro_bowler), 1) as pct_pro_bowlers
from picks
group by draft_round
order by draft_round;

-- name: q2_pick_value_curve
-- expected value at every pick number
select pick, players, avg_value, expected_value
from v_pick_expected
order by pick;

-- name: q3_pick_ranges
-- how does the #1 pick compare to later picks?
select case when pick = 1 then '1. pick 1'
            when pick <= 10 then '2. picks 2-10'
            when pick <= 32 then '3. picks 11-32'
            when pick <= 64 then '4. picks 33-64'
            when pick <= 100 then '5. picks 65-100'
            else '6. picks 101+' end as pick_range,
       count(*) as players,
       round(avg(career_value), 1) as avg_career_value,
       round(100.0 * avg(pro_bowler), 1) as pct_pro_bowlers
from picks
group by pick_range
order by pick_range;

-- name: q4_position_value
-- which positions do better than their draft spot?
-- above 0 = better than the average player taken at the same pick
select position_group,
       count(*) as picks,
       round(avg(career_value), 1) as avg_career_value,
       round(avg(value_over_expected), 2) as avg_value_over_expected,
       round(100.0 * avg(starter_3plus), 1) as pct_started_3plus
from v_picks
where position_group <> 'K/P'  -- kickers and punters are almost always late picks
group by position_group
order by avg_value_over_expected desc;

-- name: q5_position_by_round
-- starter rate by position in round 1, rounds 2-3, and rounds 4-7
select position_group,
       round(100.0 * avg(case when draft_round = 1 then starter_3plus end), 1) as round_1_pct,
       round(100.0 * avg(case when draft_round in (2, 3) then starter_3plus end), 1) as rounds_2_3_pct,
       round(100.0 * avg(case when draft_round >= 4 then starter_3plus end), 1) as rounds_4_7_pct
from picks
where position_group <> 'K/P'
group by position_group
order by round_1_pct desc;

-- name: q6_team_ranking
-- which teams drafted the best?
with teams as (
    select team,
           count(*) as picks,
           round(avg(value_over_expected), 2) as avg_value_over_expected,
           sum(pro_bowler) as pro_bowlers
    from v_picks
    group by team
)
select rank() over (order by avg_value_over_expected desc) as team_rank,
       team, picks, avg_value_over_expected, pro_bowlers
from teams
order by team_rank;

-- name: q7_steals
-- players who beat their draft spot by the most
select season, draft_round, pick, team, player, position_group,
       career_value, expected_value, value_over_expected, probowls
from v_picks
order by value_over_expected desc
limit 15;

-- name: q8_busts
-- top 10 picks who did the worst compared to their spot
select season, pick, team, player, position_group,
       career_value, expected_value, value_over_expected, games
from v_picks
where pick <= 10
order by value_over_expected
limit 15;

-- name: q9_colleges
-- which colleges had the most pro bowlers?
select college,
       count(*) as players,
       sum(pro_bowler) as pro_bowlers,
       round(100.0 * avg(pro_bowler), 1) as pct_pro_bowlers,
       round(avg(career_value), 1) as avg_career_value
from picks
group by college
having count(*) >= 40
order by pro_bowlers desc
limit 10;

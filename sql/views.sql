-- views.sql
-- expected value = what a player picked at that spot usually turns into
-- first get the average career value at each pick,
-- then average it with the 4 picks before and after to smooth it out
-- picks 1-4 just use their own average because value drops really fast at the top.

drop view if exists v_pick_expected;
create view v_pick_expected as
with by_pick as (
    select pick,
           count(*) as players,
           avg(career_value) as avg_value
    from picks
    group by pick
)
select pick,
       players,
       round(avg_value, 2) as avg_value,
       round(case when pick <= 4 then avg_value
                  else avg(avg_value) over (order by pick rows between 4 preceding and 4 following)
             end, 2) as expected_value
from by_pick;

-- every pick with its expected value and how much better or worse it did
drop view if exists v_picks;
create view v_picks as
select p.*,
       e.expected_value,
       round(p.career_value - e.expected_value, 2) as value_over_expected
from picks p
join v_pick_expected e on e.pick = p.pick;

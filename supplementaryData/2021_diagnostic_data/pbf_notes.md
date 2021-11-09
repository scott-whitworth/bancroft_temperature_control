6/28/2021 -> 6/29/2021 - pbf_2021_6_28_13:18:19_intermediate_status.csv - all taks set to 40C, refreshed water level, set probes with suction cups
Half water level

6/29/2021 -> 6/30/2021 - pbf_2021_6_29_13:30:36_intermediate_status.csv - All tanks set to 6C (off), goal is to meausre cool down trend for all
Half water level

6/30/2021 -> 7/1/2021  - pbf_2021_6_30_15:23:1_intermediate_status.csv  - All tanks set to 39.9C (full on), goal is to measure heating (with 9 tanks)
half water level

7/1/2021 -> 7/6/21     - pbf_2021_7_1_14:52:56_intermediate_status.csv  - All tanks set to 6C (off), goal is to reset tanks to low temp. We already have this data from the second test. All set to zero
Half water level

7/6/2021 -> 7/7/2021   - pbf_2021_7_6_14:17:59_intermediate_status.csv - ONE tank(4) set to 39.9C (full on). Goal is to measure a single tank heating up
Half water level

We might want to test 4 or 5 tanks heating at once (should be the same as one)

Water was added to all of the tanks (warm to tank 4, cold to rest) to bring level back up to half

7/7/2021 -> 7/8/2021 - pbf_2021_7_7_15:55:58_intermediate_status.csv - Five tanks set to 39.9C (full on). 2, 3, 5, 7, 8. Four tanks (1,4,6,9) set to 6.0. All five that are 'on' should be full power (and different than 6_30 test)
half water level


./peanut_butter_falcon.py all 39.9 600
./peanut_butter_falcon.py one 1 6.0 600
./peanut_butter_falcon.py one 4 6.0 600
./peanut_butter_falcon.py one 6 6.0 600
./peanut_butter_falcon.py one 9 6.6 600

7/8/2021 -> 7/9/2021 - pbf_2021_7_8_15:0:57_intermediate_status.csv  - Water change to Full, with a cool down. Data will be all over the place
Full water set

7/9/2021 -> 7/12/2021 - pbf_2021_7_9_14:39:13_intermediate_status.csv - Set one tank (5) to full (39.9). Goal is to measure single tank performance
Full Water set

7/12/2021 -> 7/13/2021 - pbf_2021_7_12_15:44:7_intermediate_status.csv - Set five tanks to high (39.9), Goal is to measure more than one, but less than full tanks 
               - Tanks 1 3 5 7 will be off, 2 4 6 8 9 will be on
Full Water set

./peanut_butter_falcon.py all 39.9 600
./peanut_butter_falcon.py one 1 6.0 600
./peanut_butter_falcon.py one 3 6.0 600
./peanut_butter_falcon.py one 5 6.0 600
./peanut_butter_falcon.py one 7 6.6 600

7/13/2021 -> 7/14/2021 - pbf_2021_7_13_11:29:21_intermediate_status.csv - Set everything to 6.0. This is after a system reset (so things might have turned on momentarily). This is just a secondary capture of cooling down, the other should be after the next test (where they are all full and max temp)
Full water set

7/14/2021 -> 7/15/2021 - pbf_2021_7_14_15:38:1_intermediate_status.csv - Set everything to full (39.9), goal is to measure all tanks heating
Full water set

7/15/2021 -> - pbf_2021_7_15_15:54:16_intermediate_status.csv - Setting everything off (6.0) to measure cool down of everything.
Full Water set

### Heat Gradient Construct ###
tank 4 -> control

Five sticks - front left, front right, back left, back right, center

Front Left - middle: 1
Front Right - top: 8, bottom: 7
back left - top: 6, bottom 5
back right - middle 3
center - top 9, middle 2

water depth: 19cm
probe spacing: wide: 28cm, depth 13cm, height 15cm


7/20/2021 -> - pbf_2021_7_20_16:9:22_intermediate_status.csv  - Running tank 4 up to 39.9, all other probes measuring gradient



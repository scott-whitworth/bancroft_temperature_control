# Bear Trap Configuration Files
These files set up the Main Control Node's start up behavior.

| Line | Purpose | Example |
|------|---------|---------|
| startDate | Real-world start date of the experiment. This is used against the system time of the Main Control Node to determine how many days to advance into the temperature files. This is how the system knows where to pick back up on a power cycle. | `startDate,2021,6,3` - The experiment started on the 3rd of June 2021 |
| startDay | Which line of the tempData files correlates with the start date of the system. Acts as an offset to align the starting date with the starting temp 'day' | `startDay,3` - The `startDate` correlates with the third line of each tempData file |
| hData / dData | Temperature profile files holding the data in half hour chunks of the target temp for any given time in the experiment | `hData,/home/<userName>/bancroft-lab-shia/tempData/historicData_6_04_21.csv` - Location of the historicData file on the system |

File format:
```
startDate,<year>,<month>,<day>
startDay,<index>
hData,<historic temp data csv>
fData,<future temp data csv>
```
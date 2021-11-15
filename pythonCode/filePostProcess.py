#!/usr/bin/env python

###################################################################
## Process all of the system level output data from bear_trap.py. 
## Because files are written in on-time chunks, this script pulls 
## all of those files together into one single, experiment long,
## status file. This also does one more level of processing to 
## convert the time ids to actual time stamps to make post 
## processing a little easier.
##
## Usage: set up appropriate files and lables below
##        run to produce one single .csv file
##
## Should be noted that this was written on a different system than
## the other scripts. Developed 11/2021 using python 3.10
##
## Scott Griffith
## Whitworth University
## in support of Bancroft Lab at Gonzaga University
## Last modified Fall 2021
###################################################################

import string

status_update_time = 300 # Pulled from bear_trap.py (this is overwritten by command 55)
                         # This determines how many 'measureID's will be in a half-hour

input_file_dir  = "./post_Data/"
input_file_list = [
    '2021_6_3_16_18_27_Main_status.csv',
    '2021_6_4_15_18_36_Main_status.csv',
    '2021_6_7_15_18_45_Main_status.csv',
    '2021_6_8_9_18_55_Main_status.csv',
    '2021_6_8_14_18_43_Main_status.csv' ,
    '2021_6_10_13_18_36_Main_status.csv',
    '2021_6_11_15_18_47_Main_status.csv',
    '2021_6_16_15_18_42_Main_status.csv',
    '2021_6_22_13_18_44_Main_status.csv',    
    '2021_6_22_14_18_38_Main_status.csv',
    '2021_6_24_15_18_47_Main_status.csv',
    '2021_6_28_11_18_39_Main_status.csv',    
    '2021_7_13_11_18_52_Main_status.csv',
]

output_file_name = "2021_6_3_56days_total_status.csv"
output_file_firstLine = "Combined File: Summer 2021 dayID,halfHourID,measureID,tIndex,tempProf,setTemp,heaterStat,measuredTemp,TimeStamp(Added),\n"



def make_time_stamp(fData):
# Convert single line to inner-day time stamp
# This is based on half-hour indexes and measureIDs
    #Parse data
    pData = fData.split(",")    

    # Find half hour index and measurement ID
    halfHour = int(pData[1])
    measID = int(pData[2])
    #print("Current halfHour: {} measID: {}".format(halfHour,measID))

    # convery to time of day
    outH = int(halfHour / 2) # Truncate off the .5 to match the Time Indexing format
    outSeconds = 0 # Starting seconds of the hour (about to be modified if :30)

    if( halfHour % 2):
        # Half hour is odd
        outSeconds = 1800 #Number of seconds in a half hour
    
    #Update outSeconds based on measID
    outSeconds = outSeconds + ( measID * status_update_time)

    #          00:00 format
    return "{:02}:{:02}".format(outH,int(outSeconds/60)) 


#Time Indexing format:
#     0       1      2      3      4     5      6      7      8      9     10     11
# 00:00 , 00:30, 01:00, 01:30, 02:00, 2:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30 

#    12     13     14     15     16     17     18     19     20     21     22     23
# 06:00, 06:30, 07:00, 07:30, 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30

#    24      25     26     27     28    29     30     31     32     33     34     35
# 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30

#    36     37     38     39     40     41     42     43     44     45     46     47
# 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, 21:00, 21:30, 22:00, 22:30, 23:00, 23:30 


##################################################################################################################################
## 'write' line from bear_trap.py                                                                                               ##
## status_output = "{},{},{},{},{},{},{},{}".format(dayID,halfHourID,measureID,tIndex,tempProf,setTemp,heaterStat,measuredTemp) ##
## Example output:                                                                                                              ##
## 16,32,0,53,TRUE,0,FALSE,22,                                                                                                  ##
##################################################################################################################################


print("\n")

print("Opening Output file {}".format(output_file_name))
try:
    outFile = open(input_file_dir + output_file_name,'w')
    outFile.write(output_file_firstLine)
except: 
    print("Error Opening output file {} | {}".format(input_file_dir,output_file_name))
    exit()

# Open up all file names in the input list
for fileName in input_file_list:

    print("Trying to process file {}".format(fileName))
    with open(input_file_dir + fileName) as curFile:

        #Make sure you are at the beginning of the file
        curFile.seek(0)
            
        #remove the first line (time stamp)
        line = curFile.readline() # Grabs the first line (should just be start times)
        
        #Grab All the lines of the file
        for newLine in curFile:

            if len(newLine) > 1:
                # not Last line?
                #Calculate new time stamp
                curTime = make_time_stamp(newLine)

                #append time stamp to end of line
                #                  VV Remove the trailing new line
                newLine = newLine[:-1] + "," + curTime + ",\n"             
                outFile.write(newLine)
            else :
                print("Last line: {}".format(newLine))

        print("File Done!")

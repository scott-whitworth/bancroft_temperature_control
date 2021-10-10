#!/usr/bin/env python

# diagnostic script to check the most recent day's data from a temperature output
# checks for anomalies in the data to quickly indicate which tanks probably need to be checked
#    checks: if any tanks are on the wrong day,
#            if there is a temperature deviance from the set that is too high or too low
#            if the average difference of any tank for the given day is too high
#
# usage: normal_tuesday.py [input file.csv]
#
# Scott Griffith
# Whitworth University
# in support of Bancroft Lab at Gonzaga University
# Last modified Summer 2021
#      updated tank mapping to match what was being used

import math
import sys
import calendar
import string
import time

###################################
## System Variables Just In Case ##
###################################

remote_names = ['yelnats','louis','witwicky','shaw','mutt','maverick',
                'jack','boyd','farber','francis','drummer']

# For 2021 summer work only 48 tanks were used
tankIndexs      = [     [ 4, 5, 6, 7, 8, 9], #RPi1 - yelnats
                        [13,14,15,16,17,18], #RPi2 - louis
                        [22,23,24,25,26,27], #RPi3 - witwicky
                        [31,32,33,34,35,36], #RPi4 - shaw
                        [40,41,42,43,44,45], #RPi5 - mutt
                        [49,50,51,52,53,54], #RPi6 - maverick
                        [58,59,60,61,62,63], #RPi7 - jack
                        [67,68,69,70,71,72], #RPi8 - boyd
                        [], #Rpi9 - farber
                        [], #RPi10- francis
                        [] ]         #RPi11- drummer
def validTank(tank):
#Check the above tankIndex list to make sure tank is an interesting tank number
	for t in range(len(tankIndexs)):
		for j in range(len(tankIndexs[t])):
			if tank == tankIndexs[t][j]:
				return True

	#No tanks in there, we can exit
	return False

numberOfTanks = 96

#Time Indexing format:
#     0       1      2      3      4     5      6      7      8      9     10     11
# 00:00 , 00:30, 01:00, 01:30, 02:00, 2:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30

#    12     13     14     15     16     17     18     19     20     21     22     23
# 06:00, 06:30, 07:00, 07:30, 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30

#    24      25     26     27     28    29     30     31     32     33     34     35
# 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30

#    36     37     38     39     40     41     42     43     44     45     46     47
# 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, 21:00, 21:30, 22:00, 22:30, 23:00, 23:30


#Function to pause execution and with for an enter press
def waitForE():
	try:
        	input("Press Enter to continue...")
	except SyntaxError:
        	pass


#Deal with opening status file
if(len(sys.argv) != 2):
	print "Arguments are weird! requires just [inputFile]"
	exit()

statusFile_name = sys.argv[1]
print "Opening status file: {}".format(statusFile_name)
try:
	sfile = open(statusFile_name,'r')
except:
	print "Error Opeing up file, exiting"
	exit()

line = sfile.readline()
if line.find('Start') != -1:
	print "Successful! This file starts at: {}".format(line[line.find(':')+1:])
	waitForE()
else:
	print "First Line of the file should be start time! Error, quitting"
	exit()

sfile.close()

lineNum = 0

curDayNum = -1

#Status Variables
tankStatuses = [''] * numberOfTanks 
curTimeStamp = [0,0,0]
tankStatusError = False
sErrorList = []

#Deviation Errors
measurementDev = [ [] for _ in range(96)] 
measurmentError = False
mErrorList = []
measurementThresh_min = -4.0
measurementThresh_max = 4.0
measurementThresh_avg = 0.3


for line in reversed(list(open(statusFile_name))):
#Open File in reverse order
	#print" Read Line : |{}|".format(line)
	lineNum = lineNum + 1

	if line.find('Start') != -1:
		print"End of File!"
		break

	# 0     1         2        3    4      5        6       7
	#day halfHour measurement tank profile setTemp heater measuredTemp
	data = string.split(line,',')
	#print "Parsed data size: {}".format(len(data))
	#if len(data) != 8:
	#print "Parsed Data: {}".format(data)
	if( data[3] == ''):
		print "Error Parsing following string: {}".format(line)
	else:
		curTank = int(data[3])

	if(int(data[0]) > curDayNum):
		#New Day Detected!, this may jump around a bunch
		curDayNum = int(data[0])
		print "Setting Current Day Index to: {}".format(curDayNum)

	###########################
	# Last Entry Status Reading
	###########################

	#           day
	if(int(data[0]) > curTimeStamp[0]):
		curTimeStamp[0] = int(data[0])
		curTimeStamp[1] = int(data[1])
		curTimeStamp[2] = int(data[2])
		print "Setting Current Time Stamp to: Day {} HalfHour {} Measurement {}".format(curTimeStamp[0],curTimeStamp[1],curTimeStamp[2])

	#Record the most recent Values
	if(tankStatuses[curTank-1] == ''):
		if(curTimeStamp[0] == int(data[0])):#day check
			if(curTimeStamp[1] == int(data[1]) ):#halfHour
				if(curTimeStamp[2] == int(data[2])): #measurementID
					 tankStatuses[curTank-1] = "Tank {}: Set: {}, Heater: {}, Measured: {}".format(curTank,data[5],data[6],float(data[7]))
				else:
					tankStatuses[curTank-1] = "Warning: Different MeasurementIDs - Tank {}: Set: {}, Heater: {}, Measured: {}".format(curTank,data[5],data[6],float(data[7]))
					tankStatusError = True
					sErrorList.append(int(curTank))
			else:
				tankStatuses[curTank-1] = "Warning: WRONG HalfHour: {}!!!   -  Tank {}: Set: {}, Heater: {}, Measured: {}".format(data[1],curTank,data[5],data[6],float(data[7]))
				tankStatusError = True
				sErrorList.append(int(curTank))
		else:
			tankStatuses[curTank-1] = "Warning: WRONG DAY: {}!!!   -  Tank {}: Set: {}, Heater: {}, Measured: {}".format(data[0],curTank,data[5],data[6],float(data[7]))
			tankStatusError = True
			sErrorList.append(int(curTank))
	
	##################################
	# Measurement Deviation Calculation
	##################################

	if( int(data[0]) == curDayNum ):
		           #Set Temp   Measured Temp
		dev = float(data[5]) - float(data[7])
		measurementDev[int(data[3])-1].append(dev)


	#This is just for debugging
	#waitForE()

print "Read {} lines of the file".format(lineNum)

print "::::::::::::::::"
print ":::::Report:::::"
print "::::::::::::::::"
print " "
print ":::::::::::::::::::::::::::::"
print ": Deviations for Day {}".format(curDayNum)
print ":::::::::::::::::::::::::::::"
for t in range(len(measurementDev)):
	if validTank(t+1):
		#We should only care to report on tanks that are valid
	
		if len(measurementDev[t]) == 0:
			print "Warning!!!!  No Data for Tank {}".format(t+1)
			measurmentError = True
		else:
			minVal = min(measurementDev[t])
			maxVal = max(measurementDev[t])
			avgVal = sum(measurementDev[t]) / len(measurementDev[t])

			print "Tank {} Max:{}, Min:{}, Avg:{} ".format(t+1,maxVal, minVal, avgVal)
			# TODO: Make the warnings much more obvious (like color)
			if(minVal < measurementThresh_min):
				print"Warning: Tank {} min value out of threshold!".format(t+1)
				measurmentError = True
				mErrorList.append(t+1)
			if(maxVal > measurementThresh_max):
				print"Warning: Tank {} max value out of threshold!".format(t+1) 
				measurmentError = True
				mErrorList.append(t+1)
			if(abs(avgVal) > measurementThresh_avg):
				print"Warning: Tank {} avg value out of threshold!".format(t+1)
				measurmentError = True
				mErrorList.append(t+1)

print " "
print ":::::::::::::::::::::::::::::::::::"
print ": Current Statuses of the Tanks:  :"
print ":::::::::::::::::::::::::::::::::::"
for i in tankStatuses:
	print i

if tankStatusError:
	print "WARNING: Error somewhere in the tank statuses! Check above to see which one"
	print " Check the following tanks {}".format(sErrorList)
if measurmentError:
	print "WARNING: Error somewhere in the measurement deviations! Check above to see which one"
	print "Check the following tanks {}".format(mErrorList)

#sfile.close()


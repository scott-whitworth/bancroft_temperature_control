#!/usr/bin/python

import smbus #Used to talk to the Arduino
import sys   #Used with comand line arguments
import math  #used with the floor functions
import time  #Used for time synching with the arduino
import calendar #Used for time managememnt on the Pi
import subprocess #Used for error checking the i2c
import string #Used for parsing csv file
import RPi.GPIO as GPIO

################################
## System Variables
###############################

#Status Update time in minutes. Every [status_update_time] minutes a status record will be taken
status_update_time = 2

#Number of retrys for a i2c command
i2c_Retry = 6
#Count of errored i2c connections. Used to check against threshold to cause system reset
ARD_error_ct = 0
ARD_error_thresh = 60 #if i2c_Retry is set to 6, each update from an fully failed arduino will cause 54 errors. 60 means more than one arduino failed
ARD_reset = False

#List of all of the i2c addresses for Arduinos
#ARD_ADDRESSES = [0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B]
#ARD_ADDRESSES = [0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17] #left side
ARD_ADDRESSES = [0x11]
#ARD_ADDRESSES = [0x14,0x18,0x19,0x1a,0x1b]

#Each arduino is connected to 9 temp sensors
ARD_TEMP_SIZE = 9

#Set Up i2c Bus
bus = smbus.SMBus(1)

#Status File default
statusFile = []


#Time Indexing format:
#     0       1      2      3      4     5      6      7      8      9     10     11
# 00:00 , 00:30, 01:00, 01:30, 02:00, 2:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30 

#    12     13     14     15     16     17     18     19     20     21     22     23
# 06:00, 06:30, 07:00, 07:30, 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30

#    24      25     26     27     28    29     30     31     32     33     34     35
# 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30

#    36     37     38     39     40     41     42     43     44     45     46     47
# 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, 21:00, 21:30, 22:00, 22:30, 23:00, 23:30 


##################################
## i2c Command Functions
##################################

#Commands
NULL      	= 0
HISTORIC 	= 1 	#From: Pi to Arduino. Historic Temperatures. [1,TimeIndex,MS_Temp,LS_Temp]
			#ex: [1,10,30,25] - Set historic entry of 30.25 for 05:00  
FUTURE 		= 2   	#From: Pi to Arduino. Future Temperatures [2,TimeIndex,MS_Temp,LS_Temp]
			#ex: [2,15,29,88] - Set Future entry of 29.88 for 07:30
REPORT 		= 3  	#From: Arduino to Pi. Status of Arduino [int(tankNumber),bool(isFuture), int(setTemp_MSB), int(setTemp_LSB), bool(heaterStatus), int(measueredTemp_MSB), int(measuredTemp_LSB)]
                  	#ex: [50,1, 28, 45, 0, 29, 88] = Tank 50, Future Temp, Set to 28.45 degrees, heater is off, read at 29.88
			#This is not really a message. Keeping in because of the formatting. SLAVE cannot really send info to the MASTER. This is triggered with a GET_STATUS send from the PI and a GET_STAUTS response from the arduino
GET_STATUS 	= 4 	#From Pi to Arduino. Force a REPORT message (no associated data)
SYNCH_TIME 	= 5  	#From Pi to Arduino. Set and Synch time (data tbd)


#function to convert float to two ints
#first int returned is the ones, tens and hundreds
#second int is the thenths and hundredths
#ex: 31.45 would be [31, 45]
#This is to over come the i2c limitation on byte sized ints.
#max temp is 255.255 min temp is 0.0
#DOES NOT SUPPORT NEGATIVE TEMPS
def cF_2i (floatingTemp):
	if floatingTemp < 0 :
		print "ERROR cF_2i: Sending Negative numbers is not supported!"
	firstInt = int(math.floor(floatingTemp))
	secondInt = int( math.floor( (floatingTemp*100)-(firstInt*100) ) )
	return [firstInt, secondInt]


#function to reset the arduinos if they hang
#Sets pin 13 to high (which clears out the arduinos)
#The power switch tail is connected to pin 14 as ground as well
def resetARD():
	print "*************************"
	print "** RESETTING ARDUINOS! **"
	print "*************************"
	GPIO.output(7,False) #set high, turns on tail
	time.sleep(10) #wait 10 seconds
	GPIO.output(7,True) #set low, turning the Arduinos back on
	time.sleep(10) #wait 10 more seconds
	global ARD_error_ct
	ARD_error_ct = 0
	global ARD_reset
	ARD_reset = True
	

def write_i2c(adr,cmd,data_to_send):
#send individual i2c message
#This handles errors that sometimes comes up in i2c communications
	loop = 0
	isSent = False
	global ARD_error_ct

#	print"Wiriting command {} {} {} ".format(adr,cmd,data_to_send)
	
	while (loop <= i2c_Retry) and not isSent:
		try:	
			if not (loop == 0 ):
				print"Re-sending data! {} {} {} ".format(adr,cmd,data_to_send)
			bus.write_i2c_block_data(adr,cmd,data_to_send)
#			print "Send to ard {} cmd {}".format(adr,cmd)
                        isSent = True
			time.sleep(0.01)
                except IOError: #if and error happens, wait and try again
			print "Error on ard {} cmd {} data: {}".format(adr,cmd,data_to_send)
                        #subprocess.call(['i2cdetect','-y','1'])
                        time.sleep(0.01)
			try:
				bus.write_i2c_block_data(adr,0,[0]) # Send empty message. Clear out message buffer
			except IOError:
				print "Error clearing buffer"
			time.sleep(0.01)
                        isSent = False
                        loop = loop + 1
			ARD_error_ct = ARD_error_ct + 1

	if(loop >= i2c_Retry):
		print "Data not sent to {} due to i2c error after {} attempts".format(adr,loop)
		if(ARD_error_ct > ARD_error_thresh):
			print "Current Error count:{}".format(ARD_error_ct)
			resetARD()





def read_i2c(adr,cmd):
#read individual i2c message
#This handles errors that sometimes comes up in i2c communications
        loop = 0
        isSent = False
	global ARD_error_ct

#	print"Reading command: {} {} ".format(adr,cmd)

        while (loop <= i2c_Retry) and not isSent:
                try:
                        if not (loop == 0 ):
                                print"Re-grabbing data! {} {}, error count: {} ARD_reset: {} ".format(adr,cmd,ARD_error_ct,ARD_reset)
			get_Data=bus.read_i2c_block_data(adr,cmd) #Read back data associated with Tank Index
			time.sleep(0.01)
#                       print "Send to ard {} cmd {}".format(adr,cmd)

			#######################
			## Only use this if you need to verify data before resending)
			testData = parse_Status_Data(get_Data)
			errCk = True
			if (testData[0] > 100) or (testData[0] < 1): errCk = False #tank number
			if (testData[2] > 40.0): errCk = False #setTemp 
			if (testData[4] > 40.0) or (testData[4] < 1.0): errCk = False #measuredTemp

			if (testData[0] >= 97) and (testData[0] <=99): errCk = True #bypass the last three tanks that are disconnected
			
			########################
			if errCk: #passed error check
				isSent = True
				return get_Data
			else:
				print"Parse Error, Tank number or Temps out of range: {}:{} {}".format(testData[0],testData[2],testData[4])
				isSent = False
				ARD_error_ct = ARD_error_ct + 1
                except IOError: #if and error happens, wait and try again
                        print "Error on recieving ard {} cmd {}".format(adr,cmd)
                        #subprocess.call(['i2cdetect','-y','1'])
                        time.sleep(0.01)
                        try:
				bus.read_i2c_block_data(adr,0) # Pull empty message. Clear out message buffer
			except IOError:
				print "Clearing buffer failed"
                        time.sleep(0.01)
                        isSent = False
                        loop = loop + 1
			ARD_error_ct = ARD_error_ct + 1

        if(loop >= i2c_Retry):
                print "Data not recieved from {} due to i2c error after {} attempts".format(adr,loop)
		if(ARD_error_ct > ARD_error_thresh):
			print "Current Error count: {}".format(ARD_error_ct)
			resetARD()


def write_i2c_block_toAll(cmd,data_to_send):
#function to send cmd and data_to_send to all arduinos
	for adr in ARD_ADDRESSES: #Loop through all arduino addresses
#		print "Sending Data to {}".format(adr)
		write_i2c(adr,cmd,data_to_send)
		time.sleep(0.01)


def send_HistoricTemp(time_index,temp):
#send float(temp) to time_index for all arduinos Historic Arrays
#See above for time_index mapping
	write_i2c_block_toAll(HISTORIC,[time_index] + cF_2i(float(temp))  )


def send_FutureTemp(time_index,temp):
#send float(temp) to time_index for all arduinos Future arrays
#See above for time_index mapping
	write_i2c_block_toAll(FUTURE,[time_index] + cF_2i(float(temp))  )

def send_TimeSynch() :
#function to send out TimeSynch message
        #cur_time = time.gmtime() #Read current system time in UTC
	cur_time = time.localtime() #Read current system time in local time
	

        #Assemble time data from current system time
        send_data = [int( math.floor( float(cur_time[0]) / 100.0))] #upper part of year (20 for 2017)
        send_data.append( int( cur_time[0] - (send_data[0]*100) ) ) #lower part of year (17 for 2017)
        send_data.append( int(cur_time[1]) ) #Month
        send_data.append( int(cur_time[2]) ) #day
        send_data.append( int(cur_time[3]) ) #hour
        send_data.append( int(cur_time[4]) ) #minute
        send_data.append( int(cur_time[5]) ) #second
	
	#Send data to all arduinos
	write_i2c_block_toAll(SYNCH_TIME,send_data)


def parse_Status_Data(i2c_data):
#Parse the raw data from i2c in to a status list as follows:
#[int(Tank Number, unique number of tank), bool(Future/Historic Flag), float(Current Set Temp), bool(Flag for if the heater is on or not, float(Most receint temperature read)] 
	if i2c_data is None:
		print"Error in parsing status data! Possibly check i2c connection!"
		return [-1,False,-1,False,-1]
	else :
	        #parse recieved data
        	tankNum = int(i2c_data[0]);
	        isFuture = bool(i2c_data[1]);
        	measuredTemp = float(i2c_data[2]) + (float(i2c_data[3])/100)
	        isHeaterOn = bool(i2c_data[4])
        	setTemp = float(i2c_data[5]) + (float(i2c_data[6])/100)
		return [tankNum,isFuture,setTemp,isHeaterOn,measuredTemp]


def update_Status():
#get the status of all of the tanks using the GET_STATUS / REPORT messages
#Needs to use the parse_Status_Data helper function to pull apart data
	curTime = time.localtime()
	global ARD_error_ct
	ARD_error_ct = 0;

	for ard in ARD_ADDRESSES : #step through all the arduinos
		for i in range(0,ARD_TEMP_SIZE): #In each arduino, check every tank index
			#print"Getting Status of {}".format(ard)
			write_i2c(ard,GET_STATUS,[i]) #Send the Tank Index first
			get_Data=read_i2c(ard,GET_STATUS) #Read back data associated with Tank Index
			
			cur_status = parse_Status_Data(get_Data) #cur_Status contains parsed data, see parse_Status_Data for more
			#Do something with this data!!!!
			#                 Y  M  D   TIME  Tank isFuture measuredTemp isHeaterOn setTemp
			status_output = "{},{},{},{}:{}:{},{},{},{},{},{}".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5],cur_status[0],cur_status[1],cur_status[2],cur_status[3],cur_status[4])
			statusFile.write(status_output)
			statusFile.write("\n")
	statusFile.flush()

	if ARD_error_ct > ARD_error_thresh:
		print "**********************************************Need to reset connection! Deteted {} errors!".format(ARD_error_ct)
		resetARD()

def calculateDayIndex(refDate,startIndex):
#calculate the correct date index based off of starting refDate and startIndex
#refDate comes from time.localtime()
#startIndex should be 1, but in the case that this needs to be re-started will be an offest
	curTime = time.localtime()

	elapsedSeconds = calendar.timegm(curTime) - calendar.timegm(refDate) #convert to EPOC time in seconds
	elapsedDays = elapsedSeconds / 86400 #Number of seconds in a day
	elapsedDays = int(math.floor(elapsedDays)) #round down

	return elapsedDays + startIndex

	
	

#################################
## Temp File Reading Functions
#################################

def readTempFile(in_file,l_index):
#Function to read and format incoming csv data format
#file is file to read from, should already be open
#l_index is what line you want to read from
	in_file.seek(0) #GO to the start of the file

	for i in range(0,l_index+1): #Iterate through the file, stepping through until you get to l_index
		line = in_file.readline()
		#print "{} !  {}".format(i,line)

	#print "l_index: {} line: {}".format(l_index,line)

	line = string.split(line,",")#parse the csv list into individual parts
	
	print "Day : {}".format(line[0])	

	tempData = []#initilize array
	for i in range(1,len(line)):#this should read in everything, skipping the first entry (which is the day)
		tempData.append(float(line[i]))
		
	print "Size of read data: {}".format(len(tempData))  

	return tempData


##########################################
## Function Testing
##########################################
## Read In Arguments
##
## This should only have to be done once
## Might need to deal with offsetting line based on current date vs. start of experiment date
##########################################

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.OUT) #Pin 13 is tied to the power switch tail to reset the arduinos
GPIO.output(7,True)
time.sleep(5)

if(len(sys.argv) >= 4):
	hData_fileName = sys.argv[1]
	fData_fileName = sys.argv[2]
	startingDay = int(sys.argv[3])
else:
	print "Not enough arguments. Using default values!"
	print "bancroft_lab_runner.py [historicFile.csv] [futureFile.csv] [startingDay]"
#	hData_fileName = "historicData_6_23_17.csv"
#	dData_fileName = "futureData_6_23_17.csv"
	hData_fileName = "historicData_7_19_17.csv"
	fData_fileName = "futureData_7_19_17.csv"
	startingDay = 1

dateRef = time.localtime()

print "Importing Historic file: {} and Future file: {}".format(hData_fileName, fData_fileName)

try:
	hData_file = open(hData_fileName,'r') #Open historic data file, defined by the first input argument
	fData_file = open(fData_fileName,'r') #Open future data file defined by the second input argument 
except: 
	print "Error Opening Files!"
	exit() #We don't want to continue if there was an issue



#Set up output file
curTime = time.localtime()
statusFile_name = "{}_{}_{}_{}:{}:{}_status.csv".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5])
statusFile = open(statusFile_name,"w")
statusFile.write("Start Time: {}/{}/{} {}:{}:{}\n".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5]))

wait_Time = 0 #initilize wait_Time
nextUpdateTime = 0 #initilize NextUpdate

## always running Loop!
while True:

	#Day change check
	if( (nextUpdateTime <= calendar.timegm(time.localtime())) or ARD_reset ): #if the current time is greater than the nextUpdateTime, do the update stuf
		ARD_reset = False
		## Each day new temp data should be read from the files and sent out to the arduinos
		day_index = calculateDayIndex(dateRef,startingDay) #figureOut the correct day index

		print "@@@@@@@@@@@@@@@@ Sending temp data for day {} ".format(day_index)
	
		hData = readTempFile(hData_file,day_index)
		fData = readTempFile(fData_file,day_index)

		print "@@@@@@@@@@@@@@@@ Historic {} and Future Data {} size of both: {} {}".format(hData[0],fData[0],len(hData), len(fData))
		for i in range(0,len(hData)) :
		#	print "Sending i: {} h: {} f: {}".format(i,first_HistoricData[i],first_FutureData[i])
			send_HistoricTemp(i,hData[i])
			send_FutureTemp(i,fData[i])

		print "@@@@@@@@@@@@@@@@ Sending Time Synch"
		send_TimeSynch() #This should happen often to keep the Arduinos locked to the same time. Over 24 hours arduinos get about 1 min off.
        		         #TimeSynch reads the Raspberry Pi's system clock which is tied to NTP which should be fairly accurate

		#recalculate next time to update
		tempTime = time.localtime()
		offset = int(tempTime[3]) * (60*60) #hour
		offset = offset + int(tempTime[4]) * 60  #min
		offset = offset + int(tempTime[5]) #second
		nextUpdateTime = calendar.timegm(tempTime) + 86401 - offset #seconds in a day (so the next day!)
		print"Next Time Update will be at {}".format(nextUpdateTime)


	#shortTerm check
	if(time.time() > wait_Time):#Wait for correct time to record status
		wait_Time = time.time() + (status_update_time*60) #Set new wait time
		#wait_Time = time.time() + 10 #fast post time
		print "Recording Status at {}".format(time.localtime())
		
		update_Status()	

	#At a certian point should probably trigger safe exit after file is done being read
	time.sleep(10) #wait 10 seconds before checking time again


print "Done"
GPIO.cleanup()

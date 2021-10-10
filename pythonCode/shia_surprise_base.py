#!/usr/bin/python

# Control Pair Node
# Interfaces between the Ethernet interface with bear_trap.py and a connected arduino
# Acts very much like a control signal passthrough
# This file needs to be modified for each Control Pair to localize which of the 11 control pairs this script is running as
# This could be automated, but as it is only needed to be set once at system set up time, then never changed, that is unnecessary
#
# Config todo:
#     set local_queue to the name of the node i.e.'yelnats_q'
#     set rmq_server to IP address of bear_trap.py main control node
#     set LOCAL_TEMP_INDEX to match this pair's tank indexes
#     set LOCAL_TEMP_DOMAIN to match pair's temperature treatment
#
# Should be started automatically from the bancroft.service 
# No arguments, receives all information from bear_trap.py via rabbitMQ messages
#
# Scott Griffith
# Whitworth University
# in support of Bancroft Lab at Gonzaga University
# Last modified Summer 2019

import smbus #Used to talk to the Arduino
import sys   #Used with comand line arguments
import math  #used with the floor functions
import time  #Used for time synching with the arduino
import calendar #Used for time management on the Pi
import subprocess #Used for error checking the i2c
import string #Used for parsing csv file
import RPi.GPIO as GPIO
import pika #rabbitmq library

time.sleep(190) # Start up sleep to give time for rabbitMQ system resources to fully load up

################################
## System Variables
###############################

local_queue = 'yelnats_q'
rmq_server = '<bear_trap IP address>'
#this should be Shia's IP address

#Status Update time in seconds. Every [status_update_time] seconds a status record will be taken
#This can be overwritten by from the main node with a MEASUREMENT_TIME command
status_update_time = 150

#Number of retries for a i2c command
i2c_Retry = 6

#Number of times system will re-submit on parsing errors (this is possibly caused by a bad read on the arduino side, not just  a i2c error
parse_error_thresh = 10

#Count of errored i2c connections. Used to check against threshold to cause system reset
ARD_error_ct = 0
ARD_error_thresh = 10 #if i2c_Retry is set to 6, each update from an fully failed arduino will cause 54 errors. 60 means more than one arduino failed
ARD_reset = False

#List of all of the i2c addresses for Arduinos
ARD_ADDRESSES = [0x11]

ARD_ADDRESS = 0x11

#Each arduino is connected to 9 temp sensors
ARD_TEMP_SIZE = 9

# One of the following lines needs to be uncomment to match the tank set this matches
LOCAL_TEMP_INDEX = [ 1, 2, 3, 4, 5, 6, 7, 8, 9] #RPi1 - yelnats
#LOCAL_TEMP_INDEX = [10,11,12,13,14,15,16,17,18] #RPi2 - louis
#LOCAL_TEMP_INDEX = [19,20,21,22,23,24,25,26,27] #RPi3 - witwicky
#LOCAL_TEMP_INDEX = [28,29,30,31,32,33,34,35,36] #RPi4 - shaw
#LOCAL_TEMP_INDEX = [37,38,39,40,41,42,43,44,45] #RPi5 - mutt
#LOCAL_TEMP_INDEX = [46,47,48,49,50,51,52,53,54] #RPi6 - maverick
#LOCAL_TEMP_INDEX = [55,56,57,58,59,60,61,62,63] #RPi7 - jack
#LOCAL_TEMP_INDEX = [64,65,66,67,68,69,70,71,72] #RPi8 - boyd
#LOCAL_TEMP_INDEX = [73,74,75,76,77,78,79,80,81] #Rpi9 - farber
#LOCAL_TEMP_INDEX = [82,83,84,85,86,87,88,89,90] #RPi10- francis
#LOCAL_TEMP_INDEX = [91,92,93,94,95,96]          #RPi11- drummer

# Treatment pairings need to be set for each tank
# TODO: This could be set by bear_trap via control signal

#####################
## 2019 Treatments ##
#####################
#1 = Future Domain, 0 = Current, -1 = Null / Off
#                      1  2  3  4  5  6  7  8  9 
LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 0, 0, 0, 1, 1, 0] #RPi1 - yelnats
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 0, 0, 1, 1, 1, 0] #RPi2 - louis
#LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 1, 1, 0, 1, 0, 0] #RPi3 - witwicky
#LOCAL_TEMP_DOMAIN = [ 0, 1, 1, 0, 0, 1, 0, 1, 1] #RPi4 - shaw
#LOCAL_TEMP_DOMAIN = [ 1, 0, 1, 1, 1, 1, 0, 1, 1] #RPi5 - mutt
#LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 1, 1, 0, 1, 1, 0] #RPi6 - maverick
#LOCAL_TEMP_DOMAIN = [ 1, 0, 0, 1, 0, 1, 1, 0, 1] #RPi7 - jack
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 0, 0, 0, 0, 0, 0] #RPi8 - boyd
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 0, 0, 0, 0, 0, 0] #Rpi9 - farber
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 0, 0, 0, 0, 0, 0] #RPi10- francis
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 0, 0, 0]          #RPi11- drummer

#####################
## 2018 Treatments ##
#####################
#Here for posterity
#1 = Future Domain, 0 = Current, -1 = Null / Off
#LOCAL_TEMP_DOMAIN = [ 1, 1, 1, 1, 0, 1, 0, 1, 0] #RPi1 - yelnats
#LOCAL_TEMP_DOMAIN = [ 1, 1, 1, 1, 0, 1, 1, 0, 0] #RPi2 - louis
#LOCAL_TEMP_DOMAIN = [ 1, 1, 0, 0, 0, 0, 1, 0, 1] #RPi3 - witwicky
#LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 0, 0, 1, 0, 0, 0] #RPi4 - shaw
#LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 1, 0, 1, 1, 1, 1] #RPi5 - mutt
#LOCAL_TEMP_DOMAIN = [ 0, 0, 0, 1, 1, 0, 1, 0, 1] #RPi6 - maverick
#LOCAL_TEMP_DOMAIN = [ 1, 0, 0, 1, 0, 0, 1, 0, 0] #RPi7 - jack
#LOCAL_TEMP_DOMAIN = [ 0, 1, 1, 0, 1, 0, 1, 0, 1] #RPi8 - boyd
#LOCAL_TEMP_DOMAIN = [ 1, 1, 0, 1, 1, 1, 1, 0, 0] #Rpi9 - farber
#LOCAL_TEMP_DOMAIN = [ 0, 0, 1, 1, 0, 0, 0, 0, 1] #RPi10- francis
#LOCAL_TEMP_DOMAIN = [ 0, 1, 1, 0, 1, 0]          #RPi11- drummer


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

#Set these to zero to start with
historic_set_temps = [0.0] * 48
future_set_temps = [0.0] *48


###########################
## i2c Command Functions
###########################

#Commands
NULL      	= 0
SET_TEMP 	= 11	#Communicate from Pi to Arduino, to set a temp for a tank. [11,Tank_Index,MS_Temp,LS_Temp]
READ_TEMP	= 12 	#Communicate from Pi to Arduino, prepare for update, set tank to be read by CUR_TEMP
CUR_TEMP	= 13	#Communicate from Arduino to Pi, Pull information from Arduino to the pi. Index of interest set by Read_Temp [int(tankNumber), bool(isFuture), int(setTemp_MSB), int(setTemp_LSB), bool(heaterStatus), int(measuredTemp_MSB), int(measuredTemp_LSB)]
SET_INDEX	= 14	#Communicate from Pi to Arduino, set the local index to a global index with future/historic setting



#############################
## RMQ Communication Scheme
#############################

NO_MESSAGE              = 0
DAY_TEMP_PROFILE        = 51    #Message sending a single day's worth of temperature data
                                # [51,int(tempProfile), int(dayIndex), float(temp_0), float(temp_1), ... up to ,float(temp_48) ]
                                # 48 floating point entries, must be positive, and only needs 4 digits (XX.XX)
                                # tempProfile 0 = current, 1 = future, -1 = off
                                # dayIndex = offset from first day being 0

SET_DAY                 = 52    # Message to get all nodes synced to the correct day offset. Primarily used for recording
                                # Can be checked against DAY_TEMP_PROFILE for sanity
                                # [52,int(dayIndex)

GET_TEMP                = 53    # Message requesting data from remote system, should be followed up with a GET_TEMP_DATA
                                # [53,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex)]
                                # tankIndex = Global Tank Index, checked locally for the correct tank
                                # dayIndex  = Given day of trial run, day 0 = first day started
                                # halfHourIndex = index of half hour seperation of the day. See documentation
                                # measurementIndex = This is based on how often we are taking measurements, this will be the count within a given halfhour

GET_TEMP_CHUNK          = 56    # Message to push a full half hour of data back from the nodes
                                # [56,int(tankIndex),int(dayIndex),int(halfHourIndex)]
                                # This could take the place of multiple GET_TEMP commands, just request a full set of half hour data
                                # Node is responsable for knowing how many GET_TEMP_DATAs to send back
                                # see above for variable documentation

GET_TEMP_DATA           = 54    # Message in response to a GET_TEMP request
                                # [54,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex),int(tempProfile),float(setTemp),bool(heaterStatus),float(measuredTemp)]
                                # Most fields are shared, see GET_TEMP
                                # tempProfile =  0=current, 1=future, -1=off
                                # setTemp = What temperature the tank thinks it is trying to get to, this is read from the arduino, not the PI
                                # heaterStatus = 1 = Heater is on, 0 = Heater is off
                                # measuredTemp = Read temperature of the tank

MEASUREMENT_RATE        = 55    # Message to set how often the RPis will take measurements
                                # [55, int(secondsPerPeriod)]
                                # 5 minutes = 300 seconds, 2 mins = 120 seconds, 10 mins = 600 seconds



#function to convert float to two ints
#first int returned is the ones, tens and hundreds
#second int is the tenths and hundredths
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

#Function to calculate time index (see table above)
def calculateTimeSlot(cur_time):
	slot = int(cur_time[3])*2

	if(cur_time[4] >= 30):
		slot = slot + 1

	return slot

#################################
## i2c Communication Functions
#################################

#function to reset the arduinos if they hang
#Sets pin 13 to high (which clears out the arduinos)
#The power switch tail is connected to pin 14 as ground as well
def resetARD():
	print "*****************************"
	print "** WE CAN'T RESET ARDUINO! **"
	print "*****************************"

	exit()

def write_i2c(adr,cmd,data_to_send):
#send individual i2c message
#This handles errors that sometimes comes up in i2c communications
	loop = 0
	isSent = False
	global ARD_error_ct

	#print"Writing command {} {} {} ".format(adr,cmd,data_to_send)

	while (loop <= i2c_Retry) and not isSent:
		try:
			if not (loop == 0 ):
				print"Re-sending data! {} {} {} ".format(adr,cmd,data_to_send)
			bus.write_i2c_block_data(adr,cmd,data_to_send)
			#print "Send to ard {} cmd {}".format(adr,cmd)
                        isSent = True
			time.sleep(0.1) 
                except IOError: #if and error happens, wait and try again
			print "Error on ard {} cmd {} data: {}".format(adr,cmd,data_to_send)
                        #subprocess.call(['i2cdetect','-y','1'])
                        time.sleep(0.1)
			try:
				bus.write_i2c_block_data(adr,0,[0]) # Send empty message. Clear out message buffer
			except IOError:
				print "Error clearing buffer"
			time.sleep(0.1)
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
	parse_error = 0
	global parse_error_thresh
	global ARD_error_ct

	#print"Reading command: {} {} ".format(adr,cmd)

        while (loop <= i2c_Retry) and ( parse_error_thresh >= parse_error  ) and not isSent:
                try:
                        if not (loop == 0 ):
                                print"Re-grabbing data! {} {}, error count: {} ARD_reset: {} ".format(adr,cmd,ARD_error_ct,ARD_reset)
			get_Data=bus.read_i2c_block_data(adr,cmd) #Read back data associated with Tank Index
			#time.sleep(0.01)
			time.sleep(0.1)
                        #print "Send to ard {} cmd {}".format(adr,cmd)

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
				parse_error = parse_error + 1
                except IOError: #if and error happens, wait and try again
                        print "Error on receiving ard {} cmd {}".format(adr,cmd)
                        #subprocess.call(['i2cdetect','-y','1'])
                        time.sleep(0.1)
                        try:
				bus.read_i2c_block_data(adr,0) # Pull empty message. Clear out message buffer
			except IOError:
				print "Clearing buffer failed"
                        time.sleep(0.1)
                        isSent = False
                        loop = loop + 1
			ARD_error_ct = ARD_error_ct + 1

	if(parse_error >= parse_error_thresh):
		print"************Error reading/parsing data. Data probably corrupted. Sending back any way"
		return get_Data

        if(loop >= i2c_Retry):
                print "**********Data not received from {} due to i2c error after {} attempts".format(adr,loop)
		if(ARD_error_ct > ARD_error_thresh):
			print "Current Error count: {}".format(ARD_error_ct)
			resetARD()


def write_i2c_block_toAll(cmd,data_to_send):
#function to send cmd and data_to_send to all arduinos
	for adr in ARD_ADDRESSES: #Loop through all arduino addresses
		#print "Sending Data to {}".format(adr)
		write_i2c(adr,cmd,data_to_send)
		time.sleep(0.1)


###########################
## Temperature Parsing
###########################

def load_in_Temps(message):
#Function to translate/parse temperature message data
#Message is already pulled apart into a list

	global historic_set_temps
	global future_set_temps
	tempProfile = int(message[1])
	print "Loading Data for temp profile: {}...".format(tempProfile)

	newTemp = []

	for num in message[3:]:
	#0 - message number, 1 - temp profile, 2 - day index, 3 - start of temperatures
		if num is not '':
			#print"Loading in temp: {}".format(float(num))
			newTemp.append(float(num))
			#print"NewTemp: {}".format(newTemp)

	if tempProfile == 1:
		print "Loaded in {} future temperature points: {} {}...".format(len(newTemp),newTemp[0],newTemp[1])
		future_set_temps = newTemp;
	else:
		print "Loaded in {} historic temperature points {} {}...".format(len(newTemp),newTemp[0],newTemp[1])
		historic_set_temps = newTemp


###################
## Update Parsing
###################

def parse_Status_Data(i2c_data):
#Parse the raw data from i2c in to a status list as follows:
#[int(Tank Number, unique number of tank), bool(Future/Historic Flag), float(Current Set Temp), bool(Flag for if the heater is on or not, float(Most recent temperature read)] 
	if i2c_data is None:
		print"Error in parsing status data! Possibly check i2c connection!"
		return [-1,False,-1,False,-1]
	else :
	        #parse received data
        	tankNum = int(i2c_data[0]);
	        isFuture = bool(i2c_data[1]);
        	measuredTemp = float(i2c_data[2]) + (float(i2c_data[3])/100)
	        isHeaterOn = bool(i2c_data[4])
        	setTemp = float(i2c_data[5]) + (float(i2c_data[6])/100)
		return [tankNum,isFuture,setTemp,isHeaterOn,measuredTemp]


def update_Status(measurementIndex):
#get the status of all of the tanks using the GET_STATUS / REPORT messages
#Needs to use the parse_Status_Data helper function to pull apart data
	curTime = time.localtime()
	curHIndex = calculateTimeSlot(curTime)
	global ARD_error_ct
	ARD_error_ct = 0;

	for i in range(0,ARD_TEMP_SIZE): #In each arduino, check every tank index
		print"Getting Status from arduino {}".format(i)
		write_i2c(ARD_ADDRESS,READ_TEMP,[i]) #Send the Tank Index first
		#time.sleep(0.1)
		get_Data=read_i2c(ARD_ADDRESS,CUR_TEMP) #Read back data associated with Tank Index
		#time.sleep(0.1)

		cur_status = parse_Status_Data(get_Data) #cur_Status contains parsed data, see parse_Status_Data for more
		#Do something with this data!!!!
		#                 Y  M  D   TIME  Tank isFuture measuredTemp isHeaterOn setTemp
		status_output = "{},{},{},{}:{}:{},{},{},{},{},{}".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5],cur_status[0],cur_status[1],cur_status[2],cur_status[3],cur_status[4])
		statusFile.write(status_output)
		statusFile.write("\n")

		#Format Message to main node
		#cur_status = [tankNum,isFuture,setTemp,isHeaterOn,measuredTemp]
		#GET_TEMP_DATA format =  [54,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex),int(tempProfile),float(setTemp),bool(heaterStatus),float(measuredTemp)]
		message = '-'+str( GET_TEMP_DATA )+ 	\
			  '-'+str( cur_status[0] )+ 	\
			  '-'+str( day_index )+ 	\
		          '-'+str( curHIndex )+		\
			  '-'+str( measurementIndex )+	\
			  '-'+str( cur_status[1] )+	\
	                  '-'+str( cur_status[2] )+	\
			  '-'+str( cur_status[3] )+	\
		          '-'+str( cur_status[4] )+'-'
		#Send it!
                channel_s.basic_publish(exchange='stom_transmit',routing_key=local_queue,body=message)
                print " [s] Sending Message to main node {}".format(message)

	statusFile.flush()


#Function to send updated temps to all of the tanks in the arduino
#Needs timeIndex that is outlined above for half hour incraments
def updateTemps(timeIndex):
	if timeIndex > 48:
		print "!!!Error in the time index for updateTemps!!!!"

	print "Updating Temps for Time index {}".format(timeIndex)

	for i in range(0,ARD_TEMP_SIZE):
		t = 0
		## Figure out what temp to set this tank to
		if LOCAL_TEMP_DOMAIN[i] == 0:
		#Historic
			t = historic_set_temps[timeIndex]
		if LOCAL_TEMP_DOMAIN[i] == 1:
		#Future
			t = future_set_temps[timeIndex] 

		print "Sending temp to {} : {}".format(int(i),t)
		#Parse out Temps
		t_MSB = int(math.floor(t))
		t_LSB = int( (t - t_MSB)*100) 

		write_i2c(ARD_ADDRESS,SET_TEMP,[i,t_MSB,t_LSB])

def init_tanks():
#Function to initialize the global tank indexes and the future/historic settings on the arduino
#This should only have an impact on the reporting
	for i in range(0,ARD_TEMP_SIZE):
		write_i2c(ARD_ADDRESS,SET_INDEX,[int(i),int(LOCAL_TEMP_INDEX[i]),int(LOCAL_TEMP_DOMAIN[i]) ]) 

#TODO: We should do this every half hour update.

##########################
## Main Program Section
#########################
print "Starting up a Shia Suprise!!"
print "testing mode"

print "Setting up RabbitMQ connections"
#TODO: We need to make it so we can recover from a network disconnect. A single bad network call breaks the RMQ system
#set up connection to server
userPass = pika.PlainCredentials('<MQ Password>','<MQ Password>')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rmq_server,credentials=userPass))
channel_m = connection.channel() #Channel for master to slave queues
channel_s = connection.channel() #Channel for slave to master queues

#attach to exchange for mtos_transmit/stom_transmit
channel_m.exchange_declare(exchange='mtos_transmit',exchange_type='direct')
channel_s.exchange_declare(exchange='stom_transmit', exchange_type='direct')

#Declare queues (make sure these match those in the main program)
channel_s.queue_declare(queue=local_queue)
channel_m.queue_declare(queue='m_'+local_queue)

#Starting Date/Time
dateRef = time.localtime()

#Set up output file
curTime = time.localtime()
statusFile_name = "/home/<user>/bancroft-lab-shia/outputData/{}_{}_{}_{}:{}:{}_intermediate_status.csv".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5])
statusFile = open(statusFile_name,"w")
statusFile.write("Start Time: {}/{}/{} {}:{}:{}\n".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5]))

#Initialize Tank Indexes
print "Initializing tank Indexes..."
init_tanks()

wait_Time = 0 #initialize wait_Time
nextHalfHour = 0 #Initialize when to send half hour temp settings
nextUpdateTime = 0 #initialize NextUpdate

#Int to keep track of which time index is being measured. This is a reference to the previous half hour mark
measurementIndex = 0

day_index = 0
tempRESET = False

## always running Loop!
while True:

	##########################################################
	## Every Half Hour Update Tank Set Temps On the Arduinos
	##########################################################
	if( (nextHalfHour <= calendar.timegm(time.localtime()) )) or tempRESET:
		tempRESET = False
		#Send new Temps for this half hour
		tempTime = time.localtime()

		print "%%%%% Sending Half Hour Temps for {}".format(time.localtime())	
		timeIndex = calculateTimeSlot(tempTime)
		updateTemps(timeIndex)

		#Calculate next time to update
		offset = 0
		if(tempTime[4] >= 30):
		#30 - 59 minutes
		#             minutes
			offset = (int(tempTime[4])*60) - (30*60) #Subtract 30 minutes to keep the time at the halfhour 
		else:
		#00 - 29 minutes
			offset = int(tempTime[4]*60) #Minutes

		offset = offset + int(tempTime[5]) #Seconds
		nextHalfHour = calendar.timegm(tempTime) + 1800 - offset #(currentTime - time to previous half hour)+time to next half hour
		wait_Time = 0 #This forces a temp reading at the half hour mark
		measurementIndex = 0

	#############################################
	## Every Wait_time Update Status of Each Tank
	#############################################
        if(time.time() > wait_Time):#Wait for correct time to record status
                wait_Time = time.time() + status_update_time #Set new wait time
                print "Recording Status at {}".format(time.localtime())

                update_Status(measurementIndex)
		measurementIndex = measurementIndex + 1


        #Check the master queue for incoming information
        frame,header,response = channel_m.basic_get(queue='m_'+local_queue,no_ack=True)
        if frame:
		message = string.split(response,'-')
                del message[0] #First entry is an empty chunk of data, discard

                if( int(message[0]) == GET_TEMP_DATA):
                	print "GET_TEMP_DATA Received! That is weird, that should only come from nodes"

		elif (int(message[0]) == SET_DAY) :
			print "SET_DAY Received! Setting day to {}".format(message[1])
			day_index = int(message[1])

		elif ( int(message[0]) == MEASUREMENT_RATE):
			print "MEASUREMENT_RATE Received! Setting rate to {}".format(message[1])
			status_update_time = int(message[1])

		elif (int(message[0]) == DAY_TEMP_PROFILE):
			print "DAY_TEMP_PROFILE Received! For temp profile {} Day {}".format(message[1],message[2])
			load_in_Temps(message)
			tempRESET = True

		elif (int(message[0]) == GET_TEMP_CHUNK):
			print "GET_TEMP_CHUNK Received! Not yet implimented!"
		elif (int(message[0]) == GET_TEMP):
			print "GET_TEMP Received! Not yet implimented"

                else :
			print "ERROR: Don't know how to parse: |{}|".format(response)
			print "Message: {}".format(message)


	#At a certian point should probably trigger safe exit after file is done being read
	time.sleep(0.25) #wait 10 seconds before checking time again


print "Done"
GPIO.cleanup()

#!/usr/bin/env python
import pika
import sys
import time
import calendar
import math
import string

# Main Control Node
# Controls everything about the larger system:
#     * sets up the RabbitMQ servers
#     * reads and parses historic and future temperature data
#     * updates Control Pair's with new data each day
#     * records coallated temperature data for the whole system
#
# Should be started automatically from the bancroft_bear.service 
# preferred usage:   bear_trap.py [startup config.csv]
# depreciated usage: bear_trap.py [historic data.csv] [future data.csv] [starting day offset]
# See ./configs/readme_configs.md for more documentation
#
# Scott Griffith
# Whitworth University
# in support of Bancroft Lab at Gonzaga University
# Last modified Summer 2019

###################
# RabbitMQ Control:
# sudo rabbitmq-server - starts server up, should only need to be run once at start up
# sudo rabbitmqctl list_queues - shows status of currently running queues
###################

################################################################
# Assumes temperature data is in /bancroft-lab-shia/tempData   #
# Assumes output data will be put in /bancroft-lab-shia/output #
################################################################

########################
## System Variables    #
########################

remote_names = ['yelnats','louis','witwicky','shaw','mutt','maverick',
		'jack','boyd','farber','francis','drummer']

tankIndexs 	= [ 	[ 1, 2, 3, 4, 5, 6, 7, 8, 9], #RPi1 - yelnats
			[10,11,12,13,14,15,16,17,18], #RPi2 - louis
			[19,20,21,22,23,24,25,26,27], #RPi3 - witwicky
			[28,29,30,31,32,33,34,35,36], #RPi4 - shaw
			[37,38,39,40,41,42,43,44,45], #RPi5 - mutt
			[46,47,48,49,50,51,52,53,54], #RPi6 - maverick
			[55,56,57,58,59,60,61,62,63], #RPi7 - jack
			[64,65,66,67,68,69,70,71,72], #RPi8 - boyd
			[73,74,75,76,77,78,79,80,81], #Rpi9 - farber
			[82,83,84,85,86,87,88,89,90], #RPi10- francis
			[91,92,93,94,95,96] ]         #RPi11- drummer

# This needs to be configured at the start of every experiment
#0 = historic  1 = future
tempProfiles	= [	[ 1, 1, 1, 1, 0, 1, 0, 1, 0], #RPi1 - yelnats
			[ 1, 1, 1, 1, 0, 1, 1, 0, 0], #RPi2 - louis
			[ 1, 1, 0, 0, 0, 0, 1, 0, 1], #RPi3 - witwicky
			[ 0, 0, 1, 0, 0, 1, 0, 0, 0], #RPi4 - shaw
			[ 0, 0, 1, 1, 0, 1, 1, 1, 1], #RPi5 - mutt
			[ 0, 0, 0, 1, 1, 0, 1, 0, 1], #RPi6 - maverick
			[ 1, 0, 0, 1, 0, 0, 1, 0, 0], #RPi7 - jack
			[ 0, 1, 1, 0, 1, 0, 1, 0, 1], #RPi8 - boyd
			[ 1, 1, 0, 1, 1, 1, 1, 0, 0], #Rpi9 - farber
			[ 0, 0, 1, 1, 0, 0, 0, 0, 1], #RPi10- francis
			[ 0, 1, 1, 0, 1, 0] ]	      #RPi11- drummer

loggingFile = []

#How many seconds bewteen updates
#This should be passed to the nodes
statusUpdateTime = 300 #5 minutes
#statusUpdateTime = 10 #for testing

#Time Indexing format:
#     0       1      2      3      4     5      6      7      8      9     10     11
# 00:00 , 00:30, 01:00, 01:30, 02:00, 2:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30

#    12     13     14     15     16     17     18     19     20     21     22     23
# 06:00, 06:30, 07:00, 07:30, 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30

#    24      25     26     27     28    29     30     31     32     33     34     35
# 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30

#    36     37     38     39     40     41     42     43     44     45     46     47
# 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, 21:00, 21:30, 22:00, 22:30, 23:00, 23:30

#########################
##Communication Scheme  #
#########################

NO_MESSAGE 		= 0
DAY_TEMP_PROFILE 	= 51	#Message sending a single day's worth of temperature data
			     	# [51,int(tempProfile), int(dayIndex), float(temp_0), float(temp_1), ... up to ,float(temp_48) ]
			     	# 48 floating point entries, must be positive, and only needs 4 digits (XX.XX)
			     	# tempProfile 0 = current, 1 = future, -1 = off
			     	# dayIndex = offset from first day being 0

SET_DAY			= 52 	# Message to get all nodes synced to the correct day offset. Primarily used for recording
			     	# Can be checked against DAY_TEMP_PROFILE for sanity
			     	# [52,int(dayIndex)

GET_TEMP		= 53 	# Message requesting data from remote system, should be followed up with a GET_TEMP_DATA
			     	# [53,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex)]
				# tankIndex = Global Tank Index, checked locally for the correct tank
				# dayIndex  = Given day of trial run, day 0 = first day started
				# halfHourIndex = index of half hour seperation of the day. See documentation
				# measurementIndex = This is based on how often we are taking measurements, this will be the count within a given halfhour 

GET_TEMP_CHUNK		= 56	# Message to push a full half hour of data back from the nodes
				# [56,int(tankIndex),int(dayIndex),int(halfHourIndex)]
				# This could take the place of multiple GET_TEMP commands, just request a full set of half hour data
				# Node is responsable for knowing how many GET_TEMP_DATAs to send back
				# see above for variable documentation

GET_TEMP_DATA		= 54 	# Message in response to a GET_TEMP request
			     	# [54,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex),int(tempProfile),float(setTemp),bool(heaterStatus),float(measuredTemp)]
				# Most fields are shared, see GET_TEMP
				# tempProfile =  0=current, 1=future, -1=off
				# setTemp = What temperature the tank thinks it is trying to get to, this is read from the arduino, not the PI
				# heaterStatus = 1 = Heater is on, 0 = Heater is off
				# measuredTemp = Read temperature of the tank

MEASUREMENT_RATE	= 55	# Message to set how often the RPis will take measurements
				# [55, int(secondsPerPeriod)]
				# 5 minutes = 300 seconds, 2 mins = 120 seconds, 10 mins = 600 seconds

#TIME_SYNC		= 59 	# Might not need this. Message to send time from main node to remote nodes
			     	# RabbitMQ is not real time, so there will be delay that makes this irrelevant
			     	# [52, ... idk, not going to use


##################################
## Function Declarations         #
##################################

def send_HistoricTemp(day_index,temp):
#send float(temp) to time_index for all arduinos Historic Arrays
#See above for time_index mapping
	#Form the start of the message
	#                  51                   historic        day_index
	msg = '-' + str(DAY_TEMP_PROFILE) + '-' + '0' + '-' + str(day_index) + '-'

	#Make an entry for each of the numbers for the day
	for num in temp:
		msg = msg + str(num) + '-'

	send_to_all(msg)


def send_FutureTemp(day_index,temp):
#send float(temp) to time_index for all arduinos Future arrays
#See above for time_index mapping
        #Form the start of the message
        #                  51                   future        day_index
        msg = '-' + str(DAY_TEMP_PROFILE) + '-' + '1' + '-' + str(day_index) + '-'

        #Make an entry for each of the numbers for the day
        for num in temp:
                msg = msg + str(num) + '-'

        send_to_all(msg)

def send_DayIndex(day_index):
#Send int(dayIndex) to all of the nodes
#This is useful to sync up all the nodes to the same day
	msg = '-' + str(SET_DAY) + '-' + str(day_index) + '-'
	send_to_all(msg)

def send_UpdateTime(uTime):
#Send int(uTime) to all nodes
#Useful just to set this in one point and keep going
	msg = '-' + str(MEASUREMENT_RATE) + '-' + str(uTime) + '-'
	send_to_all(msg)

def record_Update_Data(tData):
#Function to parse the message from a temp update
#This message should already be in list form (pre-parsed)
# [54,int(tankIndex),int(dayIndex),int(halfHourIndex),int(measurementIndex),int(tempProfile),float(setTemp),bool(heaterStatus),float(measuredTemp)]
#  0         1               2              3                   4                  5                6              7                   8
	#Parse the data
	tIndex = tData[1]
	dayID = tData[2]
	halfHourID = tData[3]
	measureID = tData[4]
	tempProf = tData[5]
	setTemp = tData[6]
	heaterStat = tData[7]
	measuredTemp = tData[8]
	
	#Do something with this data!!!!
	status_output = "{},{},{},{},{},{},{},{}".format(dayID,halfHourID,measureID,tIndex,tempProf,setTemp,heaterStat,measuredTemp)
	#print "Writing this to file: |{}|".format(status_output)        
	statusFile.write(status_output)
        statusFile.write("\n")
        statusFile.flush()


def calculateDayIndex(refDate,startIndex):
#calculate the correct day index based off of starting refDate and startIndex
#refDate is the starting day of the experiment (either from the config, or from start of running)
#startIndex should be 1, but in the case that this needs to be re-started will be an offest
        curTime = time.localtime()

	#We need to 'floor' the days first, then calculate the difference
	refDate_floor = time.mktime([ refDate.tm_year,
				      refDate.tm_mon,
				      refDate.tm_mday,
				      0, 		#Sets the time (hours, minutes, seconds) to zero
				      0, 
				      0,
				      refDate.tm_wday,
				      refDate.tm_yday,
				      refDate.tm_isdst])


        curTime_floor = time.mktime([curTime.tm_year,
                                     curTime.tm_mon,
                                     curTime.tm_mday,
                                     0,
                                     0, 
                                     0, 
                                     curTime.tm_wday,
                                     curTime.tm_yday,
                                     curTime.tm_isdst])

	#convert epoch seconds to difference of days
	elapsedDays = float(curTime_floor - refDate_floor) / 86400.0
	elapsedDays = int(round(elapsedDays,3)) #This should not be necessary, but DST might become an issue and cause non-complete days

	if( (elapsedDays + startIndex) < 1 ): #Index catch
		print "Error! Cannot have a zero or negative day! Current elapsedDay is: {} and startIndex is: {}".format(elapsedDays,startIndex)
		exit()

        return elapsedDays + startIndex


def readTempFile(in_file,l_index):
#Function to read and format incoming csv data format
#file is file to read from, should already be open
#l_index is what line you want to read from
        in_file.seek(0) #GO to the start of the file

        for i in range(0,l_index+1): #Iterate through the file, stepping through until you get to l_index
                line = in_file.readline()
                #print "{} !  {}".format(i,line)

        print "l_index: {} line: {}".format(l_index,line)

        line = string.split(line,",")#parse the csv list into individual parts

        print "Day : {}".format(line[0])

        tempData = []#initialize array
        for i in range(1,len(line)):#this should read in everything, skipping the first entry (which is the day)
                tempData.append(float(line[i]))

        print "Size of read data: {}".format(len(tempData))

        return tempData

def readConfigFile(c_file_name):
#function to load in information from configuration file
#c_file_name is the file to read from, function will open file
	try:
		c_file = open(c_file_name,'r')
	except:
		print "Error opening configuration file"
		exit()

	c_file.seek(0)

	line = c_file.readline() #should be |startDate,[year],[month],[day]|
	parse = string.split(line,",") #Pull apart the line
	if (parse[0] != "startDate") :
		print "Error loading config file! Found {} was expecting startDate".format(parse[0])
		exit()
	else : 
		timeStruct = []
		timeStruct.append(int(parse[1])) #Year
		timeStruct.append(int(parse[2])) #Month
		timeStruct.append(int(parse[3])) #Day
	
	line = c_file.readline() #|startDay,[day]|
	parse = string.split(line,",") #pull apart the line
	if(parse[0] != "startDay"):
		print "Error Loading config file! Found {} was expecting startDay".format(parse[0])
		exit()
	else :
		startDay = int(parse[1])

	line = c_file.readline() #|hData,[file]|
        parse = string.split(line,",") #pull apart the line
        if(parse[0] != "hData"):
                print "Error Loading config file! Found {} was expecting hData".format(parse[0])
                exit()
        else :
                hData_file = parse[1].strip()

	line = c_file.readline() #|fdata,[file]|
        parse = string.split(line,",") #pull apart the line
        if(parse[0] != "fData"):
                print "Error Loading config file! Found {} was expecting fData".format(parse[0])
                exit()
        else :
                fData_file = parse[1].strip()

	c_file.close()

	return [timeStruct, startDay,hData_file,fData_file]


################################
## Communication initializations
#################################

#Initialize Connections
print "Setting Up RMQ Connection..."
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel_m = connection.channel() #Channel for Master to Slave messages
channel_s = connection.channel() #Channel for Slave to Master messages

print "Declaring mtos_transmit/stom_transit"
channel_m.exchange_declare(exchange='mtos_transmit', exchange_type='direct')
channel_s.exchange_declare(exchange='stom_transmit', exchange_type='direct')

#Iterate over all names, set up a master to slave queue, bind it, and a slave to master queue and bind it
for n in remote_names:
	print "Setting Up RMQ Queue for {}".format(n)
	#First master to slave queues and binds
	channel_m.queue_declare(queue='m_'+n+'_q')
	channel_m.queue_bind(queue='m_'+n+'_q',exchange='mtos_transmit',routing_key='m_'+n+'_q')
	#Then slave to master queues and binds
	channel_s.queue_declare(queue=n+'_q')
	channel_s.queue_bind(queue=n+'_q',exchange='stom_transmit', routing_key=n+'_q')


#Function that sends message to all attached nodes via their m_ queues
#Uses list of names from remote_names for queue names
def send_to_all(message):
	print "Sending this to all of them: |{}|".format(message)
	for n in remote_names:
		channel_m.basic_publish(exchange='mtos_transmit',routing_key='m_'+n+'_q',body=message)





##########################################
## Main Program Block                    #
##########################################
## Read In Arguments
##
## This should only have to be done once
##########################################

print "\n"
if(len(sys.argv) >= 4):
	#This method is a little outdated. Should use config file
        hData_fileName = sys.argv[1]
        fData_fileName = sys.argv[2]
        startingDay = int(sys.argv[3])
	dateRef = time.localtime() #assumes that the experiment started on day this program started running
				   #This is approached different via the configuration file, where the dateRef is set by the configuration
	if startingDay <= 0:
		startingDay = 1  #This has to do with indexing in the temperature files, line zero is the header info, day one starts on line 1

elif(len(sys.argv) == 2):
	runConfigFile = sys.argv[1]
	print "Opening Configuration File: {}".format(runConfigFile)
	[startingDate,startingDay,hData_fileName,fData_fileName] = readConfigFile(runConfigFile)
	print "Starting with a date of {}/{}/{}, with day {}".format(startingDate[0],startingDate[1], startingDate[2],startingDay)
	print "hData: {}	fData: {}".format(hData_fileName,fData_fileName)
	dateRef = time.struct_time([startingDate[0], #year
                                     startingDate[1], #Month
                                     startingDate[2], #day
                                     0,
                                     0,
                                     0,
                                     0,
                                     0,
                                     -1]) #We don't specify if DST is in effect. If set to 0 or 1 might cause a rounding error in calculating the day offset

else:
        print "Not enough arguments. Using default values!"
        print "bancroft_lab_runner.py [historicFile.csv] [futureFile.csv] [startingDay]"
	    hData_fileName = "../tempData/historicData.csv" # These might not exist! 
        fData_fileName = "../tempData/futureData.csv"
        startingDay = 1
	print "starting day: {}	hData file: {}	fData file: {}".format(startingDay,hData_fileName, fData_fileName)
	dateRef = time.localtime() #See comments above about setting dateRef
	exit()

#Read in Temp Files
print "\nImporting Historic file: {} and Future file: {}".format(hData_fileName, fData_fileName)
try:
        hData_file = open(hData_fileName,'r') #Open historic data file, defined by the first input argument
        fData_file = open(fData_fileName,'r') #Open future data file defined by the second input argument
except:
        print "Error Opening Files!"
        exit() #We don't want to continue if there was an issue

#Set up output file
curTime = time.localtime()
print "\nProgram Starting Time: {}/{}/{} {}:{}:{} ".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5])
statusFile_name = "/home/<user>/bancroft-lab-shia/outputData/{}_{}_{}_{}:{}:{}_Main_status.csv".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5])
statusFile = open(statusFile_name,"w")
statusFile.write("Start Time: {}/{}/{} {}:{}:{}\n".format(curTime[0],curTime[1],curTime[2],curTime[3],curTime[4],curTime[5]))



wait_Time = 0 #initialize wait_Time
nextUpdateTime = 0 #initialize NextUpdate
nextDayTime = 0 #initialize NextDay

baseNumber = 0

print "Done intitializing, Going into main loop.\n"
while True:

	#Day change check
        if( nextDayTime <= calendar.timegm(time.localtime() ) ) : #if the current time is greater than the nextUpdateTime, do the update stuff
              
                ## Each day new temp data should be read from the files and sent out to the arduinos
                day_index = calculateDayIndex(dateRef,startingDay) #figureOut the correct day index
		send_DayIndex(day_index) #Make sure nodes get the day update
		send_UpdateTime(statusUpdateTime)

                print "@@@@@@@@@@@@@@@@ Sending temp data for day {} ".format(day_index)
                hData = readTempFile(hData_file,day_index)
                fData = readTempFile(fData_file,day_index)
		
		print "@@@@@@@@@@@@@@@@ Historic {} and Future Data {} size of both: {} {}".format(hData[0],fData[0],len(hData), len(fData))
		send_HistoricTemp(day_index,hData)
		send_FutureTemp(day_index,fData)

               # print "@@@@@@@@@@@@@@@@ Sending Time Synch"
               # send_TimeSynch() #This should happen often to keep the Arduinos locked to the same time. Over 24 hours arduinos get about 1 min off.
                                 #TimeSynch reads the Raspberry Pi's system clock which is tied to NTP which should be fairly accurate

                #recalculate next time to update
                tempTime = time.localtime()
                offset = int(tempTime[3]) * (60*60) #hour
                offset = offset + int(tempTime[4]) * 60  #min
                offset = offset + int(tempTime[5]) #second
                nextDayTime = calendar.timegm(tempTime) + 86401 - offset #seconds in a day (so the next day!)
                print"Next Time Update will be at {}".format(nextDayTime)



	#Check each of the node for messages in response
	for n in remote_names:
		frame,header,response = channel_s.basic_get(queue=n+'_q',no_ack=True)
		if frame:
			print "Received something from {}! |{}|".format(n,response)
			message = string.split(response,'-')
			del message[0] #First entry is an empty chunk of data, discard

			if( int(message[0]) == GET_TEMP_DATA):
				print "GET_TEMP_DATA Received! Parsing and saving to file"
				record_Update_Data(message)
			else :
				print "ERROR: Don't know how to parse: |{}|".format(response)




	#Give the system a little break
	#This could be longer, but remember the amount of data that will be coming from each node
	time.sleep(0.25);





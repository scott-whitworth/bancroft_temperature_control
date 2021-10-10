#!/usr/bin/python

import smbus #Used to talk to the Arduino
import sys   #Used with comand line arguments
import math  #used with the floor functions
import time  #Used for time synching with the arduino

#Set Up i2c Bus
bus = smbus.SMBus(1)

ARD1_ADDRESS =  0x11

#Time Indexing format:
#     0       1      2      3      4     5      6      7      8      9     10     11
# 00:00 , 00:30, 01:00, 01:30, 02:00, 2:30, 03:00, 03:30, 04:00, 04:30, 05:00, 05:30 

#    12     13     14     15     16     17     18     19     20     21     22     23
# 06:00, 06:30, 07:00, 07:30, 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30

#    24      25     26     27     28    29     30     31     32     33     34     35
# 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30

#    36     37     38     39     40     41     42     43     44     45     46     47
# 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, 21:00, 21:30, 22:00, 22:30, 23:00, 23:30 


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

if len(sys.argv) < 4 :
	print "Error with input, too few inputs. Usage: i2c_command.py [ARD_Address] [cmd] [argument]"
	sys.exit()

ard_address = int(sys.argv[1])
cmd = int(sys.argv[2])

print "Trying to send command: {} to {} ".format(cmd,ard_address)

if cmd == HISTORIC :
	print "Sending Historic Data"
	if len(sys.argv) == 6:
		bus.write_i2c_block_data(ard_address,cmd,[int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]) ]) #handles raw int input
	elif len(sys.argv) == 5:
		bus.write_i2c_block_data(ard_address,cmd, [int(sys.argv[3])]+cF_2i(float(sys.argv[4])) ) #handles float input
	else :
		print "The Historic command requires three arguments: [TimeIndex,int(MS_Temp),int(LS_Temp)] or [TimeIndex, float(Temp)]"
elif cmd == FUTURE :
	print "Sending Future Data"
	if len(sys.argv) == 6 :
		bus.write_i2c_block_data(ard_address,cmd,[int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]) ])
	elif len(sys.argv) == 5:
		bus.write_i2c_block_data(ard_address,cmd,[int(sys.argv[3])] + cF_2i(float(sys.argv[4])) )
	else :
		print "The Future command requires three arguments: [TimeIndex,int(MS_Temp),int(LS_Temp)] or [TimeIndex, float(Temp)]"

elif cmd == REPORT:
	print "ERROR: Report is only for Arduino to USE"

elif cmd == GET_STATUS :
	print "Requesting Data for tankIndex {}".format(sys.argv[3])
	if len(sys.argv) == 4 :
		bus.write_i2c_block_data(ard_address,cmd,[int(sys.argv[3])]) #Send the Tank Index first
		get_Data=bus.read_i2c_block_data(ard_address,cmd) #Read back data associated with Tank Index
		#parse recieved data
		tankNum = int(get_Data[0]);
		isFuture = bool(get_Data[1]);
		measuredTemp = float(get_Data[2]) + (float(get_Data[3])/100)
		isHeaterOn = bool(get_Data[4])
		setTemp = float(get_Data[5]) + (float(get_Data[6])/100)
		print "Parsed Data: Tank Number: {} isFuture: {} setTemp: {} isHeaterOn: {} measuredTemp: {}".format(tankNum,isFuture,setTemp,isHeaterOn,measuredTemp) 
	else :
		print "GET_STATUS requires a tankIndex to function properly"

elif cmd == SYNCH_TIME :
	cur_time = time.gmtime() #Read current system time
	print "Current Time: {}".format(cur_time)
	#Assemble time data from current system time
	send_data = [int( math.floor( float(cur_time[0]) / 100.0))] #upper part of year (20 for 2017)
	send_data.append( int( cur_time[0] - (send_data[0]*100) ) ) #lower part of year (17 for 2017)
	send_data.append( int(cur_time[1]) ) #Month
	send_data.append( int(cur_time[2]) ) #day
	send_data.append( int(cur_time[3]) ) #hour
	send_data.append( int(cur_time[4]) ) #minute
	send_data.append( int(cur_time[5]) ) #second
	bus.write_i2c_block_data(ard_address,cmd,send_data);
else :
	print "Unknow Command {}".format(cmd)

#bus.write_i2c_block_data(DEVICE_ADDRESS,DEVICE_REG_LEDOUT0, ledout_values)
#test_vals = [int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])]
#bus.write_i2c_block_data(ARD1_ADDRESS,int(sys.argv[1]),test_vals)


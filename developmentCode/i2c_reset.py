#!/usr/bin/python

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

GPIO.setwarnings(False);

pin_scl = 5
pin_sda = 3


def read_scl():
	GPIO.setup(pin_scl,GPIO.IN)
	return GPIO.input(pin_scl)

def read_sda():
	GPIO.setup(pin_sda,GPIO.IN)
	return GPIO.input(pin_sda)

def clear_scl():
	GPIO.setup(pin_scl,GPIO.OUT)
	GPIO.output(pin_scl,0)

def set_scl():
	GPIO.setup(pin_scl,GPIO.OUT)
	GPIO.output(pin_scl,1)


def clear_sda():
	GPIO.setup(pin_sda,GPIO.OUT)
	GPIO.output(pin_sda,0) 

print "Starting the bit banging for i2c"

print"Starting out, sclValue:{} sdaValue:{}".format(read_scl(),read_sda())

for i in range (0,9):
	set_scl()
	print"set SDA {} for index {}".format(read_sda(),i)
	time.sleep(0.001)
	clear_scl()
	print"clear SDA {} for index {}".format(read_sda(),i)

#GPIO.cleanup([pin_scl,pin_sda])




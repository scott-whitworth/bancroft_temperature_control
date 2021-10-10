# bancroft-lab-shia Supplementary Repository

This code pairs with a physical system developed for Betsy Bancroft's Ecology Lab at Gonzaga University.

## Repository Overview

| Section | Associated Files |
|---------|------------------|
| [System Overview](#System-Overview) | Cool files |
| [System Set Up](#Set-Up-Considerations-and-Documentation) | source |
| [Naming Convention](#system-naming-information) |  |
| [Future Work](#future-work-notes) | |
| [Licenses](#license-information-for-3rd-party-software) | |

| Sub Folder | |
|------------|-|
| `./arduinoCode` | `.ino` file that runs on each of the arduinos. Should not need to be modified per-pair, tank specific config handled by the Pi |
| `./configs` | Past config files used to run the system with documentation |
|`./developmentCode` | Depreciated code based on former system configuration with one massive shared I2C bus from one pi to many Ardunios |
| `./outputData` | Placeholder for output files from the system |
| `./pythonCode` | All of the python scripts used on the Raspberry Pis |
| `./supplementaryData` | Diagnostic or representative data collected regarding the system |
| `./systemSetup` | `.service` files and information on configuring automatic start up of the system |
| `./tempData`   | Placeholder for temperature treatment data, would hold the future and historic `.csv` files |
 
# System Overview

This system is specifically designed to facilitate ecological climate change experiments. The core requirement of the system is to individually control and record the temperature for a collection of aquarium tanks. At the moment each tank can follow one of two temperature profiles. These profiles are made up of many days of temperature data, each in 30 minute segments. As the experiment progresses the system influences the heat added to each tank to approach the required set temperature.

Each tank has a temperature probe and a aquarium heater. The system reads the temperature via the probe and applies heat using the aquarium heater. The collection of tanks are stored in a temperature controlled room set bellow the minimum temperature. The system uses a simple control algorithm comparing the current temperature to the desired temperature, if below: the heater turns on, otherwise: heater turns off.

Each collection of 9 tanks is monitored by a single Arduino Nano. Each Arduino monitors 9 tanks at a time and independently toggles the aquarium heaters to achieve the desired temperature. Each of these Arduinos are connected to a Raspberry Pi via a i2c connection. These Pis are used to keep track of intermediate data as well as coordination between all sets of tanks. There is one final control tank that runs a RabbitMQ server and handles parsing out the main temperature files.

This repository contains all of the code that is run on both the Arduinos and the Raspberry Pis. The code that runs on the Pis is written entirely in Python.

# Set Up Considerations and Documentation

## Arduino:
The arduinos will need the following libraries:

+ Wire.h  
    + Standard Arduino library for communicating with i2c devices. Utilized to communicate between a node's Raspberry Pi and Arduino
+ Time.h  
    + Time organization utility to keep track of rough time. Arduinos do not have a stable or reliable clock, instead cycles are based off of oscillator. This can cause major time drift depending on environmental conditions. Generally, time is updated via the connection to the Pi.
    + Developed by Paul Stoffregen
    + https://github.com/PaulStoffregen/Time
+ OneWire.h  
    + Utility to communicate with bi-directional (onewire) integrated devices. 
    + DallasTemperature.h is dependent on OneWire.h
    + Developed by Paul Stoffregen
    + https://github.com/PaulStoffregen/OneWire
+ DallasTemperature.h 
    + Driver for the Onewire temperature sensors.
    + Dependent on OneWire.h
    + Developed by Miles Burton et al
    + https://github.com/milesburton/Arduino-Temperature-Control-Library 

  
## Raspberry Pi:
All Raspberry Pis are running standard Raspbian Stretch Lite (9.4).  

The Raspberry Pis will need additional setup as follows:  

+ Updating Raspberry Pi System
    + `sudo apt-get update` + `sudo apt-get upgrade`  
    Ensures that the Raspberry Pi application installer is up to data. This will aid in installing RabbitMQ and other tools
+ RabbitMQ Server/Client
    + `sudo apt-get install rabbitmq-server`  
    Gets and installs the RabbitMQ software to handle the communication.
    This is needed for all nodes, not just the main node.
    + The main node also needs to set up a user.   
    `sudo rabbitmqctl add_user <user> <password>`
    `sudo rabbitmqctl set_permissions -p / <user> ".*" ".*" ".*"`
+ Pika Python Library
    + `sudo pip install pika`  
    Installs the python library needed to interface with the RabbitMQ server. This is needed for both the main node, as well as all of the sub nodes.
+ Screen Utility
    + `sudo apt-get install screen`  
    Useful for making sure terminal does not exit when closing connection. See below for more information.
+ Search the repository for `/<user>/` to accurately set all path issues
+ Start Up Behavior
    + See below for details  

## PI Start up configuration  
At power up the main node needs to automatically start the rabbitMQ server as well as start running `bear_trap.py`. The subnodes need to automatically start running `shia_surprise.py`. `systemSetup` contains detailed instructions and a start up scripts for both of these processes.  

The system utilizes the SYSTEMD utility to handle this process. 
+ Create or copy unit file in `/lib/systemd/system/`
    + This can be `bancroft.service` (remote unit pair node) or `bancroft_bear.service` (main control node)
+ Change the user permissions of the unit file to be user:Read Write/group:Read/all:Read (644)
+ Configure systemd  
    + `sudo systemctl daemon-reload`
    + `sudo systemctl enable [bancroft.service|bancroft_bear.service]`  


# System Naming Information

For context: the lab has a long running fixation on the American actor Shia LaBeouf (https://www.youtube.com/watch?v=o0u4M6vppCI)

## Raspberry Pi Naming Convention
System Level Control Node:  

Node Name |
----------|
Shia      | 
  
Control Pair Nodes:  

Node Name | Tanks |
----------|-------|
Yelnats   |   1-9 |
Louis     | 10-18 |
Witwicky  | 19-27 | 
Shaw      | 28-36 |
Mutt      | 37-45 |
Maverick  | 46-54 |
Jack      | 55-63 |
Boyd      | 64-72 |
Farber    | 73-81 |
Francis   | 82-90 |
Drummer   | 91-96*|

\* Experimental design necessitated 96 tanks. There is no functional reason the last tank needs to be limited. The 11th tank could hold tanks 91-99.

## Program Naming Convention

Script Name | Script Description |
-------------|--------------------|
bear_trap.py | Main control script. Controls RabbitMQ configuration, reading configuration and temperature profiles. |
shia_surprise.py | Control Pair supporting script. Connects logically to `bear_trap.py` to send/receive system data, interfaces with Ardiuno code via I2C connection|
normal_tuesday.py | Diagnostic script to parse / probe data. Primarily used in testing the system and monitoring the system state |
peanut_butter_falcon.py | Diagnostic control script that can be run on the Main Control Node in place of `bear_trap.py` to collect system performance data |

# Future Work Notes

+ Proper NTP configuration and or date setting. Check to make sure NTP is valid before the python scripts start running.
+ Arbitrarily different temperature profiles. At the moment the temp profiles are (kind of) hard coded as a binary (future/historic). This could be modified to have n number of temperature profile sources. The system should be able to expand to this feature.
+ Ensure that tank domain is not part of the arduino, but part of the Pis. The arduinos should not care what temperature profile they are part of, just that they know what temp they are supposed to be. This is a hold over from previous development.
+ Better security. This is probably going to need to be different users and different passwords for each node. Might want to use RSA keys.


# License Information for 3rd party Software
+ _Arduino_
    + Base Arduino Hardware
        + Creative Commons Attribution Share-Alike  
        https://creativecommons.org/licenses/by-sa/3.0/    
    + Base Arduino Software
        + General Public License  
        https://www.gnu.org/licenses/gpl-3.0.en.html
    + Wire.h  
        + Standard Arduino library
        + Creative Commons Attribution-ShareAlike 3.0 License https://creativecommons.org/licenses/by-sa/3.0/
    + Time.h  
        + Developed by Paul Stoffregen et al
        + GNU Lesser General Public License  
        https://github.com/PaulStoffregen/Time
    + OneWire.h  
        + Maintained by Paul Stoffregen et al
        + From the code:  
        `Permission is hereby granted, free of charge, to any person obtaining
        a copy of this software and associated documentation files (the
        "Software"), to deal in the Software without restriction, including
        without limitation the rights to use, copy, modify, merge, publish,
        distribute, sublicense, and/or sell copies of the Software, and to
        permit persons to whom the Software is furnished to do so, subject to
        the following conditions:`  
        `The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.`
        https://github.com/PaulStoffregen/OneWire
    + DallasTemperature.h  
        + Developed by Miles Burton et al
        + GNU Lesser General Public License  
        https://github.com/milesburton/Arduino-Temperature-Control-Library  
+ _Raspberry Pi_
    + Raspbian + Raspberry Pi Hardware
        + Creative Commons Attribution-ShareAlike 4.0 License 
        https://creativecommons.org/licenses/by-sa/4.0/
    + RabbitMQ
        + Mozilla Public License, Version 1.1  
        https://www.rabbitmq.com/mpl.html
    + Python
        + Open Source  
        https://docs.python.org/3/license.html
+ _Data Analysis_
    + R Project Scripting Language
        + https://www.r-project.org/Licenses/
    + R ggplot2 Library
        + https://ggplot2.tidyverse.org/LICENSE.html 
  


//Bancroft 2019 Lab Set Up

#include <Wire.h> //i2c Connection
//#include <Time.h> //Used in recording time: https://github.com/PaulStoffregen/Time
//I don't think we need this, all timing should be done on the Pi

//Used for connecting to Temp Probes
#include <OneWire.h> //One wire communication library: https://github.com/PaulStoffregen/OneWire 
#include <DallasTemperature.h> //Used to communicate with temp probes. dependent on OneWire.h: https://github.com/milesburton/Arduino-Temperature-Control-Library 

//////////////////////////
// System Variables
//////////////////////////
#define NUMBER_OF_TANKS 9 //Number of tanks hooked up to this arduino
#define SLAVE_ADDRESS 0x11//Address used by Pi to talk to this arduino THIS MUST BE UNIQUE

//TODO: This should be set by a I2C command
#define MAX_NUM_ON 5 //Maximum number of tanks to be on at any given time

//array of temp profiles identifying the profile of each tank
//This should be filled by a SET_INDEX command from the Pi
//                       T1 T2 T3 T4 T5 T6 T7 T8 T9
uint8_t tempProfile[] = {0, 0, 0, 0, 0, 0, 0, 0, 0};

//Array to map local address of tanks to global tank number
//This should be filled by a SET_INDEX command from the Pi
//                       T1 T2 T3 T4 T5 T6 T7 T8 T9
uint8_t tankNumber[] = { 1, 2, 3, 4, 5, 6, 7, 8, 9};

////////////////////////////////////
// Setup for Temp Probes          //
////////////////////////////////////
/********************************************************************/
#define temp_probe_1 2
#define temp_probe_2 3
#define temp_probe_3 4
#define temp_probe_4 5
#define temp_probe_5 6
#define temp_probe_6 7
#define temp_probe_7 8
#define temp_probe_8 9
#define temp_probe_9 10

//Analog Pins are mapped on the Nano to the following:
//A0=14, A1=15, A2=16, A3=17 A4=18, A5=19, A6=20 A7=21
//                  PT1 PT2 PT3 PT4 PT5 PT6 PT7 PT8 PT9
uint8_t heaters[] = {11, 12, 13, 14, 15, 16, 17, 0, 1};
//From the board:    d11 d12 d13 a0  a1  A2  A3  rx tx (6/25/2019)
                                

/********************************************************************/

// Setup a oneWire instance to communicate with any OneWire devices
// (not just Maxim/Dallas temperature ICs)
OneWire Probe1(temp_probe_1);
OneWire Probe2(temp_probe_2);
OneWire Probe3(temp_probe_3);
OneWire Probe4(temp_probe_4);
OneWire Probe5(temp_probe_5);
OneWire Probe6(temp_probe_6);
OneWire Probe7(temp_probe_7);
OneWire Probe8(temp_probe_8);
OneWire Probe9(temp_probe_9);
/********************************************************************/
// Pass our oneWire reference to Dallas Temperature.
DallasTemperature temp_1(&Probe1);
DallasTemperature temp_2(&Probe2);
DallasTemperature temp_3(&Probe3);
DallasTemperature temp_4(&Probe4);
DallasTemperature temp_5(&Probe5);
DallasTemperature temp_6(&Probe6);
DallasTemperature temp_7(&Probe7);
DallasTemperature temp_8(&Probe8);
DallasTemperature temp_9(&Probe9);
/********************************************************************/
DallasTemperature* tempProbes[NUMBER_OF_TANKS];


///////////////////
//Set Up for i2c //
///////////////////
#define MAX_MESSAGE_SIZE 48
int i2c_command[MAX_MESSAGE_SIZE + 1];

///////////////////
//Messaging Set Up
///////////////////
enum tmp_cmd {
  NOCMD = 0,
  ////////////////////////////////
  // Old commands for posterity //
  ////////////////////////////////
  //HISTORIC = 1, //From: Pi to Arduino. Historic Temperatures. [1,TimeIndex,MS_Temp,LS_Temp]
  //ex: [1,10,30,25] - Set historic entry of 30.25 for 05:00
  //FUTURE = 2,   //From: Pi to Arduino. Future Temperatures [2,TimeIndex,MS_Temp,LS_Temp]
  //ex: [2,15,29,88] - Set Future entry of 29.88 for 07:30
  //REPORT = 3,     //From: Arduino to Pi. Status of Arduino [int(tankNumber),bool(isFuture), int(setTemp_MSB), int(setTemp_LSB), bool(heaterStatus), int(measueredTemp_MSB), int(measuredTemp_LSB)]
  //ex: [50,1, 28, 45, 0, 29, 88] = Tank 50, Future Temp, Set to 28.45 degrees, heater is off, read at 29.88
  //GET_STATUS = 4, //From Pi to Arduino. Force a REPORT message for tank index [4,tankIndex]
  //This should be paired with a read from the MASTER node to get a REPORT msg back
  //SYNCH_TIME = 5  // From Pi to Arduino. Set and Synch time (data tbd)
  /////////////////////////////
  // New Commands (6/25/2019 //
  /////////////////////////////
  SET_TEMP  = 11, //Communicate from Pi to Arduino, to set a temp for a tank. SET_TEMP[int(Tank_Index),int(MS_Temp),int(LS_Temp)]
  READ_TEMP = 12, //Communicate from Pi to Arduino, prepare for update, set tank to be read by CUR_TEMP READ_TEMP[int(tankNumber)]
  CUR_TEMP  = 13, //Communicate from Arduino to Pi, Pull information from Arduino to the pi. Index of interest set by Read_Temp
                  //CUR_TEMP[int(tankNumber), bool(isFuture), int(setTemp_MSB), int(setTemp_LSB), bool(heaterStatus), int(measuredTemp_MSB), int(measuredTemp_LSB)] 
  SET_INDEX = 14  //Communicate from Pi to Arduino, set the local index to a global index with temp domain. SET_INDEX[int(tankNumber),int(globalTankIndex),int(tempProfile)]
};

////////////////////////////////////
// Temperature and Tank Variables //
////////////////////////////////////
//Array to hold set temperatures of tanks, this is filled by taking measurement
float curTemp[NUMBER_OF_TANKS];

//Array of target temperature for tanks
//This is set by a SET_TEMP command from the Pi
float targetTemp[NUMBER_OF_TANKS];

//Array to hold status of the heaters, set by control loop
bool heaterStatus[NUMBER_OF_TANKS];

//Used by GET_STATUS and REPORT to send back data
int cur_Tank_index = 0;

void setup() {
  //We cannot use Serial if pins 0 and 1 are being used for PST Output

  //i2c Set Up
  Wire.begin(SLAVE_ADDRESS);

  //CallBacks
  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);
  
  //Temp Probe SetUp
  temp_1.begin();
  tempProbes[0] = &temp_1;
  temp_2.begin();
  tempProbes[1] = &temp_2;
  temp_3.begin();
  tempProbes[2] = &temp_3;
  temp_4.begin();
  tempProbes[3] = &temp_4;
  temp_5.begin();
  tempProbes[4] = &temp_5;
  temp_6.begin();
  tempProbes[5] = &temp_6;
  temp_7.begin();
  tempProbes[6] = &temp_7;
  temp_8.begin();
  tempProbes[7] = &temp_8;
  temp_9.begin();
  tempProbes[8] = &temp_9;

  //Heater Block Set Up
  for (int i = 0; i < NUMBER_OF_TANKS; i++) {
    pinMode(heaters[i], OUTPUT); //Set Pin to output
    digitalWrite(heaters[i], LOW); //Set Pin to output LOW (off)
    heaterStatus[i] = false; //record heater as being off
  }
}

//Keep track of which tank was the 'next in line' when alternating which tanks get turned on
uint8_t previousOff = 0;
uint8_t tanksOn = 0;
uint8_t tanksOff = 0;
bool    rollingHeater[NUMBER_OF_TANKS];

///////////////////////////////
// Regular Program Structure //
///////////////////////////////
void loop() {
  //Record Current Temperatures
  for (int i = 0; i < NUMBER_OF_TANKS ; i++) { //Iterate over all probes
    tempProbes[i]->requestTemperatures(); //Request the temp data
    curTemp[i] = tempProbes[i]->getTempCByIndex(0); //Read in data
  }

  //Figure out Heater Status, will turn on in next section
  for (int i = 0; i < NUMBER_OF_TANKS ; i++) { //Iterate over all tanks
    if (curTemp[i] < targetTemp[i]) { //Measured Temp is less than set temp
      //Set heater to be ON
      heaterStatus[i] = true;
    } else {
      //Set heater to be OFF
      heaterStatus[i] = false;
    }
    rollingHeater[i] = false; //reset rollingHeater to 0
  }

  //Based on the number of tanks that need to be on
  //apply rolling window of 'on' tanks
  //(making sure there no more than MAX_NUM_ON are on at any given time)
  //turn on starting at zero's, keep rotating
  tanksOn = 0;
  tanksOff = 0;
  uint8_t tIndex = previousOff;
  //previousOff carries over from loop to loop, should be the 'next' index every time

  while( (tanksOn < MAX_NUM_ON) && //The number of tanks that are turned on are less than that maximum that can be turned on
         ( (tanksOff + tanksOn) < NUMBER_OF_TANKS ) //The number of tanks designated as off and on are less than the total number of tanks (there is still work to do)
  ){
    //If status is true, tank needs to be turned on
    //Record status in rollingHeaters, this will enact pin changes in next loop
    if(heaterStatus[tIndex]){
      rollingHeater[tIndex] = true;
      tanksOn++;
    } else {
      tanksOff++;
      //Don't need to turn off, they are already off in previous loop
    }

    //Update tIndex. If equal NUMBER_OF_TANKS, reset to 0 (loop back around)
    tIndex++;
    if(tIndex >= NUMBER_OF_TANKS){
      tIndex = 0;
    }
  }

  //Take intermediate tank status, apply what needs to be turned on to digital pins
  for(int i = 0; i < NUMBER_OF_TANKS; i++){
    if(rollingHeater[i]){ //If true, turn tank on
      //It is possible that this pin is already 'high' 
      //I don't think this will make a difference in the power going to the PST
      digitalWrite(heaters[i],HIGH);
    } else { //Don't turn tank on, might even turn tank off
      digitalWrite(heaters[i],LOW);
    }
  }

  previousOff = tIndex; //Should be the last tIndex the loop already handles the 'wrap around'
 
  delay(11500); //delay 7.5 seconds prevent issues with time locked to 60 second interavals This delay can be set to whatever resolution we want
}

///////////////////
// i2c Callbacks //
///////////////////

//Callback for receiving data
void receiveData(int byteCount) {
  char data;
  int dat_index = 0; //keep track of number of recieved pieces of information

  // Read in the incoming string.
  //Data is stored as INTs in i2c_command
  // dat_index is the number of the pieces of information recieved
  while (Wire.available()) {
    data = Wire.read();

    i2c_command[dat_index] = (int) data;
    dat_index++;
  }

  if (dat_index == 0) { //Check for empty string. If this is happening, there is probably an issue
    return;
  }

   //Parse through all the possible commands
  if (i2c_command[0] == SET_TEMP){
    //Communicate from Pi to Arduino, to set a temp for a tank. SET_TEMP[int(Tank_Index),int(MS_Temp),int(LS_Temp)]
    //                                                                         i2c_c[1]     i2c_c[2]       i2c_c[3]
    if(dat_index == 4){
      //               Index                     MSB                    LSB
      targetTemp[i2c_command[1]] = float(i2c_command[2]) + (float(i2c_command[3]) / 100);
    }
    
  } else if (i2c_command[0] == READ_TEMP){
    //Communicate from Pi to Arduino, prepare for update, set tank to be read by CUR_TEMP READ_TEMP[int(tankNumber)]
    if (dat_index == 2) {
      cur_Tank_index = i2c_command[1];
    }
    
  } else if (i2c_command[0] == SET_INDEX){
    //Communicate from Pi to Arduino, set the local index to a global index with temp domain. SET_INDEX[int(tankNumber),int(globalTankIndex),int(tempProfile)]
    //                                                                                                       i2c_c[1]          i2c_c[2]             i2c_c[3]

    //Assign global tank number
    tankNumber[i2c_command[1]] = i2c_command[2];
    //Assign Temp Profile 
    tempProfile[i2c_command[1]] = i2c_command[3];    
  } 
    
  //Check for a Get Status command. This will set the cur_Tank_index that will be used by sendData to send the requested data
  else if (i2c_command[0] == 4) { //Old GET_STATUS command, still should work witht the system
    if (dat_index == 2) {
      cur_Tank_index = i2c_command[1];
    } else { } //Handle the duplicate command from requesting GET_STATUS
  } else { //Final error check.
    //i2c error! No command found!
  }
}


//Callback for sending data
void sendData() {
  byte data[10];
  data[0] = tankNumber[cur_Tank_index];
  data[1] = tempProfile[cur_Tank_index];
  data[2] = int(floor(curTemp[cur_Tank_index]));
  data[3] = int(floor( (curTemp[cur_Tank_index] - float(data[2])) * 100.0) );
  data[4] = heaterStatus[cur_Tank_index];
  data[5] = int(floor(targetTemp[cur_Tank_index]));
  data[6] = int(floor( (targetTemp[cur_Tank_index] - float(data[5])) * 100.0));

  Wire.write(data, 7);
}

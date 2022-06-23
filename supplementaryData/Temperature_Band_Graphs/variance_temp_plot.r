library(ggplot2) 
# load in the ggplot library

# This is a modification of the tank_multi_temp_plot.r code from summer of 2021 analysis
# The goal of this script is to produce variance and error band calculations based on set-temp bands 

# Utility function to both add required headers and calculate good day values
day_set <- function(in_raw_data){
    in_raw_data <- in_raw_data[-c(1),] #Remove stale headers
    
    names(in_raw_data)[1] <- "year" # We might need days so that we can mask out days before/after the test
    names(in_raw_data)[2] <- "month" #I don't think we will end up needing time (as we are going to bin based on temp)
    names(in_raw_data)[3] <- "dayOMonth"
    names(in_raw_data)[4] <- "time"
    names(in_raw_data)[5] <- "tank"
    names(in_raw_data)[6] <- "treatement"
    names(in_raw_data)[7] <- "set_temp"
    names(in_raw_data)[8] <- "heaterStat"
    names(in_raw_data)[9] <- "mea_temp"
    in_raw_data$norm_time <- 0.0
    in_raw_data$deltaTemp <- 0.0 #difference between two neighbors
    in_raw_data$tempError <- 0.0 #difference in set to measured
    in_raw_data$day <- 0.0
    
    #Deal with june
    index <- in_raw_data$month == "6"
    in_raw_data$day[index] <- (as.numeric(in_raw_data$dayOMonth[index]) - 26)
    
    #Deal with july
    index <- in_raw_data$month == "7"
    in_raw_data$day[index] <- (as.numeric(in_raw_data$dayOMonth[index]) + 4)
    
    #Deal with august
    index <- in_raw_data$month == "8"
    in_raw_data$day[index] <- (as.numeric(in_raw_data$dayOMonth[index]) + 4 + 31)
    
    #Deal with sept
    index <- in_raw_data$month == "9"
    in_raw_data$day[index] <- (as.numeric(in_raw_data$dayOMonth[index]) + 4 + 31 + 31)
    
    
    return (in_raw_data)
}

###############
## 2021 Data ##
###############

# Set up to parse the data from running the system over the summer of 2021 (so 6 tanks per control pair)
file <- './2021_6_3_56days_total_status.csv'
file_prefix <- "2021_"
plot_sub <- expression('Average per Tank, processed from summer 2021 data, Recording resolution: 5 mins') 

#Ploting variables
maxTempBin <- 26
minTempBin <- 19

#Tank parsing info
startingDay <- 25 #This is assuming the calculations really start on Day 25
endingDay <- 40 #This ends the calculations at day 40 
ignore_tanks <- c(1,2,3,10,11,12,19,20,21,28,29,30,37,38,39,46,47,48,55,56,57,64,65,66,71) #Because of only using 6 tanks per set, we can ignore 3/9 of them
# Tank 71 has some odd stuff going on days 25-32, I think this was a heater issue
tank_nums <- 1:72 #All the possible tanks to pull information from

# ###############
# ## 2018 Data ##
# ###############

## IMPORTANT: Don't run the file opening portion for 2018 data, it needs to be loaded differently

# # Set up to parse the data from running the system over the summer of 2021 (so 6 tanks per control pair)
file1 <- './2018/01-09_yelnats_all_data_2019_07_05.csv'
file2 <- './2018/10-18_louis_all_data_2019_07_05.csv'
file3 <- './2018/19-27_witwicky_all_data_2019_07_05.csv'
file4 <- './2018/28-36_shaw_all_data_2019_07_08.csv'
file5 <- './2018/37-45_mutt_all_data_2019_07_08.csv'
file6 <- './2018/46-54_maverick_all_data_2019_07_05.csv'
file7 <- './2018/55-63_jack_all_data_2019_07_05.csv'
file8 <- './2018/64-72_boyd_all_data_2019_07_05.csv'
file9 <- './2018/73-81_farber_all_data_2019_07_05.csv'
file10 <- './2018/82-90_francis_all_data_2019_07_05.csv'
file11 <- './2018/91-96_drummer_all_data_2019_07_05.csv'

file_prefix <- "2018_"
plot_sub <- expression('Average per Tank, processed from summer 2018 data, Recording resolution: 5 mins') 

# #Ploting variables
maxTempBin <- 25
minTempBin <- 16

# There are some odd things going on with temp bands less than 16. I think this has to do with a bit flip that was un caught
# Example: Thank 46 getting a set temp of 11.55 (I am pretty sure it was supposed to be 21.55, that is what the other set temps for that time were)

# #Tank parsing info
startingDay <- 1 #This is assuming the calculations really start on Day 25
endingDay <- 34 #This is based on shortest file (drummer (91-96))
ignore_tanks <- c( 0 )
tank_nums <- 1:96 #All the possible tanks to pull information from

# Tank 

# Special set up for 2018
raw_data1 <- read.csv(file1,header = FALSE)
raw_data1 <- day_set(raw_data1)

raw_data2 <- read.csv(file2,header = FALSE)
raw_data2 <- day_set(raw_data2)

raw_data3 <- read.csv(file3,header = FALSE)
raw_data3 <- day_set(raw_data3)

raw_data4 <- read.csv(file4,header = FALSE)
raw_data4 <- day_set(raw_data4)

raw_data5 <- read.csv(file5,header = FALSE)
raw_data5 <- day_set(raw_data5)

raw_data6 <- read.csv(file6,header = FALSE)
raw_data6 <- day_set(raw_data6)

raw_data7 <- read.csv(file7,header = FALSE)
raw_data7 <- day_set(raw_data7)

raw_data8 <- read.csv(file8,header = FALSE)
raw_data8 <- day_set(raw_data8)

raw_data9 <- read.csv(file9,header = FALSE)
raw_data9 <- day_set(raw_data9)

raw_data10 <- read.csv(file10,header = FALSE)
raw_data10 <- day_set(raw_data10)

raw_data11 <- read.csv(file11,header = FALSE)
raw_data11 <- day_set(raw_data11)

raw_data <- rbind(raw_data1,raw_data2,raw_data3,raw_data4,raw_data5,raw_data6,raw_data7,raw_data8,raw_data9,raw_data10,raw_data11)
new_data <- raw_data

# ###############
# ## 2019 Data ##
# ###############

# Set up to parse the data from running the system over the summer of 2019
file <- './2019/2019_6_6_69days_total_status.csv'
file_prefix <- "2019_"
plot_sub <- expression('Average per Tank, processed from summer 2019 data, Recording resolution: 5 mins') 

# #Ploting variables
maxTempBin <- 27
minTempBin <- 16

# #Tank parsing info
startingDay <- 39 #This is assuming the calculations really start on Day 39 (July 3rd?)
endingDay <- 80 #This ends the calculations at day 59 (a guess for total length of experiment)
ignore_tanks <- c(8,33,35)
# Tank 8 and 33 has some weird data, removed
tank_nums <- 1:64 #All the possible tanks to pull information from
#only 64 tanks used even though 96 tank's worth of data is present

#Will also need to remove the single data points for tank 36 and 40 bin 50


################################
# Start of the data processing #
################################

#Pull in the data
message(sprintf("Opening File..."))
raw_data <- read.csv(file,header = FALSE) # Read in the specified file while ignoring the headers

start_time <- raw_data[1,1] #First 'cell' is the hard-coded start time, grab that
message(sprintf("Processing data from: %s",start_time))

nLines <- nrow(raw_data)
message(sprintf("Loaded in %d lines\n",nLines-1))

#Set up names of colums, this is a different format than before
names(raw_data)[1] <- "day" # We might need days so that we can mask out days before/after the test
names(raw_data)[2] <- "halfHour" #I don't think we will end up needing time (as we are going to bin based on temp)
names(raw_data)[3] <- "measurementID"
names(raw_data)[4] <- "tank"
names(raw_data)[5] <- "tempProf"
names(raw_data)[6] <- "set_temp"
names(raw_data)[7] <- "heaterStat"
names(raw_data)[8] <- "mea_temp"
names(raw_data)[9] <- "timeStamp"
raw_data$norm_time <- 0.0
raw_data$deltaTemp <- 0.0 #difference between two neighbors
raw_data$tempError <- 0.0 #difference in set to measured

new_data <- raw_data[-c(1),] #Remove hard coded time

###############################
# Start back up here for 2018 #
###############################

message(sprintf("Removing ignored tanks..."))
for(select in ignore_tanks){
    new_data <- new_data[new_data$tank != select,]
    
}

#Placeholder for the temp info for each tank
# 0-50 C for each tank
tankBins_delta <- matrix(0, nrow = 96, ncol = 50)
tankBins_error <- matrix(0, nrow = 96, ncol = 50)

#Loop through file computing a delta between a tank read value and a its neighbor (n vs n+1)
for (cur_tank in tank_nums){
#cur_tank <- 4
    if(sum(cur_tank == ignore_tanks) > 0){ # boolean returns an array of true/false, sum adds them all up, if 0, then the cur_tank is NOT in the list
        #current tank is in the ignored_tank list, skip this loop!
    } else {
    
        sub_data <- subset(new_data, as.numeric(tank)==cur_tank & as.numeric(day)>=startingDay & as.numeric(day)<=endingDay)
        message(sprintf("Current tank: %d length: %d ",cur_tank,nrow(sub_data)))
        
        sub_data[,]$mea_temp <- as.numeric(sub_data[,]$mea_temp)
        sub_data[,]$set_temp <- as.numeric(sub_data[,]$set_temp)
        
        sumCount <- numeric(50) #Generate a vector of size = 50
        # This is used to normalize / average the totals when we are done computing them
        
        #Loop through the sub_data to calculate neighbors
        #This is assuming things are already 'in order'
        #might as well also calculate error from set temp
        
        for (curIndex in 1:(nrow(sub_data)-1) ){
            #message(sprintf("Looking at current row: %d",curIndex))
            #message(sprintf("Temp: %f",as.numeric(sub_data[curIndex,]$mea_temp)))
            sub_data[curIndex,]$deltaTemp <- abs(sub_data[curIndex,]$mea_temp - sub_data[(curIndex+1),]$mea_temp)
            sub_data[curIndex,]$tempError <- abs(sub_data[curIndex,]$mea_temp - sub_data[curIndex,]$set_temp)
            
            bin <- floor(sub_data[curIndex,]$set_temp)
            
            if(bin > 50){
                bin <- 50
            }
            if(bin < 0){
                bin <- 0
            }
            
            sumCount[bin] <- sumCount[bin] + 1 #incrament count for this bin
            
            #incrament the delta / error counts for this specific bin
            tankBins_delta[cur_tank,bin] <- tankBins_delta[cur_tank,bin] + sub_data[curIndex,]$deltaTemp
            tankBins_error[cur_tank,bin] <- tankBins_error[cur_tank,bin] + sub_data[curIndex,]$tempError
        }
        
        #Normalize / average the bins
        for( bin in 1:ncol(tankBins_delta)){
            if(sumCount[bin] == 0){
                #Don't worry about the divide by zero
                tankBins_delta[cur_tank,bin] <- 0
                tankBins_error[cur_tank,bin] <- 0
                
            } else {
                tankBins_delta[cur_tank,bin] <- tankBins_delta[cur_tank,bin] / sumCount[bin]
                tankBins_error[cur_tank,bin] <- tankBins_error[cur_tank,bin] / sumCount[bin]
            }
        }
    }

}

# At this point we have the data filtered into bins, and those bins are averaged into tankBins_delta and _error

# Translate into data.frames
deltaPrint <- data.frame(tempBin = 0, averageDelta=0, averageError = 0, tankID = 0)
deltaPrint <- data.frame()

#deltaPrint is just the temp bin, averageDelta, average error and tank ID
for( bin in 1:ncol(tankBins_delta)){ #Iterate through the bins
    for(tank in 1:nrow(tankBins_delta)){ #iterate through the tanks
        #message(sprintf("Bin: %d , tank: %d",bin,tank))
        if(tankBins_delta[tank,bin] != 0 && !is.na(tankBins_delta[tank,bin]) ) { #ignore all of the zero data
            newDeltaRow <- data.frame(
                tempBin = bin,
                averageDelta = tankBins_delta[tank,bin],
                averageError = tankBins_error[tank,bin],
                tankID = tank)
            
            deltaPrint <- rbind(deltaPrint, newDeltaRow)
        }
    }
}


#Plot the deltas and the errors as separate values per bin
p_out <- ggplot(deltaPrint,aes(x=tempBin, y=averageDelta)) +
    geom_point() +
    scale_x_continuous(limits=c(minTempBin,maxTempBin), breaks=seq(minTempBin,maxTempBin,1)) +
    labs(title=sprintf("Measurement Temperature Variance for Temperature Bands"),
         subtitle=plot_sub,
         x=expression('Temperature Band ('*degree*'C)'),
         y=expression('Measurement to Measurement Delta ('*degree*'C)')) +
    theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor=element_blank(), legend.spacing.y = unit(-1,"cm"))

plot(p_out)

#Save Chart
ggsave(
    sprintf("%sdeltaVarianceByTempBand.png",file_prefix),
    plot = p_out,
    dpi = 600
)

p_out <- ggplot(deltaPrint,aes(x=tempBin, y=averageError)) +
    geom_point() +
    scale_x_continuous(limits=c(minTempBin,maxTempBin), breaks=seq(minTempBin,maxTempBin,1)) +
    labs(title=sprintf("Measured to Set Temp Absolute Error Variance for Temperature Bands"),
         subtitle=plot_sub,
         x=expression('Temperature Band ('*degree*'C)'),
         y=expression('Measured to Set Temp Absolute Error ('*degree*'C)')) +
    theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor=element_blank(), legend.spacing.y = unit(-1,"cm"))

plot(p_out)

#Save Chart
ggsave(
    sprintf("%serrorVarianceByTempBand.png",file_prefix),
    plot = p_out,
    dpi = 600
)

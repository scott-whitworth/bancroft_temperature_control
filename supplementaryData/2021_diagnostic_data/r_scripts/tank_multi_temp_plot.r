library(ggplot2) 
# load in the ggplot library

# TIME STAMP WARRNING:
# This assumes a June to July time stamp overstep!
# If the months are different you will need to modify calc_norm_time to handle a non-30 day time roll over

stat_tank_ignore <- NULL
single_tank <- 0


# 9 tanks, full water, cold to hot
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_14_all_cold_to_hot_full_tank.csv'
# file_prefix <- "full_all_c2h_"
# plot_title <- "Heating Temperature Profile, Min/Average/Max"
# plot_sub <- expression('full water level, nine tanks, from ambient temp to set_temp = 40'*degree*'C')
# time_max <- 1080
# temp_max <- 35.0
# temp_min <- 10.0

# 9 tanks, full water, hot to cold
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_15_hot_to_cold_full_tank.csv'
# file_prefix <- "full_all_h2c_"
# plot_title <- "Cooling Temperature Profile, Min/Average/Max"
# plot_sub <- expression('full water level, nine tanks, from set_temp = 40'*degree*'C to ambient temp')
# time_max <- 1440
# temp_max <- 35.0
# temp_min <- 10.0

#9 tanks, half water, cold to hot
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_6_30_cold_to_hot_all_half.csv'
# file_prefix <- "half_all_c2h_"
# plot_title <- "Heating Temperature Profile, Min/Average/Max"
# plot_sub <- expression('half water level, nine tanks, from ambient temp to set_temp = 40'*degree*'C')
# time_max <- 780
# temp_max <- 35.0
# temp_min <- 10.0

# 9 tanks, half water, hot to cold
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_6_29_hot_to_cold_halfTank.csv'
# file_prefix <- "half_all_h2c_"
# plot_title <- "Cooling Temperature Profile, Min/Average/Max"
# plot_sub <- expression('half water level, nine tanks, from set_temp = 40'*degree*'C to ambient temp')
# time_max <- 1200
# temp_max <- 35.0
# temp_min <- 10.0

# Subset of tanks
#Five tanks, full water, cold to hot, on: 2, 4, 6, 8, 9
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_12_five_tanks_warming_full_water.csv'
# file_prefix <- "full_five_c2h_"
# plot_title <- "Warming Temperature Profile, Min/Average/Max"
# plot_sub <- expression('full water level, five tanks, from ambient temp to set_temp = 40'*degree*'C ')
# time_max <- 1200
# temp_max <- 35.0
# temp_min <- 10.0
# # Overwrite stat tank numbers
# stat_tank_ignore <- c(73, 75, 77, 79)
# # 73 74 75 76 77 78 79 80 81
# # 1  2  3  4  5  6  7  8  9

# Subset of tanks
# #Five tanks, half water, cold to hot, on: 2, 3, 5, 7, 8
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_7_five_tanks_cold_to_hot_half_tanks.csv'
# file_prefix <- "half_five_c2h_"
# plot_title <- "Warming Temperature Profile, Min/Average/Max"
# plot_sub <- expression('half water level, five tanks, from ambient temp to set_temp = 40'*degree*'C ')
# time_max <- 1200
# temp_max <- 35.0
# temp_min <- 10.0
# # Overwrite stat tank numbers
# stat_tank_ignore <- c(73, 76, 78, 81)
# # 73 74 75 76 77 78 79 80 81
# # 1  2  3  4  5  6  7  8  9

# SingleTanks
# 1 tank (76/4), half water, cold to hot
file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_6_one_tank_heating_half_water.csv'
file_prefix <- "half_one_c2h_"
plot_title <- "Heating Temperature Profile"
plot_sub <- expression('half water level, one tank, from ambient temp to set_temp = 40'*degree*'C')
time_max <- 840
temp_max <- 35.0
temp_min <- 10.0
single_tank <- 76

# # 1 tank (77/5), half water, cold to hot
# file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_9_one_tank_cold_to_hot_full_tanks.csv'
# file_prefix <- "full_one_c2h_"
# plot_title <- "Heating Temperature Profile"
# plot_sub <- expression('full water level, one tank, from ambient temp to set_temp = 40'*degree*'C')
# time_max <- 1200
# temp_max <- 35.0
# temp_min <- 10.0
# single_tank <- 77



tank_nums <- 73:81 #There should be nine tanks in the file, this keeps their indices organized
xlim_max <- time_max

##############################
# Time manipulation function #
##############################

# Parse helper
# Creates a list {hour,minute,second,float} from "hh:mm:ss"
# float is the cur time in minutes
convert_time <- function(time_string){
    out <- list() #Set up the list to be filed in

    #Check hour digit
    if(substr(time_string,2,2) == ":"){
        #only one digit in the hour
        out$hour <- strtoi(substr(time_string,1,1)) #one digit
        next_digit <- 3
    } else {
        out$hour <- strtoi(substr(time_string,1,2)) #two digits
        next_digit <- 4
    }

    #Check minute digit
    if(substr(time_string,next_digit+1,next_digit+1) == ":"){
        #only one digit in the minute
        out$minute <- strtoi(substr(time_string,next_digit,next_digit))
        next_digit <- next_digit + 2
    } else {
        out$minute <- strtoi(substr(time_string,next_digit,next_digit+1))
        next_digit <- next_digit + 3
    }

    #The substring should take care of both 1 and 2 digit seconds
    out$second <- strtoi(substr(time_string,next_digit,next_digit+1))

    # Calculate minute total for this 'time'
    out$float <- (out$hour * 60.0) + out$minute + (out$second / 60.0)

    return(out)
} 

#Utility to make a singular time stamp for comparison
make_timeStamp <- function(cur_row){
    out <- list()
    out$month <- cur_row$month
    out$day <- cur_row$day

    temp_time <- convert_time(cur_row$time) #Grab data from convert_time
    out$hour <- temp_time$hour
    out$minute <- temp_time$minute
    out$second <- temp_time$second
    out$float <- temp_time$float

    return(out)    
}

#input: cur_row of data. We need day and time information
#       first_time -> calculates the offset
# output: minutes since starting the file
calc_norm_time <- function( cur_row , first_time){

    #grab time stamp for current point
    cur_time <- make_timeStamp(cur_row)

    while(cur_time$month > first_time$month){
        cur_time$month <- cur_time$month -1
        cur_time$day <- cur_time$day + 30
    }

    while(cur_time$day > first_time$day){
        #keep reducing day until it is the same day
        cur_time$day <- cur_time$day-1
        cur_time$hour <- cur_time$hour + 24 # make current time hour larger by a whole day
        cur_time$float <- cur_time$float + (24 * 60.0) #Update float as well
    }

    #At this point both cur_time and first_time should be in relation to the same day
    #now just need to take the difference in the $float values (that should be total elapsed time)
    return(cur_time$float - first_time$float)
}


#######
# END #
#######


#Pull in the data
raw_data <- read.csv(file,FALSE) # Read in the specified file while ignoring the headers

start_time <- raw_data[1,1] #First 'cell' is the hard-coded start time, grab that
message(sprintf("Processing data from: %s",start_time))

nLines <- nrow(raw_data)
message(sprintf("Loaded in %d lines\n",nLines-1))

#Set up names of collums
names(raw_data)[1] <- "year"
names(raw_data)[2] <- "month"
names(raw_data)[3] <- "day"
names(raw_data)[4] <- "time"
names(raw_data)[5] <- "tank"
names(raw_data)[6] <- "nu_treatment"
names(raw_data)[7] <- "set_temp"
names(raw_data)[8] <- "heater"
names(raw_data)[9] <- "mea_temp"
raw_data$norm_time <- 0.0

new_data <- raw_data[-c(1),] #Remove hard coded time

time_start <- make_timeStamp(new_data[1,]) #Get time stamp for the first data entry (should be the earliest time stamp)

#Add a normalized time for each of the rows in the data set
#This should all be based off of the ^^^ time_start and that rows 'time'
for(row in 1:nrow(new_data)){
    new_data[row,]$norm_time = calc_norm_time(new_data[row,],time_start)
}

#Loop through all of the tanks and graph the data
for (cur_tank in tank_nums){
    #cur_tank <- 73
    sub_data <- subset(new_data,tank==cur_tank)
    message(sprintf("Current tank: %d length: %d ",cur_tank,nrow(sub_data)))

    p_out <- ggplot( data=sub_data, aes(x=norm_time, y=mea_temp)) + 
    geom_point() +
    #ylim(10.0,35.0) + # 10 to 40 C
    #xlim(0,1000) +    # 0 to 1000 minutes (16.6 hrs)
    scale_y_continuous(limits=c(temp_min,temp_max), breaks=seq(temp_min,temp_max,5.0), minor_breaks=seq(temp_min,temp_max,1.0)) +
    scale_x_continuous(limits=c(0,xlim_max), breaks=seq(0,xlim_max,300), minor_breaks=seq(0,xlim_max,60)) +
    labs(title=sprintf("Tank %d Temperature Profile",cur_tank),
         subtitle=plot_sub,
         x="Time (minutes)",
         y=expression('Temperature ('*degree*'C)')) +
    theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor=element_blank(), legend.spacing.y = unit(-1,"cm"))


    # Save plot
    ggsave(
        sprintf("%s%d_tank_single.png",file_prefix,cur_tank),
        plot = p_out,
        #width = 5.0,
        #height = 5.0,
        dpi = 600
    )
}

# Conglomorate data
stat_data <- sub_data #Get it started (there should be equal number for all tanks)
                      #Time stamp data should be consistant 
stat_data$min <- 0.0
stat_data$max <- 0.0
stat_data$average <- 0.0

#Step over every row of stat_data frame
for (time_step in 1:nrow(stat_data)){
    #Grab the current normalized time
    cur_norm_time <- stat_data[time_step,]$norm_time

    #Collect subset of all tanks equal to current norm_time
    cur_tanks <- subset(new_data, norm_time==cur_norm_time)
    # message(sprintf("%d Current time: %f Number of tanks: %d \n", time_step , stat_data[time_step,]$norm_time, nrow(cur_tanks)))
    # print(cur_tanks)

    #Remove any tanks that need to be ignored
    for(select in stat_tank_ignore){
        cur_tanks <- cur_tanks[cur_tanks$tank != select,]
    }

    #Initially seed everything
    cur_min <- cur_tanks[1,]$mea_temp 
    cur_max <- cur_tanks[1,]$mea_temp 
    cur_total <- cur_tanks[1,]$mea_temp 

    #Go through the rest of the tanks to get min/max/average
    for(tank in 2:nrow(cur_tanks)){        
        #Check for min value
        if( cur_tanks[tank,]$mea_temp < cur_min){
            cur_min <-  cur_tanks[tank,]$mea_temp
        }
        #Check for max value
        if( cur_tanks[tank,]$mea_temp > cur_max){
            cur_max <- cur_tanks[tank,]$mea_temp
        }
        #Add to the total
        cur_total <- cur_total + cur_tanks[tank,]$mea_temp
    }
    #message(sprintf("Min: %f, Max: %f, Avg: %f",cur_min, cur_max, (cur_total/9.0)))

    #Keep all this data set up in stat_data
    stat_data[time_step,]$min <- cur_min
    stat_data[time_step,]$max <- cur_max
    stat_data[time_step,]$average <- cur_total/nrow(cur_tanks)    

}

#Handle both 'final' plots for single and multi tank sets
if(single_tank == 0){
    #Plot Stat data
    p_out <- ggplot( data=stat_data, aes(x=norm_time, y=average, ymin=min, ymax=max) ) + 
    #Plot the span between the min and max
    geom_ribbon(alpha=0.35, fill="salmon", aes(color="Min/Max Range")) + 
    #Highlight the 'edge' of the span
    geom_line(aes(x=norm_time, y=min), col="red", size=0.25, alpha = 0.65 ) +
    geom_line(aes(x=norm_time, y=max), col="red", size=0.25, alpha = 0.65) +
    #Plot the average temp
    geom_line(size=1, color="black", aes(alpha="Average")) +
    #Plot horizontal line to show set temp (probably not needed as the limits cut this out)
    # geom_hline(yintercept=40.0,color="black",linetype="dashed") + #Included if we want to show the set temp, right now it is well above the plot limits
    #Setting scales to pre-defined limits (above)
    scale_y_continuous(limits=c(temp_min,temp_max), breaks=seq(temp_min,temp_max,5.0), minor_breaks=seq(temp_min,temp_max,1.0)) +
    scale_x_continuous(limits=c(0,xlim_max), breaks=seq(0,xlim_max,300), minor_breaks=seq(0,xlim_max,60)) +
    #Set up legend to show both average and min/max
    scale_alpha_manual(name=NULL, values=c(1), breaks = c( "Average")) +
    scale_color_manual(name=NULL, values = c("Min/Max Range" = "salmon" )) +
    labs(title=plot_title,
            subtitle=plot_sub,
            x="Time (minutes)",
            y=expression('Temperature ('*degree*'C)') ) +
    theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor=element_blank(), legend.spacing.y = unit(-1,"cm"))

} else {    
    sub_data <- subset(new_data,tank==single_tank)

    #Single Plot
    p_out <- ggplot( data=sub_data, aes(x=norm_time, y=mea_temp) ) + 
    #Plot the temp
    geom_line(size=1, color="black") +
    #Plot horizontal line to show set temp (probably not needed as the limits cut this out)
    # geom_hline(yintercept=40.0,color="black",linetype="dashed") + #Included if we want to show the set temp, right now it is well above the plot limits
    #Setting scales to pre-defined limits (above)
    scale_y_continuous(limits=c(temp_min,temp_max), breaks=seq(temp_min,temp_max,5.0), minor_breaks=seq(temp_min,temp_max,1.0)) +
    scale_x_continuous(limits=c(0,xlim_max), breaks=seq(0,xlim_max,300), minor_breaks=seq(0,xlim_max,60)) +
    #Set up legend to show both average and min/max
    #scale_alpha_manual(name=NULL, values=c(1), breaks = c( "Average")) +
    #scale_color_manual(name=NULL, values = c("Min/Max Range" = "salmon" )) +
    labs(title=plot_title,
            subtitle=plot_sub,
            x="Time (minutes)",
            y=expression('Temperature ('*degree*'C)') ) +
    theme_bw() + theme(panel.grid.major = element_blank(), panel.grid.minor=element_blank(), legend.spacing.y = unit(-1,"cm"))

}

ggsave(
    sprintf("%sstat_profile.png",file_prefix),
    plot = p_out,
    #width = 5.0,
    #height = 5.0,
    dpi = 600
)

#png("stat_tanks_single.png")
#print(p_out)
#dev.off()

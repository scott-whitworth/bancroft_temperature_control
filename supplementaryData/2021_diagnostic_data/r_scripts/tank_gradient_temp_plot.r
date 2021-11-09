library(rgl) 
# load in the rgl library

# https://www.r-graph-gallery.com/3-r-animated-cube.html
# https://cran.r-project.org/web/packages/rgl/vignettes/rgl.html#primitive-shapes
# http://www.sthda.com/english/wiki/a-complete-guide-to-3d-visualization-device-system-in-r-r-software-and-data-visualization#start-and-close-rgl-device


# TIME STAMP WARRNING:
# This assumes a June to July time stamp overstep!
# If the months are different you will need to modify calc_norm_time to handle a non-30 day time roll over

# Tank information:
# tank 4 -> control
# Five sticks - front left, front right, back left, back right, center

# Front Left - middle: 1
# Front Right - top: 8, bottom: 7
# back left - top: 6, bottom 5
# back right - middle 3
# center - top 9, middle 2

# water depth: 19cm
# probe spacing: wide: 28cm, depth 13cm, height 15cm
# Full water

fl_mid_probe <- 1
fr_top_probe <- 8
fr_bot_probe <- 7
bl_top_probe <- 6
bl_bot_probe <- 5
br_mid_probe <- 3
md_top_probe <- 9
md_mid_probe <- 2
control_probe <- 4

#3D Coordinates in cm, assuming right hand rule (0,0,0 back left bottom to 13,28,15 front right top)
probe_locations <- matrix(list(), nrow = 9)
probe_locations[[1]] <- c( 13, 0 , 7.5 ) #1
probe_locations[[2]] <- c( 6.5, 14, 7.5) #2
probe_locations[[3]] <- c( 0, 28, 7.5 ) #3
probe_locations[[4]] <- c( 13, 0, 0) #4 (this is approximate)
probe_locations[[5]] <- c( 0, 0, 0) #5
probe_locations[[6]] <- c( 0, 0, 15) #6
probe_locations[[7]] <- c( 13, 28, 0) #7
probe_locations[[8]] <- c( 13, 28, 15) #8
probe_locations[[9]] <- c( 6.5, 14, 15)  #9

x_dim = 13
y_dim = 28
z_dim = 15

# 9 tanks, full water, cold to hot
file <- 'C:/Users/Scooter/Desktop/WU/Summer/2021_temp_Data/raw_data/pbf_2021_7_22_gradient_cold_to_hot_full_tank.csv'
file_prefix <- "gradient_c2h_"
plot_title <- "Heating Temperature Profile, Gradient"
plot_sub <- expression('full water level, from ambient temp to set_temp = 40'*degree*'C')
time_max <- 1080
temp_max <- 35.0
temp_min <- 10.0


#Set up temp data points
probe_locations[[1]][1]

data_points <- data.frame(x = 0.0, y = 0.0, z = 0.0) #Get it started
for(t in 1:length(probe_locations)){
    data_points[nrow(data_points) + 1,] = probe_locations[[t]]
}
data_points <- data_points[-c(1),] #Remove starting line

#Set up visual boundaries
outterSurface <- data.frame(x=0,y=0,z=0)
outterSurface[nrow(outterSurface) + 1,] = c(13,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,0,15) #Triangle one (left, bottom)
outterSurface[nrow(outterSurface) + 1,] = c(0,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,0,15)
outterSurface[nrow(outterSurface) + 1,] = c(0,0,15) #Triangle two (left, top)

outterSurface[nrow(outterSurface) + 1,] = c(0,28,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,15) #Triangle three (right, bottom)
outterSurface[nrow(outterSurface) + 1,] = c(0,28,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,15)
outterSurface[nrow(outterSurface) + 1,] = c(0,28,15) #Triangle four (right, top)

outterSurface[nrow(outterSurface) + 1,] = c(0,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(0,28,0)
outterSurface[nrow(outterSurface) + 1,] = c(0,28,15) #Triangle five (back, bottom)
outterSurface[nrow(outterSurface) + 1,] = c(0,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(0,28,15)
outterSurface[nrow(outterSurface) + 1,] = c(0,0,15) #Triangle six (back, top)

outterSurface[nrow(outterSurface) + 1,] = c(13,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,15) #Triangle seven (front, bottom)
outterSurface[nrow(outterSurface) + 1,] = c(13,0,0)
outterSurface[nrow(outterSurface) + 1,] = c(13,28,15)
outterSurface[nrow(outterSurface) + 1,] = c(13,0,15) #Triangle eight (front, top)

bottomSurface <- data.frame(x=0,y=0,z=0)
bottomSurface[nrow(bottomSurface) + 1,] = c(13,28,0)
bottomSurface[nrow(bottomSurface) + 1,] = c(0,28,0) #Triangle one 
bottomSurface[nrow(bottomSurface) + 1,] = c(0,0,0)
bottomSurface[nrow(bottomSurface) + 1,] = c(13,0,0)
bottomSurface[nrow(bottomSurface) + 1,] = c(13,28,0) #Triangle two

#Set up temp samples 
#TODO: I guess we could make this smaller resolution based on a resolution value
point_resolution = 1 #Points separated by 2 cm
sample_points = data.frame(x=0,y=0,z=0,temp=10.0)

for(x in seq(from=0, by=point_resolution, to=x_dim)){
    for(y in seq(from=0, by=point_resolution, to=y_dim)){
        for(z in seq(from=0, by=point_resolution, to=z_dim)){
            sample_points[nrow(sample_points) + 1,] = c(x,y,z,(y/y_dim)*(temp_max-temp_min) + temp_min ) #Make a new point
        }
    }
}

distance <- function(p1, p2){
    #val1 = p1[1] * p2[1]
    return( sqrt(
        (p2[1]-p1[1])^2 +  
        (p2[2]-p1[2])^2 +
        (p2[3]-p1[3])^2
        ))
}

####
# Calculate interpolation from a set of temp points to sample_points
# this is done via finding the 'closest' four points and interpolating the temp from those three points
# frame_temp is 9 sets of temperature data, this should be what is used to figure out the individual points
#     this should be called with a new set of frame_temps per data point
# TODO: the closest points could be calculated ahead of time for efficiencies sake, this is going to be non-optimal
# TODO: I changed this, I am just taking a weight based off of distances to all points

calc_sample_points <- function(sample_points, frame_temp){
    #touch every point in sample_points
    for(p in 1:nrow(sample_points)){
        #Interpolate the value from the shortest points
        
        #Calculate all the paths
        curP_distance = array(dim=9) #holding array
        for(t in 1:length(curP_distance)){
            #Collect each distance from point p to all 9 probe locations
            curP_distance[t] = distance(sample_points[p,1:3],probe_locations[[t]])
        }
        
        #Find_longest/shortest (that will give the scale) all the shortest paths
        curP_rank = array(dim=9)
        for(i in 1:length(curP_rank)){
            
        }
        
        
    }
    return(sample_points)
}

####

#Testing temp_frame, eventually this will be read from a file
temp_frame = c(17.56, 17.56, 17.62, 15.56, 15.68, 17.87, 15.68, 17.81, 17.5)

sample_points = calc_sample_points(sample_points,temp_frame)

# Color helper
# Converts temp to color
# cur_temp is linearly interpolated between min_temp (cold) and max_temp (hot
temp_to_color <- function(cur_temp,min_temp,max_temp){
    hot_color = c(0,0,1.0,1.0)
    cold_color = c(1.0,0,0,1.0)
    
    scale = (cur_temp - min_temp) / (max_temp - min_temp)
    
    out_red = (hot_color[1] * (1-scale)) + (cold_color[1] * scale)
    out_green = (hot_color[2] * (1-scale)) + (cold_color[2] * scale)
    out_blue = (hot_color[3] * (1-scale)) + (cold_color[3] * scale)
    out_alpha = (hot_color[4] * (1-scale)) + (cold_color[4] * scale)
    
    return(rgb(red=out_red, green=out_green, blue=out_blue, alpha=out_alpha))
} 


open3d()
par3d(windowRect = c(-1500,200,-500,1100))
#Probe locations
plot3d(data_points$x, data_points$y, data_points$z,
       size=5,
       xlab='x', ylab='y', zlab='z',
       #xlim =c(0,13), ylim=c(0,28), zlim = c(0,15),
       axes=FALSE, #Turns off axis
       aspect=c(13,28,15) #Set the aspect ratio of each of the axes to be the max
       )
points3d(sample_points$x, sample_points$y, sample_points$z,
         size = 4, color = temp_to_color(sample_points$temp,temp_min,temp_max),
         alpha = 0.75, fog = FALSE
         )

#Side and bottoms of tank
triangles3d(outterSurface$x, outterSurface$y, outterSurface$z, alpha = 0.5, color = 'lightblue' )
triangles3d(bottomSurface$x, bottomSurface$y, bottomSurface$z, alpha = 0.5, color = 'black' )
#axes3d(edges = "bbox", labels=FALSE, tick = FALSE, box = FALSE)
#title3d('Top','Sub top','x is nothing', 'y is here', '')


#cat("Press [enter]")
#a <- readLines("stdin",n=1);

#Test 3d plot first!
q()

#tank_nums <- 73:81 #There should be nine tanks in the file, this keeps their indices organized
#xlim_max <- time_max

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


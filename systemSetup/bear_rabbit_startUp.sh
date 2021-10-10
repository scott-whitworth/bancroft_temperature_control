#!/bin/sh
echo "Running bear_rabbit_startUP"
echo "In theory, should start up rabbitMQ-server, then start up bear_trap.py"
#/usr/lib/rabbitmq/bin/rabbitmq-server
#/usr/bin/screen -dmS startUp_rabbitMQ /usr/lib/rabbitmq/bin/rabbitmq-server
#/usr/bin/screen -dmS startUpBancroft_bear /usr/bin/python /home/<user>/bancroft-lab-shia/pythonCode/bear_trap.py /home/<user>/bancroft-lab-shia/runtimeConfig.txt

#Check to see if rabbitmqctl server is up and running (ready to accept connections)
#if not try to start the application or start the server
while ! sudo rabbitmqctl status | grep -q "os_mon"; do
	#echo "RabbitMQ is not Running!"
        #Check to see if application is stopped, try to reset
        if sudo rabbitmqctl status | grep -q "running_applications"; then
                echo "Application has started, but is currently stopped! Trying to start up"
		sudo rabbitmqctl start_app #Attempt to force application to start
		sleep 1
        else
                echo "Application never started, cannot connect to server"
		/usr/bin/screen -dmS startUp_rabbitMQ /usr/bin/sudo /usr/sbin/rabbitmq-server
		sleep 2
        fi

	sleep 1 #delay just a little bit to let the system work
done

echo "RabbitMQ is Running!"
echo "Need to start bear_trap.py"

/usr/bin/screen -dmS startUpBancroft_bear /usr/bin/python /home/<user>/bancroft-lab-shia/pythonCode/bear_trap.py /home/<user>/bancroft-lab-shia/runtimeConfig.txt

echo "Done!"

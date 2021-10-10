## How to set up the start up behavior

Based on:  
* https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/
* https://superuser.com/questions/1276775/systemd-service-python-script-inside-screen-on-boot

At the moment:  
bancroft.service is in /lib/systemd/system/

chmod needs to be run on bancroft.service

systemctl needs to reload daemon and enable bancroft.service

**Important** We need to test the timing of everything. At the moment there is a 30 second delay to let RabbitMQ fully load (and maybe other things) before starting the script. We may want to make a script that runs continuously if the python fails for whatever reason.

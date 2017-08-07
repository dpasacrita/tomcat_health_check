TOMCAT HEALTH CHECKER

Author: dpasacrita

Function: This project is meant to be ran as a service on a server running apache and tomcat together. The service will periodically check the given URL to make sure apache is still correctly serving content. If it is not, it will run the tomcat restart script to restart tomcat and resume checking.


Setup: It's recommended to set up the python script as a service and let it run. You could also run it via command line and disconnecting from the screen, but that's clunky and I wouldn't recommend it.

I'd place both the py script and the sh script in /usr/sbin/ and set up py as a service. Place the cfg file in /etc/ and point the script at it.

It goes without saying that this only works on Linux. I'd also only run this as root.


Configuration:

The cfg file is pretty self explanatory, but the options will be listed here.

[Server]
Host: The host the script is looking at. It can check a remote server, but the restart won't work, so I wouldn't recommend it.
HTTP URL: The URL the script will be checking. Make sure to start with a / 

[Polling]
Poll Seconds: How many seconds in between each check.
Alert Count: How many times the service will detect an issue before it will alert about a problem.
Restart Count: How many times before it performs the restart.
Response Time Threshold: How many seconds the script will wait before it decides it can't see the URL.

[Email]
To Email: Email that alerts are sent to.
From Email: Email that alerts are sent from.
smtp Server: Server the script uses to email.


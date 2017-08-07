#!/bin/bash
# Tomcat Restart
# This script is used by the tomcat_health_checker script to restart tomcat when it has crashed.

# Load bash profile
. ~/.bash_profile

# Determine PWD, and time.
WORK_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/"
TOMCAT_DIRECTORY="/opt/tomcat/"
LOG_DIRECTORY="/var/log/"
LOG_FILE="tomcat_restart.log"
CURRENT_DATE=$(date)
TOMCAT_USER="user"

# Determine PID of tomcat
tomcat_pid="$(ps aux | grep '[t]omcat' | awk '{print $2}')"
# ERROR HANDLING - If failure, start tomcat
if [ -n "$tomcat_pid" ]
then
    # Success, keep moving through the script, as this means tomcat is running.
    printf "[$CURRENT_DATE] - Successfully retrieved tomcat pid.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
else
    printf "[$CURRENT_DATE] - ERROR: Did not successfully retreive pid! Tomcat might not be running\n" >&2 >> "$LOG_DIRECTORY""$LOG_FILE"
    # Start Tomcat
    printf "[$CURRENT_DATE] - Starting tomcat...\n" >> "$LOG_DIRECTORY""$LOG_FILE"
    su -c ''"$TOMCAT_DIRECTORY"'bin/startup.sh' storefront >> "$LOG_DIRECTORY""$LOG_FILE"
    # ERROR HANDLING
    if [ $? -eq 0 ]
    then
        # Say that it successfully restarted, and exit
	printf "[$CURRENT_DATE] - Tomcat has been restarted.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
        exit 0
    else
	# Print another Error and just give up already.
        printf "[$CURRENT_DATE] - ERROR: Failed to start tomcat! Shutting down.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
	exit 1
    fi
fi


# Restart tomcat
printf "[$CURRENT_DATE] - Killing tomcat...\n" >> "$LOG_DIRECTORY""$LOG_FILE"
kill -9 "$tomcat_pid" >> "$LOG_DIRECTORY""$LOG_FILE"
# ERROR HANDLING
if [ $? -eq 0 ]
then
    printf "[$CURRENT_DATE] - Tomcat process has been killed.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
else
    printf "[$CURRENT_DATE] - ERROR: Failed to kill tomcat process!\n" >> "$LOG_DIRECTORY""$LOG_FILE"
    exit 1
fi
# Run tomcat as storefront
su -c ''"$TOMCAT_DIRECTORY"'bin/startup.sh' $TOMCAT_USER >> "$LOG_DIRECTORY""$LOG_FILE"
# ERROR HANDLING
if [ $? -eq 0 ]
then
    # Say that it successfully restarted, and exit
    printf "[$CURRENT_DATE] - Tomcat has been restarted.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
    exit 0
else
    # Print another Error and just give up already.
    printf "[$CURRENT_DATE] - ERROR: Failed to start tomcat! Shutting down.\n" >> "$LOG_DIRECTORY""$LOG_FILE"
    exit 1
fi


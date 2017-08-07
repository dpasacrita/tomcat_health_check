#!/usr/bin/python3.5
import sys, os, re
import time, signal, smtplib
import datetime
import requests
import configparser
import subprocess

# Globals
# Some of these can be set in the config file which will override these
config_file        = "/etc/tomcat_health_checker.cfg"
checker_log_file     = "/var/log/tomcatMonitor.log"
logList            = []
poll_seconds        = 60
alert_email         = "to@mail.com"
from_email          = "from@Mail.com"
smtp_server         = "smtp.mail.com"
host               = ""
http_url          = ""
alert_count        = 2
restart_count      = 3
response_time_threshold = 7.5
restart_script     = "/usr/sbin/tomcat_restart.sh"

class TomcatMonitor:
    # Initialize class object and register vars
    def __init__(self,):

        # Base Values for object
        today = datetime.date.today()
        #self.logFileName = logFileName
        #self.cLogFileName = self.logFileName % (today,)
        #self.logName = logName
        #self.regEx = []
        #self.lastReport = 0
        #self.reportTimeout = reportTimeout
        #self.requestCache = {}
        #self.errorLogs = ""
        #self.logFile = None
        self.complete_url = ""
        self.current_count = 0
        self.last_restart = 0

        # construct complete_url variable
        self.complete_url = "http://" + host "/" + http_url

    def health_check(self):

        start_time = time.time()
        try:
            response = requests.head(self.complete_url)
        except requests.ConnectionError:
            logit("ERROR: Failed to connect! Check Apache")
            # Can add code here to restart apache remotely
            sys.exit()
        total_time = float('{0:.3g}'.format(time.time() - start_time))
        # print(response.status_code)
        # print("Took %s seconds" % total_time)
        # This should try it a couple times, and restart if it doesn't work.
        if response.status_code != 200 or total_time > response_time_threshold:
            self.current_count += 1
            logit("PROBLEM!!! Raising Count to %s" % self.current_count)
        if self.current_count == alert_count:
            logit("Count is now at %s, send an alert, one more to restart" % self.current_count)
            if (time.time()-self.last_restart) <= 1800:
                logit("Last restart was within 30 minutes. Suppressing Alert.")
            else:
                message = host + ": " + "Count is now at %s! One more to Restart!" % self.current_count
                send_message(alert_email, from_email, "Alert Threshold reached on " + host, message, smtp_server)
        elif self.current_count == restart_count:
            logit("Count is now 4 or greater, sending alert and restarting")
            if (time.time()-self.last_restart) <= 1800:
                logit("Last restart was within 30 minutes. Suppressing Alert.")
            else:
                message = host + ": " + "Count is now at %s! Restarting Tomcat and resetting count." % self.current_count
                send_message(alert_email, from_email, "Restart Threshold reached on " + host, message, smtp_server)
            self.last_restart = time.time()
            logit("Restarting now...")
            try:
                subprocess.call(restart_script)
                logit("Restarted.")
            except FileNotFoundError:
                logit("File not found! With no restart script this script is pointless. Quitting.")
                sys.exit(1)
            self.current_count = 0
        elif self.current_count > restart_count:
            logit("ERROR: Count greater than restart threshold, restart must have failed. Quitting.")
            sys.exit(1)
        elif self.current_count < 0:
            logit("ERROR: Invalid count number! Something went terribly wrong here.")
            sys.exit(1)


def get_config(config):

    # Declare Globals
    global host
    global http_url
    global poll_seconds
    global alert_count
    global restart_count
    global response_time_threshold
    global alert_email
    global from_email
    global smtp_server

    # Load Configuration File
    # First check if file exists
    if not os.path.isfile(config):
        logit("ERROR: Config file not found!")
        sys.exit(1)
    # Now load the file
    configuration = configparser.ConfigParser()
    configuration.read(config)

    # Server Config
    try:
        options = configuration.options("Server")
        # Get host value
        try:
            host = configuration.get("Server", options[options.index("host")])
        except ValueError:
            logit("ERROR: Host is not properly defined! Quitting.")
            sys.exit(1)
        # Get HTTP URL Value
        try:
            http_url = configuration.get("Server", options[options.index("http url")])
        except ValueError:
            logit("ERROR: HTTP URL is not properly defined! Quitting.")
            sys.exit(1)
    except configparser.NoSectionError:
        logit("ERROR: No Server configuration found in file! Quitting.")
        sys.exit(1)

    # Polling Config
    try:
        options = configuration.options("Polling")
        # Get poll seconds value
        try:
            poll_seconds = int(configuration.get("Polling", options[options.index("poll seconds")]))
        except ValueError:
            logit("WARNING: Poll Seconds not properly defined. Using default of 60.")
        # Get Alert Count value
        try:
            alert_count = int(configuration.get("Polling", options[options.index("alert count")]))
        except ValueError:
            logit("WARNING: Alert Count not properly defined. Using default of 3.")
        # Get Restart Count value
        try:
            restart_count = int(configuration.get("Polling", options[options.index("restart count")]))
        except ValueError:
            logit("WARNING: Restart Count not properly defined. Using default of 4.")
        # Get Response Time Threshold
        try:
            response_time_threshold = float(configuration.get("Polling", options[options.index("response time threshold")]))
        except ValueError:
            logit("WARNING: Response Time Threshold not properly defined. Using default of 7.5.")
    # If no polling settings are found, print a warning but keep going. Default values will be used.
    except configparser.NoSectionError:
        logit("WARNING: Polling configuration not present. Using default values.")

    # Email Config
    try:
        options = configuration.options("Email")
        # Get alert Email value
        try:
            alert_email = configuration.get("Email", options[options.index("to email")])
        except ValueError:
            logit("WARNING: Alert Email not properly defined. Using default of to@mail.com.")
        # Get From Email value
        try:
            from_email = configuration.get("Email", options[options.index("from email")])
        except ValueError:
            logit("WARNING: From Email not properly defined. Using default of from@mail.com.")
        # Get smtp Server value
        try:
            smtp_server = configuration.get("Email", options[options.index("smtp server")])
        except ValueError:
            logit("WARNING: SMTP Server not properly defined. Using default of smtp.mail.com.")
    except configparser.NoSectionError:
        logit("WARNING: Email configuration not present. Using default values.")

    # Verify values; some combinations would be impossible
    if restart_count <= alert_count:
        logit("ERROR: Restart count must be higher than alert count! Quitting.")
        sys.exit(1)
    if poll_seconds <= 0 or alert_count <= 0 or restart_count <= 0 or response_time_threshold <= 0:
        logit("ERROR: Config file has one or more important values as 0 or less!\n"
              "Why would you even try that?? Quitting.")
        sys.exit(1)

def send_message(mailto, mailfrom, subject, message, smtpserver):
    try:
        server = smtplib.SMTP(smtpserver)
    except:
        #logit("Error: Failed to connect to SMTP server: (" + smtpserver + ")")
        logit("Error: Failed to connect to SMTP server: (" + smtpserver + ")")
        return
    # Prepare the message
    mesg = """To: %s\r\nFrom: %s\r\nSubject: %s\r\n\r\n%s""" % (mailto, mailfrom, subject, message)
    # Send the message
    try:
        server.sendmail(mailfrom, mailto, mesg)
    except:
        logit("Error: Failed to connect to SMTP server: (" + smtpserver + ")")


def logit(data):
    global checker_log_file
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        log_file = open(checker_log_file, "a")
    except:
        return
        # Fire email warning about cannot log to disk
    try:
        log_file.write(cur_time + " -- " + data + "\n")
    except:
        return
        # Email warning about can't write to logfile
    log_file.close()

if __name__ == "__main__":

    #logit("Starting up...")
    get_config(config_file)

    logList.append(TomcatMonitor())
    while(1):
        for checks in logList:
            checks.health_check()
        time.sleep(poll_seconds)

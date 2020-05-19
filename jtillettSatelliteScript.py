# This script reads in reports from the file referenced, parses them using the csv library
# then uses several if comparisons to determine whether or not a report falls within
# a given alert status. If enough alerts are reached within a 5-minute period, a dict
# is generated with the current alert status. All dicts are converted into a json and
# printed before the end of the script.
#
# With some minor adjustments, this could be converted to something that monitors an incoming
# stream and posts alerts to a webhook in a slack instance or sends an email to an alert address.

from datetime import datetime #Importing datetime for math and .strftime method
import csv #Importing csv to interpret dataset
import json #Importing json to transform dataset prior to printing


class Satillite: #Class used to cut code clutter on time tracking variables.
    def __init__(self, satNum):
        self.satNo = satNum
        self.tempTime1 = datetime(1900, 1, 1) # Dates are instantiated to 1/1/1900. Since every report doesn't result in an alert, you can't reliably instantiate these with report dates.
        self.tempTime2 = datetime(1900, 1, 1) # Given the sample data set, it is assumed that all dates come in order. As a result, we can use old dates
        self.battTime1 = datetime(1900, 1, 1) # since and be confident that they'll be phased out as new alerts come in.
        self.battTime2 = datetime(1900, 1, 1)
        
    def timeCheck(self, newTime, condition): #Method used to compare times and decide whether an alert needs to be triggered.
        if condition == "BATT": #Each satellite has two potential failure points. This if statement determines which two time variables to use.
            delta1 = (newTime - self.battTime1) #Delta times are used for comparison each time the method is called
            delta2 = (newTime - self.battTime2)
            seconds1 = delta1.total_seconds() #seconds variables are used for numerical comparisons.
            seconds2 = delta2.total_seconds() #.totalseconds() is used to convert a date to an integer
            if seconds2 < 300: # Checks if within 5 minutes of second alert
                if seconds1 < 300: #Check if within 5 minutes of first alert
                    self.battTime1 = self.battTime2
                    self.battTime2 = newTime
                    return 2 #Triggers battery alert
                
            self.battTime1 = self.battTime2 #Iterates times up a position if alert isn't triggered
            self.battTime2 = newTime
            return 0 #Returns no alert
        
        else: #Repeat of above code using temperature time variables
            delta1 = (newTime - self.tempTime1)
            delta2 = (newTime - self.tempTime2)
            seconds1 = delta1.total_seconds()
            seconds2 = delta2.total_seconds()
            if seconds2 < 300:
                if seconds1 < 300:
                    return 1 #Triggers temperature alert
              
            self.tempTime1 = self.tempTime2
            self.tempTime2 = newTime
            return 0 #Returns no alert


sat1 = Satillite(1000) # Instantiated satellite objects. You could possibly swap these with a list of dynamic objects generated from unique satelliteIds
sat2 = Satillite(1001) # That would allow you to cut down on the amount of if comparisons in the loop below.
alertList = [] #Alert list used to compile dictionaries for json

with open('variable.txt', 'r') as f:
  csv_reader = csv.reader(f, delimiter='|')
  for row in csv_reader:
      dateVar = datetime.strptime(row[0], '%Y%m%d %H:%M:%S.%f') #This line and the following 6 pull each value from the current row of the csv
      satNo = row[1]
      redHigh = float(row[2]) #Floated value for comparison of reading value against ranges given by report
      yellowHigh = float(row[3])
      yellowLow = float(row[4])
      redLow = float(row[5])
      readingValue = float(row[6])
      component = row[7]
      alert = 0 #Tracks alert status. 0 is "Good", 1 is "TSTAT", 2 is "BATT"
      
      if satNo == "1000" and component == "TSTAT": #If comparisons test specifically for satellite ID and component type before throwing alert to satellite object
          if readingValue > redHigh:
              alert = sat1.timeCheck(dateVar, component) #alert is set depending on value given by the method

      if satNo == "1001" and component == "TSTAT":
          if readingValue > redHigh:
              alert = sat2.timeCheck(dateVar, component)

      if satNo == "1000" and component == "BATT":
          if readingValue < redLow:
              alert = sat1.timeCheck(dateVar, component)
              
      if satNo == "1001" and component == "BATT":
          if readingValue < redLow:
              alert = sat2.timeCheck(dateVar, component)
    
      if alert == 1: #If comparisons check alert value, trigger alarm generation. 1 is Temperature
          dateString = dateVar.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
          dateString = dateString + "Z"
          alertList.append({"satelliteId": satNo, "severity": "RED HIGH", "component": component, "timestamp": dateString})
      if alert == 2: #If comparisons check alert value, trigger alarm generation. 2 is Battery
          dateString = dateVar.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
          dateString = dateString + "Z"
          alertList.append({"satelliteId": satNo, "severity": "RED LOW", "component": component, "timestamp": dateString})
          

alertJson = json.dumps(alertList) #Creates json of any alerts generated in for loop
print(alertJson) #prints json to console. Could easily save to file or post elsewhere via API call with minor adjustments.
exit() #exits script
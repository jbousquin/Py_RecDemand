import os
import urllib
import time
import csv
from xml.etree.ElementTree import XML, fromstring, tostring
#####USER PARAMETERS#####
path = r"L:\Public\jbousqui\AED\GIS\Cape\NE_Block_groups"

fromFile = path + os.sep + "O-D_table.csv" #csv with: ID, Origin, Destination
ResultFile = ".txt" #whatever we want it to be
#########################

with open(fromFile, 'r') as f:
	reader = csv.reader(f)
	OD_Lst = list(reader)
	#OD_Lst: [['ID_0', 'Origin_0_Lat', 'Origin_0_Long', 'Destination_0_Lat', 'Destination_0_Long'],
	#        ['ID_1', 'Origin_1_Lat', 'Origin_1_Long', 'Destination_1_Lat', 'Destination_1_Long']]
f.close()

outType = "xml" #simplejson is not in 10.3 arcpy stack
units = "imperial"
durationLst=[]
distanceLst=[]

for pair in range(0, len(OD_Lst)):
        ID=str(OD_Lst[pair][0])
        origin= str(OD_Lst[pair][1]) + "," +str(OD_Lst[pair][2])
        destination= str(OD_Lst[pair][3]) + "," +str(OD_Lst[pair][4])

        googleTxt = "https://maps.googleapis.com/maps/api/distancematrix/" + outType + "?units=" + units + "&origins=" + origin + "&destinations=" + destination

        #run it
        xmlfile = urllib.urlopen(googleTxt)
        xml = xmlfile.read()
        value = "NA"
        dom = fromstring(xml)
        nodelist = dom.getchildren()
        if (nodelist[0].text == "OK"):
                print("Found Addresses from gps for ID#" + ID)
                #nodelist[1].text = origin_address
                #nodelist[2].text = destination_address
                element = nodelist[3].getchildren()[0] #row
                status = element.getchildren()[0]
                if (status.text == "OK"):
                        print("Calculated Distance")
                        if element[1].tag == 'duration':
                                duration = element[1]
                                print("Travel time for ID" + ID + " : " + duration[1].text)
                                durationLst.append(duration[0].text)
                        else:
                                print("Something in the xml (duration) is off")
                        if element[2].tag == 'distance':
                                distance = element[2]
                                print("Travel distance for ID" + ID + ": " + distance[1].text)
                                distanceLst.append(distance[0].text)
                        else:
                                print("Something in the xml (distance) is off")
                else:
                        print("Could not calculate distance/time, check 'status'")
        else:
                print("Could not find address from gps, check 'status'")
                
#sepChar = "|"
#To do:
#create csv of Origin-Destination lat/long using arcpy

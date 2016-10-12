"""Reassembled Open Street Map Routing OSRM Script
# Author: Nate Merrill, Justin Bousquin
# Project: Cape Cod Recreational Demand for NE block groups
#This creates the OD matrix with Open Street Map Routing OSRM
"""
import sys, os
from __future__ import division
import requests #may not need
import arcpy
from arcpy import env
from arcpy import da
import numpy as np
#JJB added
from urllib2 import urlopen
import json

#from OSRM new
class DefaultRequestConfig:
    def __init__(self):
        self.host = "http://localhost:5000"
        self.profile = "driving"
        self.version = "v1"

    def __str__(self):
        return("/".join([self.host, '*', self.version, self.profile]))

    def __repr__(self):
        return("/".join([self.host, '*', self.version, self.profile]))

    @staticmethod
    def __call__(addr=None):
        if not addr:
            return DefaultRequestConfig()
        else:
            tmp = addr.split('/')
            cla = DefaultRequestConfig()
            cla.host = tmp[0]
            i = len(tmp)
            cla.version = tmp[i-2]
            cla.profile = tmp[i-1]
            return cla

#shouldn't need this, but good error handling
def check_host(host):
    """ Helper function to get the hostname in desired format """
    if not ('http' in host and '//' in host) and host[len(host)-1] == '/':
        return ''.join(['http://', host[:len(host)-1]])
    elif not ('http' in host and '//' in host):
        return ''.join(['http://', host])
    elif host[len(host)-1] == '/':
        return host[:len(host)-1]
    else:
        return host
def exec_time(start, message):
    end = time.clock()
    comp_time = (end - start)/60
    print("Run time for " + message + ": " + str(comp_time) + " min")
    start = time.clock()
    return start

"""Work in progress"""
def simplest_route(coord_origin, coord_dest, alt=False,
                    output='raw', url_config=RequestConfig, host='http://localhost:5000'):
    coords = "{},{};{},{}".format(coord_origin[0], coord_origin[1], coord_dest[0], coord_dest[1])
    #format coord_origin and coord_dest: "13.388860,52.517037;13.397634,52.529407;13.428555,52.523219"
    url = ["{}/route/{}/{}/{}?overview=false".format(host, url_config.version, url_config.profile, coords)]
    return url

def ping(url):
    #should just use urllib2 (or urllib)
    r = urlopen("".join(url))
    r_json = json.loads(r.read().decode('utf-8'))
    if "code" not in r_json or "Ok" not in r_json["code"]:
        if 'matchings' in r_json.keys():
            for i, _ in enumerate(r_json['matchings']):
                geom_encoded = r_json["matchings"][i]["geometry"]
                geom_decoded = [[point[1] / 10.0,
                                 point[0] / 10.0] for point
                                in PolylineCodec().decode(geom_encoded)]
                r_json["matchings"][i]["geometry"] = geom_decoded
        else:
            print('No matching geometry to decode')
            #raise ValueError(
            #    'Error - OSRM status : {} \n Full json reponse : {}'.format(
            #        parsed_json['code'], parsed_json))
            #print rather than fail
            print("'Error - JSON status: {} \n Full json reponse: {}'.format(r_json['code'], r_json))"
    else:    
        return r_json

#####USER SPECIFIED#####
workspace=r"L:\Public\jbousqui\AED\GIS\Cape\Tool_Test" #L drive
agents="agents3.shp"
destinations="destination3.shp"

#####MAIN#####
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

RequestConfig = DefaultRequestConfig()

#origins
ac = arcpy.GetCount_management(agents)
ac = int(ac.getOutput(0)) #can we combine to 1 line?

agent_latlon=np.ones((ac,2)) #not familiar w/ np.ones
agent_list_id=np.ones((ac,1))

i=0 #could alternatively create a list and append
for row in arcpy.da.SearchCursor(agents,["SHAPE@XY","FID"]):
    agent_latlon[i]=row[0]
    agent_list_id[i]=row[1]
    i=i+1

#destinations
dc=arcpy.GetCount_management(destinations)
dc = int(dc.getOutput(0))
dest_latlon=np.ones((dc,2))
dest_list_id=np.ones((ac,1))

i=0
for row in arcpy.da.SearchCursor(destinations,["SHAPE@XY","OBJECTID"]):
    dest_latlon[i]=row[0]
    dest_list_id[i]=row[1]
    i=i+1

#build in loop
#for i in len(agent_latlon)
i = 0
#create url (indent when loop is active)
route_url = simplest_route(agent_latlon[i],dest_latlon[i], output='raw',host='http://localhost:5000')
route = ping(route_url)

distance = route["routes"][0]["distance"]
duration =  route["routes"][0]["duration"]

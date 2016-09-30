'''This tool creates a table of travel time for origins and destination using ArcGIS Online routing services
Function adapted from http://esriurl.com/uc16napy
Date: 8/23/2016
Version 0.0.13
Notes: Trying to not break it. Added Param for start position.
'''
import arcpy
import os
import sys
import time

"""
#Global Timer
#Funct Notes: used during testing to compare efficiency of each step
"""
def exec_time(start, message):
    end = time.clock()
    comp_time = end - start
    arcpy.AddMessage("Run time for " + message + ": " + str(comp_time))
    start = time.clock()
    return start

"""Set Input Parameter
Purpose: returns arcpy.Parameter for provided string, setting defaults for missing."""
def setParam(str1, str2, str3, str4, str5):
    lst = [str1, str2, str3, str4, str5]
    defLst = ["Input", "name", "GpFeatureLayer", "Required", "Input"]
    i = 0
    for str_ in lst:
        if str_ =="":
            lst[i]=defLst[i]
        i+=1       
    return arcpy.Parameter(
        displayName = lst[0],
        name = lst[1],
        datatype = lst[2],
        parameterType = lst[3],
        direction = lst[4])

"""Exceeds 200 Warning
Purpose: provide message and how many runs it will take when an input has more than 200 points"""
def exceed_200_warn(num, string):
    arcpy.AddMessage("There were {} {}. They must be separated into {} tables.".format(str(num), string, str(math.ceil(int(num)/200.0))))
    print("There were {} {}. They must be separated into {} tables.".format(str(num), string, str(math.ceil(int(num)/200.0))))

    return int(math.ceil(int(num)/200.0))

"""Import Service
Purpose:"""
def import_service(service_name, username="", password="", ags_connection_file="", token="", referer=""):
    '''Imports the service toolbox based on the specified credentials and returns the toolbox object'''

    #Construct the connection string to import the service toolbox
    if username and password:
        tbx = "https://logistics.arcgis.com/arcgis/services;{0};{1};{2}".format(service_name, username, password)
    elif ags_connection_file:
        tbx = "{0};{1}".format(ags_connection_file, service_name)
    elif token and referer:
        tbx = "https://logistics.arcgis.com/arcgis/services;{0};token={1};{2}".format(service_name, token, referer)
    else:
        raise arcpy.ExecuteError("No valid option specified to connect to the {0} service".format(service_name))

    #Import the service toolbox
    tbx_alias = "agol"
    arcpy.ImportToolbox(tbx, tbx_alias)

    return getattr(arcpy, tbx_alias) 

def main(params):
    '''Program entry point'''
    start = time.clock() #start the clock
#script params:
#origin_in = 'blockpoints3_cape'
#destination_in ='Cape_Cod_Merged2'
#travel_modes = "'Driving Time';'Walking Time"
#time_of_day = "9/17/2016"
#time_zone = "Geographically Local"
#path = r"L:\Public\jbousqui\AED\GIS\Cape\TestResults.gdb"
    
    #define inputs
    origin_in = params[0].valueAsText
    destination_in = params[1].valueAsText
    #optional
    travel_modes = params[2].valueAsText
    time_of_day = params[3].valueAsText
    time_zone = params[4].valueAsText
    #output GDB
    path = params[5].valueAsText
    #derived
    travel_modes = map(lambda a: a.replace("'",""), travel_modes.split(';'))
    st = int(params[6].valueAsText) #start at run #

    #Get the name and version of the product used to run the script
    install_info = arcpy.GetInstallInfo()
    product_version = "{0} {1}".format(install_info["ProductName"], install_info["Version"])

    #Get the credentials from the signed in user and import the service
    #NOTE: Sign in through catalog- "ready to use services"
    service_name = "World/OriginDestinationCostMatrix"
    credentials = arcpy.GetSigninToken()
    if not credentials:
        raise arcpy.ExecuteError("Please sign into ArcGIS Online")
    token = credentials["token"]
    referer = credentials["referer"]
    service = import_service(service_name, token=token, referer=referer)

    #create gbd if it doesn't exist
    if not os.path.exists(path):
        arcpy.management.CreateFileGDB(os.path.dirname(path), os.path.basename(path))
    #intermediate names
    origin_FC = path + os.sep + "Origins_A"
    destination_FC = path + os.sep + "Destinations_A"
    
    #copy FC into GBD to make sure OBJECTID are sequential
    arcpy.CopyFeatures_management(origin_in, origin_FC)
    arcpy.CopyFeatures_management(destination_in, destination_FC)
    arcpy.AddMessage("origin_in: {} -> oring_FC: {}".format(origin_in, origin_FC))
    arcpy.MakeFeatureLayer_management(origin_FC, "Origin")
    arcpy.MakeFeatureLayer_management(destination_FC, "Destination")
    
    run_lst = []
    #check the number of origins (limit <200)
    numO = int(str(arcpy.GetCount_management(origin_FC)))
    numD = int(str(arcpy.GetCount_management(destination_FC)))
    #create a list of lists depending on how many sets of 200 in each
    if numO > 200:
        runsO = exceed_200_warn(numO, "origins") #features/200
        if numD > 200:
            runsD = exceed_200_warn(numD, "destinations")
            arcpy.AddMessage("With {} origin tables and {} destination tables, there will be {} runs.".format(runsO, runsD, runsO *runsD))
            print("With {} origin tables and {} destination tables, there will be {} runs.".format(runsO, runsD, runsO *runsD))
            for o in range(0, runsO):
                for d in range(0, runsD):
                    run_lst.append([[o],[d]]) #list of O sets x D sets
        else:
            for o in range(0, runsO):
                run_lst.append([[o], [0]]) #list of O sets x 1 D set
    else:
        if numD > 200:
            runsD = exceed_200_warn(numD, "destinations")
            for d in range(0, runsD):
                run_lst.append([[0],[d]]) #list of 1 O set x D sets
        else:
            run_lst = [[0],[0]]
    
    #objectid name for whereClause
    o_oid_name = arcpy.Describe(origin_FC).OIDFieldName
    d_oid_name = arcpy.Describe(destination_FC).OIDFieldName

    start=exec_time(start, "Parameters Initialized")
    
    i = st #iterator for naming, start at st (start run)
    for run in run_lst[st:]:
        #o_whereClause = '"OBJECTID" BETWEEN ' + str((run[0][0] * 200) + 1) + " AND " + str((run[0][0]*200) + 201)
        o_whereClause = '{0} >= {1} AND {0} <= {2}'.format('"'+ str(o_oid_name) + '"', str((run[0][0] * 200) + 1), str((run[0][0] * 200) + 200))
        d_whereClause = '{0} >= {1} AND {0} <= {2}'.format('"'+ str(d_oid_name) + '"', str((run[1][0] * 200) + 1), str((run[1][0] * 200) + 200))
        arcpy.AddMessage("Origin whereClause: " + o_whereClause)
        arcpy.AddMessage("Destination whereClause: " + d_whereClause)
        
        #select origin
        arcpy.SelectLayerByAttribute_management("Origin", "NEW_SELECTION", o_whereClause)
        arcpy.SelectLayerByAttribute_management("Destination", "NEW_SELECTION", d_whereClause)

        #Call the service for each travel mode, with the selection
        for mode in travel_modes:
            arcpy.AddMessage("Generating Matrix Table using '{}' travel mode with {} as the Origin and {} as the Destination"
                             .format(mode, origin_FC, destination_FC))
            #Get token again
            credentials = arcpy.GetSigninToken()
            token = credentials["token"]
            service = import_service(service_name, token=token, referer=referer)
            #WALKING TIME only available for <50miles
            #result = service.GenerateOriginDestinationCostMatrix("Origin", "Destination")
            result = service.GenerateOriginDestinationCostMatrix("Origin", "Destination", Travel_Mode = mode, Time_of_Day = time_of_day, Time_Zone_for_Time_of_Day = time_zone)
                  #(Origins, Destinations, {Travel_Mode}, {Time_Units}, {Distance_Units}, {Analysis_Region},
                  #{Number_of_Destinations_to_Find}, {Cutoff}, {Time_of_Day}, {Time_Zone_for_Time_of_Day},
                  #{Point_Barriers}, {Line_Barriers}, {Polygon_Barriers}, {UTurn_at_Junctions}, {Use_Hierarchy},
                  #{Restrictions;Restrictions...}, {Attribute_Parameter_Values}, {Impedance}, {Origin_Destination_Line_Shape})

            #Check the status of the result object every second until it has a value of 4(succeeded) or greater 
            while result.status < 4:
                time.sleep(1)#one second

            #print any warning or error messages returned from the tool
            result_severity = result.maxSeverity
            if result_severity == 2:
                arcpy.AddError(result.getMessages(2))
                raise arcpy.ExecuteError("An error occured when running the tool")
            elif result_severity == 1:
                arcpy.AddMessage("Warnings were returned when running the tool")
                arcpy.AddWarning(result.getMessages(1))

            #Get the output matrix table and save to a file geodatabase feature class.
            output_FC_name = u"Online_{}_{}".format(arcpy.ValidateTableName(mode, path), str(i))
            output_service_table = os.path.join(path, output_FC_name)
            if arcpy.Exists(output_service_table):
                arcpy.management.Delete(output_service_table)
            result.getOutput(1).save(output_service_table)
            runNum = "run #" + str(i)
            start=exec_time(start, runNum)
        i+=1
###########TOOLBOX############
class Toolbox(object):
    def __init__(self):
        self.label = "Generate Cost Matrices"
        self.alias = "Generate Cost Matrix"
        # List of tool classes associated with this toolbox
        self.tools= [Cost_Matrix]
class Cost_Matrix (object):
    def __init__(self):
        self.label = "Cost Matrix" 
        self.description = "This tool generates a travel network cost matrix given two sets of points"
        
    def getParameterInfo(self):
        origin_in = setParam("Origin", "origin_FC", "", "", "")
        destination_in = setParam("Destination", "dest_in", "", "", "")
        
        time_of_day = setParam("Travel Date & Time", "time_of_day", "GPDate", "Opttional", "")
        time_zone = setParam("Time Zone", "time_zone", "GPString", "Optional", "")
        st = setParam("Start Run", "start_run", "GPString", "Optional", "")
        outTbl = setParam("Results", "outTbl", "DEWorkspace", "", "Output")
        
        travel_modes =arcpy.Parameter(
            displayName = "Travel Modes",
            name = "travel_mode_lst",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = True)
        
        #value list
        travel_modes.filter.type = "ValueList"
        travel_modes.filter.list = ["Driving Time", "Walking Time", "Trucking Time", "Rural Driving Time"]
        #defaults
        travel_modes.value = "Driving Time"
        time_zone.value = "Geographically Local"
        st.value = "0"

        #default values to make debugging faster
        #origin_in.value = 'blockpoints3_cape'
        destination_in.value ='Cape_Cod_Merged2'
        time_of_day.value = "9/17/2016"
        outTbl.value = r"L:\Public\jbousqui\AED\GIS\Cape\TestResults.gdb"
        
        params = [origin_in, destination_in, travel_modes, time_of_day, time_zone, outTbl, st]
        return params
    def isLicensed(self):
        return True
    def updateParameters(self, params):
        return
    def updateMessages(self, params):
        return
    def execute(self, params, messages):
        main(params)
        try:
            main(params)
        except Exception as ex:
            arcpy.AddMessage(ex.message)
            print(ex.message)

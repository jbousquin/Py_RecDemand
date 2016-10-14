#https://developers.arcgis.com/rest/analysis/api-reference/programmatically-accessing-analysis-services.htm#ESRI_SECTION1_A034157421D148709C219BF3F8B7A61E
#arcpy.GetActivePortalURL()
'''CONNECT ORIGINS TO DESTINATIONS
Using ArcGIS Online Services
ArGIS Rest API: Spatial Analysis Service
Limits:
Origins layer - 5000 Feature
Desinations layer - 5000 Features
'''
import urllib
import urllib2
import httplib
import time
import json
import contextlib

###############
###FUNCTIONS###

def submit_request(request):
    """Returns the response from an HTTP request in json format."""
    with contextlib.closing(urllib2.urlopen(request)) as response:
        job_info = json.load(response)
        return job_info

def get_token(portal_url, username, password):
    """Returns an authentication token for use in ArcGIS Online"""
    #username and password are set and passed up to this function
    params = { "username": username,
               "password": password,
               "referer": "https://www.arcgis.com",
               #"https://www.arcgis.com"
               #"https://www.epa.maps.arcgis.com",
               #http://www.esri.com/AGO/9022B77D-7706-42A3-A1F3-EC1386E90F30
               "f": "json"}
    token_url = "{}/generateToken".format(portal_url)
    request = urllib2.Request(token_url, urllib.urlencode(params))
    token_response = submit_request(request)
    if "token" in token_response:
        print("Getting token...")
        token = token_response.get("token")
        return token
    else:
        #request for token must be made through HTTPS
        if "error" in token_response:
            error_mess = token_response.get("error", {}).get("message")
            #if "This request needs to be made over https." in error_mess:
            #    token_url = token_url.replace("http://", "https://")
            #    token = get_token(token_url, username, password)
            #    return token
        else:
            raise Exception("Portal error: {} ".format(error_mess))

def get_analysis_url(portal_url, token):
    "Returns Analysis URL from AGOL for running analysis services."""

    print("Getting Analysis URL...")
    portals_self_url = "{}/portals/self?f=json&token={}".format(portal_url, token)
    request = urllib2.Request(portals_self_url)
    portal_response = submit_request(request)

    #Parse the dictionary from the json data response to get Analysis URL
    if "helperServices" in portal_response:
        helper_services = portal_response.get("helperServices")
        if "analysis" in helper_services:
            analysis_service = helper_services.get("analysis")
            if "url" in analysis_service:
                analysis_url = analysis_service.get("url")
                return analysis_url
    else:
        raise Exception("Unable to obtain Anlysis URL.")
    
def analysis_job(analysis_url, task, token, parmas):
    """Submits an Anlysis job and returns the job URL for monitoring the job
        status in addition to the json response data for the submitted job."""
    #Unpack the analysis job parameters as a dictionary and add token and formatting
    #parameters to the dictionary. The dictionary is used in the HTTP POST request.
    #Headers are also added as a dictionary to be included with the POST.
    print("Submitting analysis job...")

    params["f"] = "json"
    params["token"] = token
    headers = {"Referer" :"http://arcgis.com"}
    task_url = "{}/{}".format(analysis_url, task)
    submit_url = "{}/submitJob?".format(task_url)
    request = urllib2.Request(submit_url, urllib.urlencode(params), headers)
    analysis_response = submit_request(request)
    if analysis_response:
    #print the response from submitting the analysis job
        print(analysis_response)
        return task_url, analysis_response
    else:
        raise Exception("Unable to submit analysis job.")

def analysis_job_status(task_url, job_info, token):
    """Tracks the staus of the submitted analysis job."""
    if "jobId" in job_info:
        #Get the id of the analysis job to track the status
        job_id = job_info.get("jobId")
        job_url = "{}/jobs/{}?f=json&token={}".format(task_url, job_id, token)
        request = urllib2.Request(job_url)
        job_response = submit_request(request)

        #Query and report the analysis job status
        if "jobStatus" in job_response:
            while not job_response.get("jobStatus") == "esriJobSucceeded":
                time.sleep(5)
                request = urllib2.Request(job_url)
                job_response = submit_request(request)
                print(job_response)

                if job_response.get("jobStatue") == "esriJobFailed":
                    raise Exception("Job failed.")
                elif job_response.get("jobStatus") == "esriJobCancelled":
                    raise Exception("Job canceled.")
                elif job_response.get("jobStatus") == "esriJobTimedOut":
                    raise Exception("Job timed out.")

            if "results" in job_response:
                return job_response
        else:
            raise Exception("No job results.")
    else:
        raise Exception("No job url.")
    
def analysis_job_results(task_url, job_info, token):
    """use the job result json to get information about the feature service created from the analysis job."""

    #get the paramUrl to get info about the analysis job results
    if "jobId" in job_info:
        job_id = job_info.get("jobId")
        if "results" in job_info:
            results = job_info.get("results")
            results_values = {}
            for key in results.keys():
                param_value = results[key]
                if "paramUrl" in param_value:
                    param_url = param_value.get("paramUrl")
                    result_url = "{}/jobs/{}/{}?token={}&f=json".format(task_url, job_id, param_url, token)
                    request = urllib2.Request(result_url)
                    param_result = submit_request(request)
                    job_value = param_result.get("value")
                    results_values[key] = job_value
            return results_values
        else:
            raise Exception("Unable to get analysis job results.")
    else:
        raise Exception("Unable to get analysis job results.")

def get_transportObj(token, name):
    param = "execute?token={}&f=pjson".format(token)
    request_url = "https://logistics.arcgis.com/arcgis/rest/services/World/Utilities/GPServer/GetTravelModes/" + param
    request = urllib2.Request(request_url)
    analysis_response = submit_request(request)
    #check that the intended json object is sent back
    if "results" in analysis_response:
        #it worked, we think
        transport_lst = []
        for i in analysis_response["results"][0]["value"]["features"]:
            transport_lst.append(i["attributes"]["Name"])
        if name in transport_lst:
            ind = transport_lst.index(name)
            return(analysis_response["results"][0]["value"]["features"][ind]["attributes"]["TravelMode"])
        else:
            raise Exception(name + " did not appear as an available type.")
    else:
        raise Exception("Error occured with Transport Type Query")

###############
####EXECUTE####
if __name__ == '__main__':
    httplib.HTTPConnection._http_vsn = 10
    httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

    #GET TOKEN
    username = #set this
    password = #set this

    host_url = "https://epa.maps.arcgis.com"
    #"https://arcgis.com"
    portal_url = "{}/sharing/rest".format(host_url)
    token = get_token(portal_url, username, password)
    #alternative
    credentials = arcpy.GetSigninToken()
    if not credentials:
        raise arcpy.ExecuteError("Please sign into ArcGIS Online")
    token = credentials["token"]
    
    #Use token to do analysis
    analysis_url = get_analysis_url(portal_url, token)
    
    task = "connectOriginsToDestinations/submitJob"
    #setup parameters
    #origins = "services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/Block_pnts_100mi/FeatureServer" #EPA
    #destinations = "services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/CapeCodMerged2/FeatureServer" #EPA
    origins = "services6.arcgis.com/2TtZhmoHm5KqwqfS/arcgis/rest/services/Block_pnts_100mi/FeatureServer"
    destinations = "services6.arcgis.com/2TtZhmoHm5KqwqfS/arcgis/rest/services/CapeCodMerged2/FeatureServer" #jbousquin
    feature_service_origins = "https://{}".format(origins)
    feature_service_destinations = "https://{}".format(destinations)

    measurementType = get_transportObj(token, "Driving Time")
    #transport method must be json object
    #walking time:
    #measurementType = {
    #    "attributeParameterValues": [
    #        {
    #            "parameterName": "Restriction Usage",
    #            "attributeName": "Walking",
    #            "value": "PROHIBITED"
    #            },
    #        {
    #            "parameterName": "Restriction Usage",
    #            "attributeName": "Preferred for Pedestrians",
    #            "value": "PREFER_LOW"
    #            },
    #        {
    #            "parameterName": "Walking Speed (km/h)",
    #            "attributeName": "WalkTime",
    #            "value": 5
    #            }
    #        ],
    #    "description":"Follows paths and roads that allow pedestrian traffic and finds solutions that optimize travel time. The walking speed is set to 5 kilometers per hour.",
    #    "impedanceAttributeName":"WalkTime",
    #    "simplificationToleranceUnits": "esriMeters",
    #    "uturnAtJunctions": "esriNFSBAllowBacktrack",
    #    "restrictionAttributeNames": [
    #        "Prefered for Pedestrians",
    #        "Walking"
    #        ],
    #    "useHierarchy": False,
    #    "simplificationTolerance": 2,
    #    "timeAttributeName": "WalkTime",
    #    "distanceAttributeName": "Miles",
    #    "type": "WALK",
    #    "id": "caFAgoThrvUpkFBW",
    #    "name": "Walking Time"
    #    }

    #time of day
    timeOfDay = "631195200000"
    #typical Monday at noon = "1/1/1990" in milliseconds, UNIX = "631195200000"
    #live traffic must be in Unix time
    #unix converter: http://www.epochconverter.com/

    timeZoneForTimeOfDay = "GeoLocal" #GeoLocal or UTC
    outputName = "OriginsToDestinations_feature_service"
    
    params = {"originsLayer": {"url":feature_service_origins},
              "destinationsLayer":{"url":feature_service_destinations},
              "measurementType":measurementType,
              "originsLayerRouteIDField":"FID",
              "destinationsLayerRouteIDField":"FID",
              "timeOfDay":timeOfDay,
              "timeZoneForTimeOfDay":timeZoneForTimeOfDay,
              "outputName":{"serviceProperties":{"name": outputName}},
              "context":"",
              "f":"json"}
              
#####BUFFER EXAMPLE#####
    task = "CreateBuffers"
    #woony Watershed
    #FS = "services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/HUC/FeatureServer"
    #feature_service = "https://{}".format(FS)

    inputService = feature_service_destinations
    output_service = "CreateBuffers_50_feature_service" #set this
    params = {"inputLayer": {"url":inputService},
              "distances": [50],
              "units": "Miles",
              "dissolveType": "Dissolve",
              "outputName": {"serviceProperties":{"name": output_service}}} #fix these
#####

    task_url, job_info = analysis_job(analysis_url, task, token, params)
    job_info = analysis_job_status(task_url, job_info, token)
    job_values = analysis_job_results(task_url, job_info, token)

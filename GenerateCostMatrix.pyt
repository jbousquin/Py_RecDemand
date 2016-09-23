"""GenerateCostMatrix.pyt
Version: 0.0.9
Requirements: developed on ArcGIS 10.3, Python 2.7
Description:
This python toolbox can be downloaded as one file and pulled into ArcGIS Desktop. The tool uses ESRI "ready to use services" to determine
travel time and distance using transportation networks stored on ESRI servers. To access these services the user must log in to their
arcGIS online account inside of arcCatalog or arcMap. At the time of development GenerateOriginDestinationCostMatrix was in Beta and
running this tool did not cost arcGIS online "credits." be sure to check the check the status of this before running the tool to ensure
account credits are available if needed.

Notes:
works sometimes...
"""

import arcpy
import os
import sys
import time

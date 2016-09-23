# Py_RecDemand
Scripts for beach recreation demand modeling

Estimating the non-market value of beaches for saltwater recreation is complex. An individual’s preference for a beach depends on beach
characteristics and perception. When choosing one beach over another, an individual balances these personal preferences with any
additional costs, in travel time and/or fees to access the beach. This trade-off can be used to infer how people value different beach
characteristics and evaluate changes in beach characteristics, such as water quality. Especially when beaches are free to the public,
beach value estimates rely heavily on accurate travel times.

The tools included in this repository allow the user to estimate travel costs in terms of travel time and distance. This is done using a
set of start/origin points and a set of destination points. The tools for calculating travel time do not require a network dataset, but
instead use networks stored on a variety of different servers (ArcGIS, Google, Open StreetMaps).

Python Toolboxes (.pyt) can be downloaded and run using ArcGIS desktop 10.0+.
Python scripts (.py) can be downloaded and run using python, but may require non-standard libraries (e.g. arcpy).

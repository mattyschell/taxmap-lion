# Background

Approximately 4 times a year the Department of Finance asks DoITT to refresh
the "LION Subset" data used in the digital tax map.  The source of this data
is both  the LION release from the Dept. of City Planning and CSCL Centerlines.

In the Digital Taxmap this logical dataset is copied into two physical datasets.
First, there is an ESRI geodatabase-registered feature class 
dof_taxmap.LION_SUBSET_SDE that Dept. of Finance users refer to in their map 
documents as an editing reference.  Second, there's an Oracle spatial table named 
CSCL_CENTERLINE that contains data which we use for generating street labels on 
taxmap tiles.


# Part A: Upload LION Subset

1.	Download new LION data and place on T Drive

2.	In python stg first then prod:

```shell
> python
>>> from featureclassupdate import *
>>> prodnew = EsriFeatureClass("C:\\arcgis_connections\\arcgisconnections-dof_taxmap@geocprd (dof_taxmap).sde", 'LION_SUBSET_SDE_new')
>>> prodnew.copytosde("T:\GIS_ORTHO\Spatial Data\DCP\LION\Current\\18B\\nyclion_18b\lion\lion.gdb\lion",'N')
>>> prodnew.updateprivileges()
```

```shell
> python
>>> prod = EsriFeatureClass("C:\\arcgis_connections\\arcgisconnections-dof_taxmap@geocprd (dof_taxmap).sde", 'LION_SUBSET_SDE')
>>> prod.rename('LION_SUBSET_SDE_17C')
>>> prodnew.rename('LION_SUBSET_SDE')
```


# Part B: Copy to SDO for Tiles

Reverse-engineering the requirements, street labels on the digital taxmap should:

1. Use the published CSCL centerlines (aka "CSCL Pub")
2. Use whatever column CSCL currently describes as "for cartographic labeling"
3. Include bike lanes
4. Not include ferry routes 

Example, this should be scripted up and .sde files added to resources when 
blessed by DOF.

```shell
> REM jump back to python 2.7 if necessary 
> REM set PATH=C:\Python27\ArcGIS10.6;%PATH%
> python
>>> import featureclassupdate
>>> csclsource = featureclassupdate.EsriFeatureClass("C:/arcgisconnections/mschell@csclcprd.sde",'CSCL_PUB.Centerline')
>>> cscltargettemp = featureclassupdate.EsriFeatureClass("C:/matt_projects/database_utils/arcgisconnections/dof_taxmap@geocdev (dof_taxmap).sde",'CSCL_TEMP_SDO')
>>> csclcenterline = featureclassupdate.EsriFeatureClass("C:/matt_projects/database_utils/arcgisconnections/dof_taxmap@geocdev (dof_taxmap).sde",'CSCL_CENTERLINE')
>>> cscltargettemp.copytosde(csclsource.featureclass,'N','SDO_GEOMETRY','1=1')
>>> csclcenterline.truncate()
>>> csclcenterline.populate_hardcodecolumns(cscltargettemp)
>>> csclcenterline.hardcoded_removecurves()
>>> csclcenterline.validatesdo()
>>> cscltargettemp.delete()
```

Reminder on fixing invalid geometries.  The DOF_TAXMAP user-schema geodatabase 
shadows some oracle functions with ESRI functions of the same name.  Ordinarily
the MDSYS prefix is unnecessary.

```sql
update 
   cscl_centerline a
set 
   a.shape = mdsys.sdo_util.RECTIFY_GEOMETRY(a.shape, .0005)
where 
    a.objectid = 789;
```

# Part C: Regenerate Tiles

The plan we have cooked up for now is to connect to the tile host and delete
all zoom levels where street labels appear.  Then recreate tiles for the default
zoom of the application when searching for a lot, +/- 1 zoom (3 total).  All 
other zoom levels with street labels can fill in from ad hoc use.

## C1: Delete or rename zoom levels 8-13.  Sample staging directories after this step:

```shell
[***@*****-******** /gis/data/tiles/gwc/dtm]ll
total 104
drwxr-xr-x   4 gis gis  4096 Feb  5  2015 dtm_00
drwxr-xr-x   8 gis gis  4096 Feb  5  2015 dtm_01
drwxr-xr-x   4 gis gis  4096 May 21  2015 dtm_02
drwxr-xr-x   8 gis gis  4096 Jun 24  2015 dtm_03
drwxr-xr-x   8 gis gis  4096 Jul 17  2018 dtm_04
drwxr-xr-x  14 gis gis  4096 Jul 18  2018 dtm_05
drwxr-xr-x  12 gis gis  4096 Jul 18  2018 dtm_06
drwxr-xr-x  16 gis gis  4096 Jul 18  2018 dtm_07
drwxr-xr-x   7 gis gis  4096 Jan 15 10:15 dtm_08
drwxr-xr-x  14 gis gis  4096 Jul 18  2018 dtm_08x
drwxr-xr-x   9 gis gis  4096 Jan 15 10:15 dtm_09
drwxr-xr-x  21 gis gis  4096 Jan  9 11:49 dtm_09x
drwxr-xr-x   7 gis gis  4096 Jan 15 10:12 dtm_10
drwxr-xr-x  27 gis gis  4096 Jul 18  2018 dtm_10x
drwxr-xr-x   5 gis gis  4096 Jan 14 16:31 dtm_11
drwxr-xr-x  78 gis gis  8192 Mar 27  2013 dtm_11x
drwxr-xr-x   3 gis gis  4096 Jan 14 15:23 dtm_12
drwxr-xr-x  76 gis gis  8192 Mar 27  2013 dtm_12x
drwxr-xr-x   3 gis gis  4096 Jan 14 15:23 dtm_13
drwxr-xr-x 241 gis gis 20480 Jun 26  2015 dtm_13x
```

## C2: Using the GUI (if possible) fully seed 9, 10, and 11.  Default zoom in the app is 10.   

(not possible)

## C2 option 2: Seed 9, 10, and 11 without the GUI

We take this approach when the gis-ogc containers flake out too much to make 
the GUI seed process tenable.  For a single zoom (9 in the example) keep at 
least one thread going until all tiles are seeded.

```shell
> REM set python 2.7 if you default to 3
> set PATH=C:\Python27\ArcGIS10.6;%PATH%
> python sisyphustiles.py dtm notadmin iluvdoitt247 2263 9 png seed "http://*******/geowebcache/rest/seed/dtm.json"

```
Docs for the version of GWC we are using (I think):

    https://www.geowebcache.org/docs/1.5.1/index.html

Reminder: Getting the current state of the seeding threads

```shell
curl -v -u notadmin:iluvdoitt247 -XGET "http://********/geowebcache/rest/seed/dtm.json"
```



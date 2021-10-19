

############################################################
# Author: Erika Kamptner
# Description: Updates featureclasses via SDE connections
# Created: 03/22/2018
# Log:
#
############################################################

import arcpy
import fcmutils

class EsriFeatureClass(object):

    def __init__(self,
                 connpath,
                 name):  #name of final dataset ie. LION_SUBSET_SDE

        self.name = name.upper()
        self.sdeconn = connpath
        self.featureclass = connpath + "/" + self.name

    # Rename existing table as backup
    def rename(self,
               targetname):

        arcpy.Rename_management(self.featureclass, targetname.upper())

        msg = self.name + " has been renamed to " + targetname

        print msg

    # Import Lion feature class
    def copytosde(self,
                  inputfeatures,
                  allowoverwrite='N',
                  targetkeyword=None,
                  whereclauseoverride=None):

        targetfc = EsriFeatureClass(self.sdeconn,
                                    self.name)

    # Check if target feature class already exists and/or has a lock
        if targetfc.exists():

            if allowoverwrite == 'N':

                errormsg = self.featureclass + " already exists. Set overwrite to Y"
                print errormsg
                raise ValueError(errormsg)

            elif targetfc.lockexist():

                errormsg = self.featureclass + " already exists and has schema lock. "
                print errormsg
                raise ValueError(errormsg)

            else:

                print self.featureclass + " already exists. "

        # feature class to feature class conversion with where clause for lion streets
        if whereclauseoverride is None:
        
            whereclause = " \"FEATURETYP\" = '0' and \"SEGMENTTYP\" = 'B' " \
                        "OR \"FEATURETYP\" = '0' and \"SEGMENTTYP\" = 'R'" \
                        "OR \"FEATURETYP\" = '0' and \"SEGMENTTYP\" = 'U'" \
                        "OR \"FEATURETYP\" = 'A' and \"SEGMENTTYP\" = 'U' " \
                        "OR \"FEATURETYP\" = '0' and \"SEGMENTTYP\" = 'T' " \
                        "OR \"FEATURETYP\" = '5' " \
                        "OR \"FEATURETYP\" = '9' "
        
        else:

            whereclause = whereclauseoverride

        arcpy.FeatureClassToFeatureClass_conversion(inputfeatures,
                                                    self.sdeconn,
                                                    self.name,
                                                    whereclause,
                                                    config_keyword=targetkeyword)

        self.countcheck(inputfeatures, whereclause, False)

    def delete(self):

        arcpy.Delete_management(self.featureclass)

    def exists(self):

            return arcpy.Exists(self.featureclass)

    def lockexist(self):

        if arcpy.TestSchemaLock(self.featureclass):

            return False

        else:

            return True

    def countcheck(self, inputfeatures, whereclause, issde=False):

        if not issde:

            # tried a search cursor here, but for some reason cursors don't work with the get count function
            arcpy.MakeTableView_management(inputfeatures, "filtercount", whereclause)
            sourcecount = int(arcpy.GetCount_management("filtercount").getOutput(0))

        else:
            sourcecount = arcpy.GetCount_management(inputfeatures)

        targetcount = arcpy.GetCount_management(self.featureclass)

        if str(targetcount) == str(sourcecount):
            msg = "Congratulations, ESRI did not fail you. Target count: " + str(targetcount) + "   Source Count: " + str(sourcecount)
            print msg
        else:
            msg = "Something went wrong... Target count: " + str(targetcount) + "   Source Count: " + str(sourcecount)
            print msg

        arcpy.Delete_management("filtercount")

    # Update read only privileges on dataset
    def updateprivileges(self):

        arcpy.ChangePrivileges_management(self.featureclass, "MAP_VIEWER", "GRANT")
        arcpy.ChangePrivileges_management(self.featureclass, "DOF_EDITOR", "GRANT")

        msg = "Update complete!"
        print msg

    def truncate(self):

        sql = 'TRUNCATE table {0}'.format(self.name)

        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        if not sdereturn:
            raise ValueError('{0} threw {1}'.format(sql,
                                                    sdereturn))

        
    def populate_hardcodecolumns(self,
                                 sourcefc):

        # poor form chap
        sql = """insert into {0} """.format(self.name) \
            + """   (objectid, physicalid, stname_lab, shape) """ \
            + """select """ \
            + """    objectid, physicalid, TRIM (stname_label), shape """ \
            + """from {0} """.format(sourcefc.name) \
            + """where """ \
            + """rw_type <> 14"""

        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        if not sdereturn:
            raise ValueError('{0} threw {1}'.format(sql,
                                                    sdereturn))

    def validatesdo(self):

        sql = "select a.objectid from {0} a ".format(self.name) \
            + "where " \
            + "sdo_geom.validate_geometry_with_context(a.shape, .0005) <> 'TRUE'"

        sdereturn = fcmutils.selectacolumn(self.sdeconn,
                                           sql)

        if (len(sdereturn) > 0):
            raise ValueError("Invalid objectids in {0} are {1}".format(self.name, 
                                                                       sdereturn)) 

    def hardcoded_removecurves(self):

        sql = "update {0} b ".format(self.name) \
            + "set b.shape = sdo_geom.sdo_arc_densify(b.shape, .0005, 'arc_tolerance=.25 unit=FOOT') " \
            + "   where b.objectid IN ( " \
            + "SELECT aa.objectid FROM " \
            + "   (SELECT " \
            + "       a.objectid, " \
            + "       DECODE(MOD(ROWNUM, 3), 2, t.COLUMN_VALUE, NULL) etype, " \
            + "       DECODE(MOD(ROWNUM, 3), 0, t.COLUMN_VALUE, NULL) interpretation " \
            + "    FROM " \
            + "       {0} a, ".format(self.name) \
            + "       TABLE(a.shape.sdo_elem_info) t ) aa " \
            + "    WHERE " \
            + "        aa.etype IN (1005, 2005) " \
            + "     OR aa.interpretation IN (2,4) " \
            + ")"

        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        if not sdereturn:
            raise ValueError('{0} threw {1}'.format(sql,
                                                    sdereturn))

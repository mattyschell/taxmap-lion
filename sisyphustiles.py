# mschell! 20200309
# cribbed from https://github.com/mattyschell/tilerefresh
# Motivation: gis-ogc container crashes and must be auto-restarted.
#             This kills all running seed threads
# Assumption for simplicity: We will complete each zoom as separate and 
#                            indepedent exercises
# A call to sisyphustiles.py will work to ensure that at least 1 thread is 
#    running until all tiles for the zoom are complete. Feel free to kick off a 
#    few additional threads from the GUI.  Here in this script we  will start a 
#    single thread and then restart it as necessary.  The goal is not to be fast 
#    but to ensure that we can keep chugging away overnight or through a weekend. 

# python sisyphustiles.py
#        dtm
#        notadmin
#        iluvdoitt247
#        2263
#        9
#        png
#        seed
#        "http://***********/geowebcache/rest/seed/dtm.json"

import sys
import time
import datetime
import traceback
import os
import re
import json
import urllib2


def usage():
    print " "
    print "   I am " + sys.argv[0]
    print "Usage: "
    print "   <gwclayername>   Geowebcache layer (probably dtm)"
    print "   <gwcuser>        Geowebcache user"
    print "   <gwcpass>        Geowebcache password"
    print "   <srs>            Layer spatial reference (probably 2263)"
    print "   <zoomstart>      Zoom level to fill in (probably 9, 10, or 11)"
    print "   <imagetype>      Cached image format (probably png)"
    print "   <refreshtype>    Type of refresh (probably seed)"
    print "   <resturl>        Geowebcache url"
    print "I received as input:"
    for arg in sys.argv:
        print "   " + arg


def timer(start, end):
    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)


class mbrfilemanager(object):

    # placeholder, going with hard coded full extent in this repo for now

    def __init__(self,
                 mbrfilepath=None):

        if mbrfilepath is None:

            self.mbrfilepath = None
            mbrs = '700000.0,-4444.4455643044785,1366666.6683464567,440000.0'
            self.mbrs = []
            self.mbrs = self.readmbrfile(mbrs)

        else:

            if os.path.isfile(os.path.normpath(mbrfilepath)):
                self.mbrfilepath = os.path.normpath(mbrfilepath)
            else:
                raise ValueError('source mbr file ' + mbrfilepath + ' doesnt exist')

            self.mbrs = []
            self.mbrs = self.readmbrfile()

    def readmbrfile(self,
                    mbrs = None):

        if mbrs is None:

            #pull from a file
            with open(self.mbrfilepath, 'r') as mbrfilehandle:
                mbrlist = mbrfilehandle.read().splitlines()

            if len(mbrlist) == 0:
                raise ValueError('Didnt get any mbrs from ' + self.mbrfilepath)

        else:
            
            # passed in a single x,y,x,y
            mbrlist = []
            mbrlist.append(mbrs)

        cleanmbrs = []

        for mbr in mbrlist:
            print "working MBR comma delimited like " + mbr
            # reject empty lines and lines without 3 commas
            if mbr and re.search(r'.+,.+,.+,.+', mbr):
                cleanmbrs.append(mbr.strip().split(','))

        if len(cleanmbrs) == 0:
            raise ValueError('Didnt get any valid mbr strings from ' + self.mbrfilepath)

        return cleanmbrs


class gwclayermanager(object):

    def __init__(self,
                 playername,
                 purl,
                 pgwcuser,
                 pgwcpass,
                 psrs,
                 pzoomstart,
                 pzoomstop,
                 pimagetype,
                 prefreshtype):

        self.layername = playername
        self.url = purl

        # Keep it on the DL: I dont understand this urllib2 business
        self.passwordmanager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        self.passwordmanager.add_password(None, purl, pgwcuser, pgwcpass)
        self.authenticationhandler = urllib2.HTTPBasicAuthHandler(self.passwordmanager)
        self.proxyhandler = urllib2.ProxyHandler({})
        self.opener = urllib2.build_opener(self.proxyhandler, 
                                           self.authenticationhandler)

        self.zoomstart = int(pzoomstart)
        self.zoomstop = int(pzoomstop)
        self.srs = int(psrs)
        self.imagetype = pimagetype
        self.seedtype = self.setseedtype(prefreshtype)
        # default start
        self.pctcomplete = 0
        self.maxcomplete = 0

    def getjsondata(self,
                    mbrlist):

        jsondata = {"seedRequest": {"name": self.layername, "srs": {"number": self.srs}, "zoomStart": self.zoomstart,
                                    "zoomStop": self.zoomstop, "type": self.seedtype, "threadCount": 1,
                                    "format": 'image/' + self.imagetype,
                                    "bounds": {"coords": {"double": mbrlist}}
                                    }
                    }

        # dict to str
        return json.dumps(jsondata)

    def setseedtype(self,
                    seedtype):

        if seedtype is None:
            return 'seed'
        else:
            return seedtype.lower()

    def setpctcomplete(self,
                       gwcarray):

        # this version is live percent complete, from the GWC GET call
        if gwcarray:

            array1 = gwcarray[0]

            # float conversion is necessary in 2.7
            self.pctcomplete = float(array1[0]) / array1[1] * 100

        else:

            # passed an emtpy array, either done or ded
            self.pctcomplete = 0

    def setmaxpctcomplete(self,
                       maxcomplete):

        # this version keeps track of the highest number we see

        if maxcomplete > self.maxcomplete:

            self.maxpctcomplete = maxcomplete 

    def getpctcomplete(self):

        self.setpctcomplete(self.getstate())

        return self.pctcomplete

    def executerequest(self,
                       jsondata):

        urllib2.install_opener(self.opener)

        request = urllib2.Request(self.url,
                                  jsondata,
                                  {'User-Agent': "Python script", 'Content-type': 'text/xml; charset="UTF-8"',
                                   'Content-length': '%d' % len(jsondata)})

        try:

            response = urllib2.urlopen(request)

            if response.code == 200:
                response.close()
                return 'SUCCESS: called gwc rest api with {0}{1}'.format(jsondata,
                                                                         '\n')
            else:
                retcode = response.code
                print "response info {0}".format(response.info())
                print "response code {0}".format(retcode)
                print "response read {0}".format(response.read())
                response.close()
                return 'FAIL: Response {0} not ok{1}'.format(retcode,
                                                             '\n')

        except IOError, e:
            print "exception calling geowebcache rest api " + str(e)
            print "using url {0} and jsondata {1}".format(self.url,
                                                          jsondata)
            return 'FAIL: with unhandled error {0}{1}'.format(str(e),
                                                              '\n')

    def getstate(self):

        urllib2.install_opener(self.opener)

        "the HTTP request will be a POST instead of a GET when the data parameter is provided."
        request = urllib2.Request(self.url)

        # active
        #{"long-array-array":[[9849,1502501,4850,7,1]]}
        # done or dead
        #{"long-array-array":[]}

        try:

            response = urllib2.urlopen(request)

            if response.code == 200:
                responsed = json.loads(response.read())
                response.close()
                return responsed.get('long-array-array')
            else:
                retcode = response.code
                print "response info {0}".format(response.info())
                print "response code {0}".format(retcode)
                print "response read {0}".format(response.read())
                response.close()
                return 'FAIL: Response {0} not ok{1}'.format(retcode,
                                                             '\n')

        except IOError, e:
            print "exception calling geowebcache rest api " + str(e)
            print "using url {0}".format(self.url)                                                          
            return 'FAIL: with unhandled error {0}{1}'.format(str(e),
                                                              '\n')

    def isded(self):

        # Writing more comments than code: An indication of success! 
        # We will distinguish between three known types of behavior (under our
        #   simplifying assumptions see the top) using the results from a GET 
        #   request of geowebcache
        # [tiles processed, total # of tiles to process, # of remaining tiles, Task ID, Task status]
        #    (number of remaining tiles doesnt make any sense to me)
        # 1. Running along, slowly producing tiles.  NOTDED
        #    [100000, 200000, x, y]
        #    ... repeated isded checks, pct complete approaches 100 slowly ...
        #    [100100, 200000, x, y]
        #    [100200, 200000, x, y]
        #    ...
        #    []
        # 2. Running along after a restart, all tiles are complete 
        #    but GWC rolls thru checking them.  NOTDED
        #    [100000, 200000, x, y]
        #    .... repeated isded checks, pct complete approaches 100 quickly ...
        #    [123000, 200000, x, y]
        #    [146000, 200000, x, y]
        #    ... 
        #    []
        # 3. Running along and died.  DED
        #    [100000, 200000, x, y]
        #    ... repeated isded checks, pct complete does not approach 100 ...
        #    []

        pctcomplete1 = self.getpctcomplete()
        self.setmaxpctcomplete(pctcomplete1)    
        
        print "percent complete is {0}".format(str(pctcomplete1))
        print "sleeping for 1 minute and checking again"

        time.sleep(60)

        pctcomplete2 = self.getpctcomplete()
        self.setmaxpctcomplete(pctcomplete2)
        print "percent complete is {0}".format(str(pctcomplete2))

        
        if pctcomplete2 == 0 and self.maxpctcomplete > 95:

            # kinda taking a risk here on the 95 number
            # but Im making a decision that even if we only get 95% complete
            # the remaining 5% can fill from general use
            # can get (99, 100) .. (0, 0). Checking max complete    
            # avoids (0,0) being 'notded'
            return 'dun'

        if pctcomplete2 >= pctcomplete1 and pctcomplete2 > 0:
            
            return 'notded'

        elif pctcomplete2 == 0:

            # ie back to nothing running and max complete never passed 95    
            return 'ded'
        
        else:
            
            raise ValueError('Inexplicable progress percent complete went from {0} to {1}'.format(pctcomplete1,
                                                                                                  pctcomplete2)) 


def main(gwclayername,
         gwcuser,
         gwcpass,
         srs,
         zoom,
         imagetype,
         refreshtype,
         resturl):

    start_time = time.time()
    logtext = "{0}Starting {1} at {2} {3}".format('\n',
                                                  sys.argv[0],
                                                  str(datetime.datetime.now()),
                                                  '\n\n')

    try:

        mbrmgr = mbrfilemanager()

        gwcmgr = gwclayermanager(gwclayername,
                                 resturl,
                                 gwcuser,
                                 gwcpass,
                                 srs,
                                 zoom,
                                 zoom,
                                 imagetype,
                                 refreshtype)

        for mbrlist in mbrmgr.mbrs:

            response = gwcmgr.executerequest(gwcmgr.getjsondata(mbrlist))

            logtext += response

            if response.startswith('FAIL'):

                break

            else: 

                vitalsigns = 'notded'

                while vitalsigns <> 'dun':
                
                    vitalsigns =  gwcmgr.isded() 

                    print "gwc is {0} ".format(vitalsigns)

                    if vitalsigns == 'ded':
                    
                        print 'ded, executing a new request to geowebcache'
                        response = gwcmgr.executerequest(gwcmgr.getjsondata(mbrlist))

                        if response.startswith('FAIL'):
                        
                            break

                    elif vitalsigns == 'dun':
                        
                        print 'dun!!!'
                        #the only sucessful exit
                        return 0

                    elif vitalsigns == 'notded':
                        
                        print 'still chugging'

    except Exception as e:

        print str(e)

        logtext += "This is a FAILURE :-( notification \n\n" + logtext
        logtext += str(traceback.format_exception(*sys.exc_info()))

    logtext += "{0}Elapsed Time: {1} {2}".format('\n',
                                                 timer(start_time, time.time()),
                                                 '\n\n')
    print logtext
    return 1


if __name__ == "__main__":

    if len(sys.argv) != 9:
        usage()
        raise ValueError('Expected 8 inputs, see usage (may be in the log')

    pgwclayername = sys.argv[1]
    pgwcuser      = sys.argv[2]
    pgwcpass      = sys.argv[3]
    psrs          = sys.argv[4]
    pzoom         = sys.argv[5]
    pimagetype    = sys.argv[6]
    prefreshtype  = sys.argv[7]
    presturl      = sys.argv[8]

    mainreturn = main(pgwclayername,
                      pgwcuser,
                      pgwcpass,
                      psrs,
                      pzoom,
                      pimagetype,
                      prefreshtype,
                      presturl)

    print "Exiting with status{0}".format(mainreturn)

    exit(mainreturn)
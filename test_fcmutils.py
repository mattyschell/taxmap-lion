import os
import unittest
import time
import fcmutils

# python -m unittest -v test_fcmutils
# slow opening sde connections and importing arcpy tis normal

class UtilsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        dir = os.path.dirname(__file__)
        self.resourcepath = os.path.join(dir,
                                         'resources')

        self.sdeconn = os.path.join(self.resourcepath,
                                    '********')

        self.testpackage = 'FCMTESTPKG1'
        self.testpackage2 = 'FCMTESTPKG2'

        self.testsqlfile = os.path.join(self.resourcepath,
                                        'test_sqlfile.sql')

    @classmethod
    def tearDownClass(self):

        sql = 'DROP PACKAGE ' + self.testpackage

        if not fcmutils.execute_immediate(self.sdeconn, sql):
            raise ValueError('Failed to drop ' + self.testpackage)

        sql = 'DROP PACKAGE ' + self.testpackage2

        if not fcmutils.execute_immediate(self.sdeconn, sql):
            raise ValueError('Failed to drop ' + self.testpackage2)

    def test_atimer(self):

        start_time = time.time()
        time.sleep(.25)

        elapsed = fcmutils.timer(start_time, time.time())
        self.assertGreater(elapsed, 0)

    def test_bexecute_immediate(self):

        #sql returns a single X

        sql = 'SELECT dummy from dual'
        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        self.assertEqual(len(sdereturn), 1)

        self.assertEqual(sdereturn[0], 'X')

    def test_cexecute_immediate(self):

        #sql returns a list with 2 Xs

        sql = 'SELECT dummy from dual UNION ALL select dummy from dual'
        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        self.assertIsInstance(sdereturn, list)

        self.assertEqual(len(sdereturn), 2)

    def test_dselectavalue(self):

        sql = 'SELECT dummy FROM dual'

        sdereturn = fcmutils.selectavalue(self.sdeconn,
                                          sql)

        self.assertEqual(sdereturn, 'X')

    def test_eselectnull(self):

        # should error.  Its select a value, not select the void
        sql = 'SELECT NULL FROM dual'

        try:
            sdereturn = fcmutils.selectavalue(self.sdeconn,
                                              sql)
        except:
            pass
        else:
            self.assertFalse(sdereturn)

    def test_hcompiledbcode(self):

        sql = """CREATE OR REPLACE PACKAGE """ + self.testpackage + """
                AUTHID CURRENT_USER
                AS

                   PROCEDURE DUMMY (
                      the_letter_a      IN VARCHAR2
                   );

                END """ + self.testpackage + """;"""

        retval = fcmutils.compiledbcode(self.sdeconn,
                                        sql)

        self.assertTrue(retval)

        sql = 'DROP PACKAGE ' + self.testpackage
        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        self.assertTrue(sdereturn)

    def test_icompilesqlfile(self):

        # test sql file has 2 packages, first named like self.testpackage

        sdereturn = fcmutils.compilesqlfile(self.sdeconn,
                                            self.testsqlfile)

        self.assertTrue(sdereturn)

        sql = "SELECT COUNT(*) FROM user_objects " \
            + "WHERE object_type = 'PACKAGE' " \
            + "AND object_name = '" + self.testpackage + "'" \
            + "AND status = 'VALID'"

        sdereturn = fcmutils.selectavalue(self.sdeconn,
                                          sql)

        self.assertEqual(sdereturn, 1)

    def test_jcallproc(self):

        sql = """CALL """ + self.testpackage + """.DUMMY('A') """

        sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                               sql)

        self.assertTrue(sdereturn)

    def test_kcallproc(self):

        # should error

        
        sql = """CALL """ + self.testpackage + """.DUMMY('B') """

        print "Expecteded sql fail on next line from {0}".format(sql)

        try:
            sdereturn = fcmutils.execute_immediate(self.sdeconn,
                                                   sql)
        except:
            pass
        else:
            self.assertFalse(sdereturn)

    def test_lselectacolumn(self):

        sql = 'SELECT dummy FROM dual'

        output = fcmutils.selectacolumn(self.sdeconn,
                                        sql)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'X')

        sql = 'select dummy from dual union all select dummy from dual'

        output = fcmutils.selectacolumn(self.sdeconn,
                                        sql)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], 'X')
        self.assertEqual(output[1], 'X')

    def test_mselectabadcolumn(self):

        sql = 'SELECT boo FROM dual'
        print "Expected sql fail on next line from {0}".format(sql)

        try:
            output = fcmutils.selectacolumn(self.sdeconn,
                                            sql)
        except:
            pass
        else:
            raise ValueError('Shoulda failed')

    def test_nselectanumbercolumn(self):

            sql = 'SELECT 1 FROM dual'

            output = fcmutils.selectacolumn(self.sdeconn,
                                            sql)

            self.assertIsInstance(output, list)
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0], 1)

            sql = 'select 1 from dual union all select 1 from dual'

            output = fcmutils.selectacolumn(self.sdeconn,
                                            sql)

            self.assertIsInstance(output, list)
            self.assertEqual(len(output), 2)
            self.assertEqual(output[0], 1)
            self.assertEqual(output[1], 1)

    def test_ogetnulldupes(self):

        nulldupes = fcmutils.get_duplicates(self.sdeconn,
                                            'DUAL',
                                            'DUMMY')

        self.assertEqual(len(nulldupes), 0)

    def test_pgetadupe(self):

        table = '(select dummy from dual union all select dummy from dual)'
        adupe = fcmutils.get_duplicates(self.sdeconn,
                                        table,
                                        'DUMMY')

        self.assertEqual(len(adupe), 1)
        self.assertEqual(adupe[0], 'X')

    def test_qgetmultidupes(self):

        table = "(select dummy from dual union all select dummy from dual " \
              + "union all " \
              + "select 'Y' from dual union all select 'Y' from dual) "

        dupes = fcmutils.get_duplicates(self.sdeconn,
                                        table,
                                        'DUMMY')

        self.assertEqual(len(dupes), 2)
        # ordered yo
        self.assertEqual(dupes[0], 'X')
        self.assertEqual(dupes[1], 'Y')

    def test_rselectanullcolumn(self):

        sql = 'SELECT 1 FROM dual UNION ALL SELECT NULL FROM dual'

        output = fcmutils.selectacolumn(self.sdeconn,
                                        sql)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0], 1)
        self.assertIsNone(output[1])

        sql = 'SELECT NULL FROM dual'

        output = fcmutils.selectacolumn(self.sdeconn,
                                        sql)

        self.assertIsInstance(output, list)
        self.assertEqual(len(output), 1)
        self.assertIsNone(output[0])

if __name__ == '__main__':
    unittest.main()
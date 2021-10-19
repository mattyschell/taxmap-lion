CREATE OR REPLACE PACKAGE FCMTESTPKG1
AUTHID CURRENT_USER
AS

   PROCEDURE DUMMY (
      the_letter_a      IN VARCHAR2
   );

END FCMTESTPKG1;
/

CREATE OR REPLACE PACKAGE BODY FCMTESTPKG1
AS

   PROCEDURE DUMMY (
      the_letter_a      IN VARCHAR2
   )
   AS

      --mschell! 20161209
      --dumb tester for unit tests.  A profound success would be
      --CALL FEATURECLASS_MAINTENANCE.DUMMY('A');

   BEGIN

      IF UPPER(the_letter_a) = 'A'
      THEN

          RETURN;

      ELSE

         RAISE_APPLICATION_ERROR(-20001, 'Thats not the letter A');

      END IF;

   END DUMMY;

END FCMTESTPKG1;
/

CREATE OR REPLACE PACKAGE FCMTESTPKG2
AUTHID CURRENT_USER
AS

   PROCEDURE DUMMY (
      the_letter_a      IN VARCHAR2
   );

END FCMTESTPKG2;
/

CREATE OR REPLACE PACKAGE BODY FCMTESTPKG2
AS

   PROCEDURE DUMMY (
      the_letter_a      IN VARCHAR2
   )
   AS

      --mschell! 20161209
      --dumb tester for unit tests.  A profound success would be
      --CALL FEATURECLASS_MAINTENANCE.DUMMY('A');

   BEGIN

      IF UPPER(the_letter_a) = 'A'
      THEN

          RETURN;

      ELSE

         RAISE_APPLICATION_ERROR(-20001, 'Thats not the letter A');

      END IF;

   END DUMMY;

END FCMTESTPKG2;
/
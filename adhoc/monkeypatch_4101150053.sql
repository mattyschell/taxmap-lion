-- CSCL source
create table mp_4101150053 as 
select *
from 
    cscl_pub.centerline a
where 
    mdsys.sdo_anyinteract(a.shape
                         ,mdsys.SDO_GEOMETRY(2003, 41088, NULL, 
                                             SDO_ELEM_INFO_ARRAY(1, 1003, 3), 
                                             SDO_ORDINATE_ARRAY(1039293, 192843, 1040048, 193897))
                         ) = 'TRUE';
-- download from source to shp 
-- load shp to target
-- then
select max(objectid+1) from cscl_centerline;
create sequence mp_4101150053seq start with xx increment by 1;
--
create table cscl_centerline_bak 
as 
select * 
from 
    cscl_centerline a
where 
    mdsys.sdo_anyinteract(a.shape
                         ,mdsys.SDO_GEOMETRY(2003, 41088, NULL, 
                                             SDO_ELEM_INFO_ARRAY(1, 1003, 3), 
                                             SDO_ORDINATE_ARRAY(1039293, 192843, 1040048, 193897))
                         ) = 'TRUE';
delete from 
    cscl_centerline a
where 
    mdsys.sdo_anyinteract(a.shape
                         ,mdsys.SDO_GEOMETRY(2003, 41088, NULL, 
                                             SDO_ELEM_INFO_ARRAY(1, 1003, 3), 
                                             SDO_ORDINATE_ARRAY(1039293, 192843, 1040048, 193897))
                         ) = 'TRUE';     
commit;
insert into cscl_centerline
    (objectid
    ,physicalid
    ,stname_lab
    ,shape)
select 
    mp_4101150053seq.nextval
   ,physicalid
   ,stname_lab
   ,shape
from mp_4101150053;
commit;
--run the tile business and verify
--then
drop sequence mp_4101150053seq;
-- delete mp_4101150053 from ArcCatalog


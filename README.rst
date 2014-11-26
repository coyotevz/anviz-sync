anviz-sync
==========

Synchronizes an Anviz Time & Attendance device with a specified database using
SQLAlchemy.

The connection to the device is made using the socket library and don't depend
on any other software.

The functionality is still limited but the main use cases are supported
(set/get device time, get record information, download records)

Tested with Anviz A300.

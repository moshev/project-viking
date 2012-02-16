@echo off

Set UI=%1
Set PY=%UI:.ui=.py%

"C:\Python26\python" "C:\Python26\Lib\site-packages\PyQt4\uic\pyuic.py" -o %PY% %UI%
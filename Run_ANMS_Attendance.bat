@echo off
setlocal
set "APP=%~dp0ANMS_Attendance.exe"
if not exist "%APP%" set "APP=%~dp0dist\ANMS_Attendance.exe"
if not exist "%APP%" (
    echo ANMS_Attendance.exe was not found beside this launcher or in the dist folder.
    pause
    exit /b 1
)
start "" "%APP%"
exit /b 0
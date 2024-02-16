call conda activate py-behav-box-v2
if not exist %USERPROFILE%\Desktop\py-behav\logging mkdir %USERPROFILE%\Desktop\py-behav\logging
call pybehave > %USERPROFILE%\Desktop\py-behav\logging\%date:~10%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%.log 2>&1
pause
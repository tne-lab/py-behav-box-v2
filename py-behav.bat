call C:\ProgramData\Anaconda3\Scripts\activate.bat py-behav-box-v2
cd C:\Users\SetShift\Documents\GitHub\py-behav-box-v2\source
if not exist %USERPROFILE%\Desktop\py-behav\logging mkdir %USERPROFILE%\Desktop\py-behav\logging
if not exist %USERPROFILE%\Desktop\py-behav\profiling mkdir %USERPROFILE%\Desktop\py-behav\profiling
call viztracer --max_stack_depth 4 --ignore_c_function --magic_comment -o %USERPROFILE%\Desktop\py-behav\profiling\result.json run.py > %USERPROFILE%\Desktop\py-behav\logging\%date:~10%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%.log 2>&1
pause
:: SET LOCAL_PY_DIR=%USERPROFILE%\Anaconda3
:: SET LOCAL_PY_DIR=%LOCALAPPDATA%\Continuum\anaconda3
SET LOCAL_PY_DIR=%HOMEPATH%\Anaconda3
:: SET LOCAL_PY_DIR=C:\tools\Anaconda3

CALL %LOCAL_PY_DIR%\Scripts\Activate.bat
%LOCAL_PY_DIR%\python.exe frag_encode.py
timeout 3

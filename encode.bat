:: SET LOCAL_PY_DIR=%LOCALAPPDATA%\Continuum\anaconda3
SET LOCAL_PY_DIR=%HOMEPATH%\Anaconda3

call %LOCAL_PY_DIR%\Scripts\activate.bat
%LOCAL_PY_DIR%\python frag_encode.py
timeout 3

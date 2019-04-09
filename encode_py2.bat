:: SET LOCAL_PY_DIR=%LOCALAPPDATA%\Continuum\anaconda3
:: SET LOCAL_PY_DIR=%HOMEPATH%\Anaconda3
SET LOCAL_PY_DIR=C:\WinPython-64bit-2.7.10.3\python-2.7.10.amd64

%LOCAL_PY_DIR%\python frag_encode.py
timeout 3

@echo off
cd /d "%~dp0"
set "APP_URL=http://localhost:8000"
set "PORTABLE_PYTHON_LITE=%~dp0portable-python-lite\python.exe"
set "PORTABLE_PYTHON=%~dp0portable-python\python.exe"
set "PGADMIN_PYTHON_18=C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe"
set "PGADMIN_PYTHON_17=C:\Program Files\PostgreSQL\17\pgAdmin 4\python\python.exe"
set "PGADMIN_PYTHON_16=C:\Program Files\PostgreSQL\16\pgAdmin 4\python\python.exe"

if exist "%PORTABLE_PYTHON_LITE%" (
  echo Iniciando con Python portable liviano incluido en la carpeta...
  echo Abriendo: %APP_URL%
  start "" "%APP_URL%"
  "%PORTABLE_PYTHON_LITE%" server.py
) else if exist "%PORTABLE_PYTHON%" (
  echo Iniciando con Python portable incluido en la carpeta...
  echo Abriendo: %APP_URL%
  start "" "%APP_URL%"
  "%PORTABLE_PYTHON%" server.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    echo Iniciando con Python del sistema...
    echo Abriendo: %APP_URL%
    start "" "%APP_URL%"
    python server.py
  ) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
      echo Iniciando con el lanzador py de Windows...
      echo Abriendo: %APP_URL%
      start "" "%APP_URL%"
      py -3 server.py
    ) else if exist "%PGADMIN_PYTHON_18%" (
      echo Iniciando con Python incluido en pgAdmin/PostgreSQL 18...
      echo Abriendo: %APP_URL%
      start "" "%APP_URL%"
      "%PGADMIN_PYTHON_18%" server.py
    ) else if exist "%PGADMIN_PYTHON_17%" (
      echo Iniciando con Python incluido en pgAdmin/PostgreSQL 17...
      echo Abriendo: %APP_URL%
      start "" "%APP_URL%"
      "%PGADMIN_PYTHON_17%" server.py
    ) else if exist "%PGADMIN_PYTHON_16%" (
      echo Iniciando con Python incluido en pgAdmin/PostgreSQL 16...
      echo Abriendo: %APP_URL%
      start "" "%APP_URL%"
      "%PGADMIN_PYTHON_16%" server.py
    ) else (
      echo.
      echo No se encontro Python en este computador y tampoco esta portable-python.
      echo Copia la carpeta completa incluyendo portable-python.
      echo.
    )
  )
)

pause

@echo off

set INSTALLER="d:\Program Files\python23\Installer\Build.py"
set DIST=distalbumart-qt-w32

python %INSTALLER% albumart-qt-w32.spec
mkdir %DIST%\share
mkdir %DIST%\share\albumart
:mkdir %DIST%\lib
:mkdir %DIST%\lib\albumart
copy ..\..\share\albumart\*.png %DIST%\share\albumart
:copy ..\..\lib\albumart\albumart_source*.py %DIST%\lib\albumart
:copy ..\..\lib\albumart\albumart_target*.py %DIST%\lib\albumart

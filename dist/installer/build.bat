@echo off

set INSTALLER="\python23\Installer\Build.py"
set DIST=distalbumart-qt-w32

python %INSTALLER% albumart-qt-w32.spec
mkdir %DIST%\share
mkdir %DIST%\share\albumart
copy ..\..\share\albumart\*.png %DIST%\share\albumart
copy ..\..\README %DIST%\Readme.txt
copy ..\..\COPYING %DIST%\Copying.txt
copy ..\..\CHANGELOG %DIST%\Changelog.txt

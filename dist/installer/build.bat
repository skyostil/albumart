@python ..\..\..\Installer\Build.py albumart-qt.spec
@mkdir distalbumart-qt\share
@mkdir distalbumart-qt\share\albumart
@copy ..\..\share\albumart\*.png distalbumart-qt\share\albumart

#!/bin/sh

python ~/bin/Installer/Build.py albumart-qt.spec

mkdir distalbumart-qt/share
mkdir distalbumart-qt/share/albumart
cp -v ../../share/albumart/*.png distalbumart-qt/share/albumart
cp -v ../../README distalbumart-qt
upx -9 distalbumart-qt/albumart-qt

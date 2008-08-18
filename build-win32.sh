CX_FREEZE=c:/proj/cx_Freeze-3.0.3/FreezePython.exe
MAKENSIS=c:/Program\ Files/NSIS/makensis
PYUIC=/c/python24/bin/pyuic.exe

# Build everything
make PYUIC=$(PYUIC)

# Gather the dynamically loaded modules
MODULES=albumart_dialog,sip,encodings.iso8859_1,encodings.utf_8
for FN in lib/albumart/albumart_{source,target,recognizer}*.py; do
  FN=$(basename $FN)
  FN=${FN/.py/}
  MODULES=$MODULES,$FN
done

# Build the frozen binary
"$CX_FREEZE" --base-name Win32Gui --install-dir dist/win32 --include-path lib/albumart --include-modules $MODULES bin/albumart-qt

# Copy misc files
cp dist/win32-libs/*.dll dist/win32
cp copying dist/win32/copying.txt
cp readme dist/win32/readme.txt
unix2dos dist/win32/*.txt

# Build installer
"$MAKENSIS" dist/installer/albumart.nsi

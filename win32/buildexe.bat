@ECHO OFF
cd ..
python setup.py py2exe --dist-dir win32/dist --force --windows -O2

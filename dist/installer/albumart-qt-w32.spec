a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\..\\bin\\albumart-qt'],
             pathex=['..\\..\\bin', '..\\..\\lib\\albumart', 'C:\\Sami\\cvs\\albumart\\dist\\INSTAL~1'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='buildalbumart-qt-w32/albumart-qt.exe',
          debug=0,
          strip=0,
          upx=0,
          console=0 , icon='..\\..\\win32\\icon.ico')
coll = COLLECT( exe,
               a.binaries,
               strip=0,
               upx=0,
               name='distalbumart-qt-w32')

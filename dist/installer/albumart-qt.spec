a = Analysis([
               os.path.join(HOMEPATH,'support/_mountzlib.py'),
               os.path.join(HOMEPATH,'support/useUnicode.py'),
               '../../bin/albumart-qt'
             ],
             pathex=['../../bin', '../../lib/albumart'],
             hookspath=['.']
            )
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='buildalbumart-qt/albumart-qt',
          debug=0,
          strip=0,
          upx=0,
          console=1 )
coll = COLLECT( exe,
               a.binaries,
               strip=0,
               upx=1,
               name='distalbumart-qt')

import os

hiddenimports=[]
for f in os.listdir("../../lib/albumart/"):
    if (f.startswith("albumart_source") or f.startswith("albumart_target")) and f.endswith(".py"):
            hiddenimports.append(os.path.basename(f).split(".")[0])
print "Found modules:", hiddenimports

#hiddenimports=['albumart_source_amazon','albumart_target_windows','albumart_target_freedesktop']

#
# Various debug definitions and functions
#
import sys
import time

__version__ = "$Revision: 1.1 $"
__author__ = "Leif Hedstrom <leif@ogre.com>"
__date__ = "Tue Mar 29 10:21:42 PST 2005"


# Debug levels, 32 bits of "features"
DEBUG_LEVELS = { 'ALL' : 2**32-1,
                 'HTTP' : 2**0,
                 'PARAMS': 2**1,
                 'PARSING' : 2**2,
                 
                 # These are very verbose
                 'RAWXML' : 2**31,
                 }


#
# Simple class to use instead of "object", to enable
# debugging messages etc.
#
class Debuggable(object):
    def __init__(self, debug=0):
        self._debug_level = debug

    def _debug_msg(self, msg, level, *args):
        if self._debug_level & level:
            sys.stderr.write("[debug: ")
            text = msg % args
            if isinstance(text, unicode):
                try:
                    text = text.encode("utf-8")
                except:
                    text = msg + " (encode() failed!)"
            sys.stderr.write(text)
            sys.stderr.write("]\n")



#
# local variables:
# mode: python
# indent-tabs-mode: nil
# py-indent-offset: 4
# end:

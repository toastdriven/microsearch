# Python 3 compatibility.
from __future__ import print_function
from __future__ import unicode_literals

import os

try:
    import simplejson as json
except ImportError:
    import json


__author__ = 'Daniel Lindsley'
__license__ = 'BSD'
__version__ = (0, 1, 0)




import os
import sys
FILE_PATH = os.path.expanduser(__file__)
FILE_PATH = os.path.abspath(FILE_PATH)
if os.path.islink(FILE_PATH):
    FILE_PATH = os.readlink(FILE_PATH)
DIR_PATH = os.path.dirname(FILE_PATH)
NADBG_PATH = os.path.abspath(os.path.join(DIR_PATH, '../'))
sys.path.insert(0, NADBG_PATH)

from core.nadbg import nadbg

class Common(object):
    def __init__(self):
        pass
    @property
    def pid(self):
        return nadbg.pid

common = Common()
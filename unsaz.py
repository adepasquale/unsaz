#!/usr/bin/env python

import os
import sys
from zipfile import ZipFile

with ZipFile(sys.argv[1]) as sazfile:
    for f in sazfile.namelist():
        if f.startswith("raw/") and f.endswith(".txt"):
            print(sazfile.open(f).readline())


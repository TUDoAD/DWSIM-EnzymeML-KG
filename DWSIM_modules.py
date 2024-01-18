# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 15:04:30 2024

@author: Alexander Behr
"""

import os
import uuid
import clr 

# Importiere Python Module
import pythoncom
import System
pythoncom.CoInitialize()

from System.IO import Directory, Path, File
from System import String, Environment
from System.Collections.Generic import Dictionary

import EnzymeMLtoDWSIM-modules.py

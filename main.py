# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 19:35:20 2024

@author: Alexander Behr
"""

import ELNs_to_KG_modules
import DWSIM_modules


enz_str = "./ELNs/EnzymeML_Template_18-8-2021_KR.xlsm"
eln_str = "./ELNs/New-ELN_Kinetik_1.xlsx"
onto_str ="./ontologies/KG-DWSIM_EnzML_ELN.owl"
filename_DWSIM ="ABTS_ox.dwxmz"


ELNs_to_KG_modules.run()
DWSIM_modules.run(filename_DWSIM,enz_str,eln_str,onto_str)


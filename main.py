# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 19:35:20 2024

@author: Alexander Behr
"""

import ELNs_to_KG_modules
import DWSIM_modules

base_onto_str = "./ontologies/BaseOntology.owl"


enzml_XLSX_path = "./ELNs/EnzymeML_Template_18-8-2021_KR.xlsm"
pfd_XLSX_path = "./ELNs/New-ELN_Kinetik_1.xlsx"
base_ontology_path
extended_ontology_path


onto_str ="./ontologies/KG-DWSIM_EnzML_ELN.owl"
filename_DWSIM ="ABTS_ox.dwxmz"

##
# Loading the information stored in both enz_str and eln_str Excel-files
# and extending the BaseOntology with the data to a knowledge graph
# storing it in the file asserted in onto_str
PFD_iri = ELNs_to_KG_modules.run()

##
# Using the produced knowledge graph in onto_str 
##EXCEL STRINGS RAUS?
DWSIM_modules.run(filename_DWSIM,enz_str,eln_str,onto_str)


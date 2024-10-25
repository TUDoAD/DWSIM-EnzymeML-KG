# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 19:35:20 2024

@author: Alexander Behr
"""

import ELNs_to_KG_modules
import DWSIM_modules
#import individual_extr
#import robot_KG_shrinker

base_onto_path = "./ontologies/BaseOntology.owl"
#BaseOntology_for_CSTR.owl
#base_onto_path = "./ontologies/BaseOntology_for_CSTR.owl"

enzml_XLSX_path = "./ELNs/EnzymeML_Template_18-8-2021_KR.xlsm"
#enzml_XLSX_path = "./ELNs/EnzymeML_Template_Sain.xlsm"

pfd_XLSX_path = "./ELNs/New-ELN_Kinetik_1.xlsx"
#pfd_XLSX_path = "./ELNs/New-ELN_Kinetik_1_Sain_AB.xlsx"

extended_ontology_path ="./ontologies/KG-DWSIM_CSTR_ELN.owl"
filename_DWSIM ="Sain.dwxmz"

##
# Loading the information stored in both enz_str and eln_str Excel-files
# and extending the BaseOntology with the data to a knowledge graph
# storing it in the file asserted in onto_str
PFD_uuid = ELNs_to_KG_modules.run(enzml_XLSX_path,pfd_XLSX_path, base_onto_path, extended_ontology_path)

##
# Using the produced knowledge graph in onto_str 
##EXCEL STRINGS RAUS?
DWSIM_modules.run(filename_DWSIM,PFD_uuid,extended_ontology_path)


#individual_extr.run()
#robot_KG_shrinker.run()
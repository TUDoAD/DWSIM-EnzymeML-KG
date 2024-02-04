# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 10:48:42 2024

@author: smaxbehr
"""

from owlready2 import *

def run():
    onto = get_ontology("./ontologies/KG-DWSIM_EnzML_ELN_output_with_r4c_gca.owl").load()
    
    indv_list = list(onto.individuals())
    iri_list = [i.iri for i in indv_list]
    with open('iri_individuals.txt', 'w') as f:
        for entry in iri_list:    
            f.write(str(entry)+"\n")
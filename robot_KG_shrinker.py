# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 10:27:42 2023

@author: smaxbehr
"""

import os
from owlready2 import *

# URL: link to ontologie
# IRI-file: txt-file with the IRI's
# onto: name of the output-file
working_dir = os.getcwd()
#working_dir = "C://Users/smaxbehr/Documents/GitHub/DWSIM-EnzymeML-KGontologies/""

#URL = "https://raw.githubusercontent.com/nfdi4cat/Ontology-Overview-of-NFDI4Cat/main/ontologies/AFO.ttl"

URL = working_dir + "/ontologies/KG-DWSIM_EnzML_ELN.owl" #"C://Users/smmcvoel/Documents/GitHub/Abschlussarbeiten_Behr/VoelkenrathMA/ontologies/HuPSON_v092013_merged.owl"
IRI_file = "iri_individuals.txt"
onto_path = "ontologies/KG-DWSIM_EnzML_ELN_robotted.owl"

def run():
    
    # meth: methods can be found here [http://robot.obolibrary.org/extract]
    meth = "BOT"
    
    bashCommand = "java -jar {}/robot/robot.jar extract --input {} --method {} --term-file {} --output {} ".format(working_dir,URL, meth, IRI_file, onto_path)
    
    #bashCommand = "java -jar C://Users/smmcvoel/Documents/GitHub/Abschlussarbeiten_Behr/VoelkenrathMA/robot/robot.jar merge --input ontologies/MV-Onto.owl --input ontologies/Reac4Cat_Folgereaktion.owl --output ontologies/MV-Ontology.owl"
    
    
    os.system(bashCommand)
    
    
    object_props = ["ends after", "has participant", "participates in", "temporally related to", "has role", "has characteristic", "composed primarily of","has modifier"]
    class_props = ["occurrent", "continuant","specifically dependent continuant"]#,""]
    
    onto = get_ontology("./"+ onto_path).load()
    
    for prop_name in object_props:
        prop = onto.search_one(label = prop_name)
        prop.domain = None
        prop.range = None
    
    
    for class_name in class_props:
        prop = onto.search_one(label = class_name)
        if prop:
            for rel in prop.is_a:
                try:
                    if rel.property.iri == "http://purl.obolibrary.org/obo/BFO_0000050":
                        prop.is_a.remove(rel)
                except:
                    pass
    
    onto.save(file="./"+onto_path, format="rdfxml")
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  4 13:00:31 2024

@author: smaxbehr
"""

from owlready2 import *

onto = get_ontology("./ontologies/KG-DWSIM_EnzML_ELN_output_with_r4c.owl").load()

cat_name = "Laccase"

reacComp_prop_str = "hasReactionComponent"
potCatBy_prop_str ="isPotentiallyCatalysedBy"
cat_prop_str = "hasCatalyst"

with onto:
#(hasReactionComponent some ({Sub_Laccase})) and (isPotentiallyCatalysedBy some ({Sub_Laccase}) SubClassOf hasCatalyst some ({Sub_Laccase})
    cat_sub_indv = onto.search_one(label = cat_name).instances()[0]
    
    reacComp_rel = onto.search_one(label = reacComp_prop_str)
    potCatBy_rel = onto.search_one(label = potCatBy_prop_str)
    cat_rel = onto.search_one(label = cat_prop_str) 
    
    gca = GeneralClassAxiom(reacComp_rel.some(cat_sub_indv) & potCatBy_rel.some(cat_sub_indv)) # Left side
    gca.is_a.append(cat_rel.some(cat_sub_indv)) # Right side
      
#'Laccase Reaction' and (hasCatalyst some ((material entity or chemical entity) and (inverse (hasReactionComponent some 'Laccase Reaction'))) SubClassOf 'Catalysed Laccase Reaction'
#(hasEductComponent some ABTS_red) and (hasEductComponent some Oxygen) and (hasProductComponent some ABTS_ox) SubClassOf hasReactionRole some ({Laccase_reaction_indv})

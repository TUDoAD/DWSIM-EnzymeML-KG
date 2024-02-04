# -*- coding: utf-8 -*-
"""
Created on Sun Feb  4 13:00:31 2024

@author: smaxbehr
"""

from owlready2 import *

onto = get_ontology("./ontologies/KG-DWSIM_EnzML_ELN_output.owl").load()


with onto:
#(hasReactionComponent some ({Sub_Laccase})) and (isPotentiallyCatalysedBy some ({Sub_Laccase}) SubClassOf hasCatalyst some ({Sub_Laccase})
    cat_sub_indv = onto.search_one(label = subst)
    gca = GeneralClassAxiom(onto.hasReactionComponent.some() & onto.has_location.some(onto.Heart)) # Left side
    gca.is_a.append(onto.CardiacDisorder) # Right side
      
#'Laccase Reaction' and (hasCatalyst some ((material entity or chemical entity) and (inverse (hasReactionComponent some 'Laccase Reaction'))) SubClassOf 'Catalysed Laccase Reaction'
#(hasEductComponent some ABTS_red) and (hasEductComponent some Oxygen) and (hasProductComponent some ABTS_ox) SubClassOf hasReactionRole some ({Laccase_reaction_indv})

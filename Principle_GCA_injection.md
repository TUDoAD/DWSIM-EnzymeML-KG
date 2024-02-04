## General Class Axioms to infer:

(hasReactionComponent some ({Sub_Laccase})) and (isPotentiallyCatalysedBy some ({Sub_Laccase}) SubClassOf hasCatalyst some ({Sub_Laccase})

'Laccase Reaction' and (hasCatalyst some ((material entity or chemical entity) and (inverse (hasReactionComponent some 'Laccase Reaction'))) SubClassOf 'Catalysed Laccase Reaction'

(hasEductComponent some ABTS_red) and (hasEductComponent some Oxygen) and (hasProductComponent some ABTS_ox) SubClassOf hasReactionRole some ({Laccase_reaction_indv})


## Entities
hasReactionComponent = r4c - has input, has output
{Sub_Laccase} = Indv. of substance Laccase
isPotentiallyCatalysedBy = r4c
hasCatalyst = r4c

'Laccase Reaction' = SubClassOf (redox reaction) http://biomodels.net/SBO/SBO_0000200
material entity = http://biomodels.net/SBO/SBO_0000240 (material entity, or BFO_0000040)
chemical entity = NONE
'Catalysed Laccase Reaction' = SubClassOf 'Laccase Reaction'


hasEductComponent = has input
ABTS_red = self
Oxygen = self
hasProductComponent = has output
ABTS_ox = self
hasReactionRole = r4c
{Laccase_reaction_indv} = self

## General Class Axioms to infer:

(hasReactionComponent some ({Sub_Laccase})) and (isPotentiallyCatalysedBy some ({Sub_Laccase}) SubClassOf hasCatalyst some ({Sub_Laccase})

'Laccase Reaction' and (hasCatalyst some ((material entity or chemical entity) and (inverse (hasReactionComponent some 'Laccase Reaction'))) SubClassOf 'Catalysed Laccase Reaction'

(hasEductComponent some ABTS_red) and (hasEductComponent some Oxygen) and (hasProductComponent some ABTS_ox) SubClassOf hasReactionRole some ({Laccase_reaction_indv})


## Entities
hasReactionComponent = 
{Sub_Laccase} =
isPotentiallyCatalysedBy = 
hasCatalyst =

'Laccase Reaction' = (RedOX reaction
material entity =
chemical entity =
'Catalysed Laccase Reaction' = (catalysed RedOX reaction)


hasEductComponent =
ABTS_red = 
Oxygen = 
hasProductComponent =
ABTS_ox =
hasReactionRole =
{Laccase_reaction_indv} =

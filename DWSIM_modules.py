# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 15:04:30 2024

@author: Alexander Behr
"""

import os
import uuid

import clr 

from owlready2 import *

# Importiere Python Module
import pythoncom
import System
pythoncom.CoInitialize()

from System.IO import Directory, Path, File
from System import String, Environment
from System.Collections.Generic import Dictionary

import ELNs_to_KG_modules
# Path to DWSIM-Directory

dwsimpath = os.getenv('LOCALAPPDATA') + "\\DWSIM8\\"

clr.AddReference(dwsimpath + "DWSIM")
clr.AddReference(dwsimpath + "CapeOpen.dll")
clr.AddReference(dwsimpath + "DWSIM.Automation.dll")
clr.AddReference(dwsimpath + "DWSIM.Interfaces.dll")
clr.AddReference(dwsimpath + "DWSIM.GlobalSettings.dll")
clr.AddReference(dwsimpath + "DWSIM.SharedClasses.dll")
clr.AddReference(dwsimpath + "DWSIM.Thermodynamics.dll")
clr.AddReference(dwsimpath + "DWSIM.UnitOperations.dll")
clr.AddReference(dwsimpath + "DWSIM.Inspector.dll")
clr.AddReference(dwsimpath + "System.Buffers.dll")
clr.AddReference(dwsimpath + "DWSIM.MathOps.dll")
clr.AddReference(dwsimpath + "TcpComm.dll")
clr.AddReference(dwsimpath + "Microsoft.ServiceBus.dll")
clr.AddReference(dwsimpath + "DWSIM.FlowsheetSolver.dll")
clr.AddReference("System.Core")
clr.AddReference("System.Windows.Forms")
clr.AddReference(dwsimpath + "Newtonsoft.Json")

from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
from DWSIM.Thermodynamics import Streams, PropertyPackages
from DWSIM.UnitOperations import UnitOperations, Reactors
from DWSIM.Automation import Automation3
from DWSIM.GlobalSettings import Settings

from enum import Enum
# Paket, um Kalkulationen durchzuführen 
from DWSIM import FlowsheetSolver
# Paket, um ein neues Fließbild zu erstellen und darauf zuzugreifen
from DWSIM import Interfaces
from System import *

from System.Linq import *
from DWSIM import *
#from DWSIM import FormPCBulk
from DWSIM.Interfaces import *
from DWSIM.Interfaces.Enums import*

# Paket, um Fließbild zu zeichnen
from DWSIM.Interfaces.Enums.GraphicObjects import *

# Paket, um neu erstellte Komponenten als JSON datei abzuspeichern
from Newtonsoft.Json import JsonConvert, Formatting

from DWSIM.Thermodynamics import*
from DWSIM.Thermodynamics.BaseClasses import *
from DWSIM.Thermodynamics.PropertyPackages.Auxiliary import *

# Pakte, um Pseudocompound Creator auszuführen
from DWSIM.Thermodynamics.Utilities.PetroleumCharacterization import GenerateCompounds
from DWSIM.Thermodynamics.Utilities.PetroleumCharacterization.Methods import *

###
def data_ini(enzymeML_ELN_path,process_ELN_path,ontology_path):
    onto = owlready2.get_ontology(ontology_path).load()
    onto.name = "onto"
    enzdict, eln_dict = ELNs_to_KG_modules.eln_to_dict(enzymeML_ELN_path,process_ELN_path)
    return enzdict, eln_dict, onto
##

##
def flowsheet_simulation(onto, pfd_iri):
        #enz_dict, pfd_dict, onto, pfd_iri): 
    working_dir = os.getcwd()
    Directory.SetCurrentDirectory(dwsimpath)
    # Automatisierungsmanager erstellen
    # Create automatin manager
    interf = Automation3()
    sim = interf.CreateFlowsheet()
    sim.CreateAndAddPropertyPackage("Raoult's Law")

    ## 
    pfd_ind = onto.search_one(iri = pfd_iri)
    pfd_list = pfd_ind.BFO_0000051 # has part
        
    comp_list = [] # lists the components contained in the PFD
    process_streams = [] # lists the stream info for the flowsheet 
            
    # "subst_indv": ontology_individual, "subst_class": ontology_class, "subst_role": role of the individual in the PFD (reactant, product, catalyst,...)
    for module in pfd_list:
        if module.is_a[0].label.first() == "EnergyStream":
            # add energy streams to stream_names for later input in stream creation
            process_streams.append(module)
        
        elif module.is_a[0].label.first() == "MaterialStream":
            materialstream = module.BFO_0000051 # has part
            
            # add material streams to stream_names for later input in stream creation
            process_streams.append(module)
            
            for comp in materialstream:
                mat = comp.RO_0002473.first() # composed primarily of
                subst = mat.is_a.first() 
                role = mat.RO_0000087.first().name # has role
                comp_list.append({"subst_indv":mat, "subst_class": subst, "subst_role":role})
                #print(mat,subst, role) # substance individual, substance class, role [product, reactant]
        try:
            if module.RO_0000087.first().name == "product":# has role
                subst = module.is_a.first()
                role = module.RO_0000087.first() # has role
                comp_list.append({"subst_indv":module, "subst_class": subst, "subst_role":role})#print(module,module.is_a,module.RO_0000087.first().name) # substance individual, substance class, role [product, reactant]
        except:
            pass
    
    #loading components into DWSIM-simulation and filling dictionaries regarding
    # stoichiometric coefficients and reaction order coeffs.
    
    comps = Dictionary[str, float]()
    dorders = Dictionary[str, float]()
    rorders = Dictionary[str, float]()
    
    
    for comp in comp_list:
        # add label of class (= substance name) to the DWSIM-Simulation
        # comp
        subst_class_name = comp["subst_class"].label.first()
        stoich_coeff = comp["subst_indv"].hasStoichiometricCoefficient.first()
        dorder_coeff = comp["subst_indv"].hasDirect_OrderCoefficient.first()
        rorder_coeff = comp["subst_indv"].hasReverse_OrderCoefficient.first()
        
        # add compount to dwsim simulation class
        sim.AddCompound(subst_class_name)
        
        # add coefficents to dictionaries to prepare for creation of reaction
        comps.Add(subst_class_name, stoich_coeff)
        dorders.Add(subst_class_name, dorder_coeff)
        rorders.Add(subst_class_name, rorder_coeff) 
        
        if comp["subst_role"] == "catalyst":
            #has characteristic -> kinetics
            kin_indv = comp["subst_indv"].RO_0000053 
            substrate_indv = []
            for indv in kin_indv: # might be more than one substrate
                # has input -> input = substrate of reaction    
                substrate_indv.append(indv.RO_0002233)
    
    ## Add streams to DWSIM:
    
    # Add starting streams of flow sheet
    stream_info = []
    #for later reference, streams lists the dwsim-object-representation of the streams 
    streams = {}
    # Start at y = 0, x=0
    y_axis = 0
    for stream_indv in process_streams:
        # if the property output of (RO_0002353) returns an empty list -> Start of the flowsheet
        if not stream_indv.RO_0002353:
            #print(stream_indv.label)
            stream_type = stream_indv.is_a[0].label.first()
            stream_name = stream_indv.label.first()
            codestr = """stream = sim.AddObject(ObjectType.{}, 0,{},'{}')
streams['{}'] = stream""".format(stream_type,y_axis,stream_name,stream_name)
            #codestr = """stream_info.append({{'type': ObjectType.{}, 'x': 0, 'y': {}, 'name': '{}'}})""".format(stream_type,y_axis,stream_name)
            code = compile(codestr, "<string>","exec")
            exec(code)
            y_axis += 50
            if stream_indv.is_a[0].label.first() == "MaterialStream":
                
                subst_indv = stream_indv.BFO_0000051 # has part
                
                ## set molar flows of compounds
                for sub_stream in subst_indv:
                    substance = sub_stream.RO_0002473.first().is_a.first().label.first() #composed primarily of
                    if sub_stream.hasCompoundMolarFlowUnit.first().replace(" ","") in ["mol/s","mols^-1"]:
                        mol_flow = float(sub_stream.hasCompoundMolarFlow.first())
                    else:
                        print("compound molar flow unit not recognized: {} in stream {}".format(substance,sub_stream.label.first()))
                        mol_flow = 0
                    
                    #print("stream_name: {}, substance:{}, mol_flow:{}".format(stream_name, substance, mol_flow))
                    streams[stream_name].GetAsObject().SetOverallCompoundMolarFlow(substance,mol_flow)
                
                # set overall volume flow
                try: 
                    if stream_indv.hasVolumetricFlowUnit.first().replace(" ","") in ["m3/s","m^3s^-1", "m^3/s", "m3s-1"]:
                        streams[stream_name].GetAsObject().SetVolumetricFlow(float(stream_indv.overallVolumetricFlow.first()))
                except:
                    print(stream_name + ": No volumetric flow defined")
                
                
                ## set temperature
                if subst_indv.first().hasTemperature:
                    if subst_indv.first().hasTemperatureUnit.first() in ["C","c","°c", "°C","Celsius","celsius"]:
                        temp = float(subst_indv.first().hasTemperature.first()) + 273.15
                    else:
                        temp = float(subst_indv.first().hasTemperature.first())
                    streams[stream_name].GetAsObject().SetTemperature(temp)
                
                

    #Add the streams and other objects (mixer, reactor, ...) to the simulation Flowsheet
    stream_info = []
    y_axis = 0
    x_axis = 100   
    codestr = ""
    for stream_indv in process_streams:
        # if the property output of (RO_0002353) returns an empty list -> Start of the flowsheet
        #if not stream_indv.RO_0002353: # output of -> starting streams
        next_modules = stream_indv.RO_0002234 # has output
        for module in next_modules:                
            module_type = module.is_a[0].label.first()
            module_name = module.label.first()
            module_names = list(streams.keys())
            # check, if module was already added to the simulation
            # only when true, go further downstream and add the has output streams
            if module_name not in module_names:
                codestr = """stream = sim.AddObject(ObjectType.{},{},{},'{}')\n""".format(module_type,x_axis, y_axis,module_name)
                codestr += """streams['{}'] = stream""".format(module_name)
                #stream = eval("sim.AddObject(ObjectType.{},{},{},'{}')".format(module_type,x_axis, y_axis,module_name))
                #eval("streams['{}'] =stream".format(module_name))
                #stream = None
                #codestr = """stream_info.append({{'type': ObjectType.{}, 'x': 0, 'y': {}, 'name': '{}'}})""".format(stream_type,y_axis,stream_name)
                code = compile(codestr, "<string>","exec")
                exec(code)
#                codestr = """stream_info.append({{'type': ObjectType.{}, 'x': {}, 'y': {}, 'name': '{}'}})""".format(module_type,x_axis, y_axis,module_name)
#                code = compile(codestr, "<string>","exec")
                #exec(code)
                x_axis += 100
                
                # take a look on next stream, going out from last module
                next_streams = module.RO_0002234
                for stream in next_streams:
                    stream_type = stream.is_a[0].label.first()
                    stream_name = stream.label.first()
                    stream_names = [i["name"] for i in stream_info]
                    if stream_name not in stream_names: 
                        codestr = """stream = sim.AddObject(ObjectType.{},{},{},'{}')\n""".format(stream_type,x_axis,y_axis,stream_name)
                        codestr += """streams['{}'] = stream\n""".format(stream_name)
                        code = compile(codestr, "<string>","exec")
                        exec(code)
                        #eval("streams['{}'] = sim.AddObject(ObjectType.{},{},{},'{}')".format(stream_name,stream_type,x_axis,y_axis,stream_name))
                        #codestr = """stream_info.append({{'type': ObjectType.{}, 'x': {}, 'y': {}, 'name': '{}'}})""".format(stream_type,x_axis, y_axis,stream_name)
                        x_axis += 100

    #iterate through pfd_list connect the objects, direction of connection comes
    # with RO_0002234 (has output) and RO_0002353 (output of)
    for pfd_obj in process_streams:
        obj_name = pfd_obj.label.first()  
        obj_1 = streams[obj_name].GetAsObject().GraphicObject
        
        output_objects = pfd_obj.RO_0002234 # has_output -> obj_1 connected to obj_2
        input_objects = pfd_obj.RO_0002353 # output of -> obj_2 connected to obj_1
        
        for out_obj in output_objects:
            obj_2_name = out_obj.label.first()
            obj_2 = streams[obj_2_name].GetAsObject().GraphicObject
            sim.ConnectObjects(obj_1,obj_2, -1,-1)
        
        for inp_obj in input_objects:
            obj_2_name = inp_obj.label.first()
            obj_2 = streams[obj_2_name].GetAsObject().GraphicObject
            sim.ConnectObjects(obj_2,obj_1, -1,-1)
            
    
    ## Add special information to modules
    # 
    reactor_list = []
    for module in pfd_list:
        # Add information to reactors
        if module.is_a[0].label.first() in ["RCT_PFR","RCT_Conversion","RCT_Equilibrium","RCT_Gibbs","RCT_CSTR"]:
            # WARNING: Reactors other than "RCT_PFR" might not work properly yet!    
            dwsim_obj = streams[module.label.first()].GetAsObject()
            reactor_list.append(module)
            dwsim_obj.ReactorOperationMode = Reactors.OperationMode(int(module.hasTypeOf_OperationMode.first()))
            if module.is_a[0].label.first() == "RCT_PFR":
                dwsim_obj.ReactorSizingType = Reactors.Reactor_PFR.SizingType.Length
                
            dwsim_obj.Volume= float(module.hasVolumeValue.first())
            dwsim_obj.Length= float(module.hasLengthValue.first())
            dwsim_obj.UseUserDefinedPressureDrop = True
            dwsim_obj.UserDefinedPressureDrop = float(module.hasDeltaP.first())
    
    ##
    # Add reaction(s)    
    if kin_indv:
        substrate_list = []
        i = 0
        for sub_ind in substrate_indv:
            # get label(s) of class of substrate individual(s)
            substrate_list.extend([i.is_a.first().label.first() for i in sub_ind])
        
        #TODO: split for arrhenius kinetic (default) and custom reaction kinetics
        #-> iterating kin_indv -- <has role in modeling> --> reactions
        
        for kin_ind in kin_indv:
            react_list = kin_ind.RO_0003301
            #print(react_list)
            for reaction in react_list: #enz_dict["reaction_dict"]:
                kr1 = sim.CreateKineticReaction(reaction.id.first(), "", comps, dorders, rorders, substrate_list[0], "Mixture", "Molar Fraction", "mol/m3", "mol/[m3.s]", 0.5, 0.0, 0.0, 0.0, "", "")  
                sim.AddReaction(kr1)
                sim.AddReactionToSet(kr1.ID, "DefaultSet", True, 0)   
                
                # add py-script for own kinetics Equation:
                script_name =kr1.ID# reaction.label.first()#enz_dict["reaction_dict"][reaction.id.first()]["name"]
                
                #sim = createScript(sim,script_name)                
                sim.Scripts.Add(script_name, FlowsheetSolver.Script())
                
                #custom_reac = sim.GetReaction(kr1.ID)
                custom_reac_script = sim.Scripts[script_name]
                custom_reac_script.Title = script_name
                custom_reac_script.ID = str(i)
                
                reac_inlet_name = ""
                
                #first Reactor in reactor_list --output of (RO_0002353)-> Input of Reactor individual
                # reactor_list.RO_0002353
                if reactor_list:
                    for reactor in reactor_list:
                        for inp_stream in reactor.RO_0002353:
                            if inp_stream.is_a.first().label.first() == "MaterialStream": 
                                reac_inlet_name = inp_stream.label.first()
                                #print("Reactor found. Inlet stream name "+reac_inlet_name)                              
                
                if reac_inlet_name == "": 
                    print("Warning: No Reactor found to apply kinetics to!")
                
                #print(reac_inlet_name)
                    
                catalysts = kin_ind.RO_0000052 # characteristic of
                code_str = "import math\n"# +"reactor = Flowsheet.GetFlowsheetSimulationObject('{}')\n".format(reactor_name)
                code_str += """
obj = Flowsheet.GetFlowsheetSimulationObject('{}')

n = obj.GetPhase('Overall').Properties.molarflow # mol/s
Q = obj.GetPhase('Overall').Properties.volumetric_flow # m3/s

concentration_flow = n/Q # mol/m3

# Access to compound list
values = obj.GetOverallComposition()
compsids = obj.ComponentIds
comp_dict = {{}}

for i in range(len(compsids)):
    comp_dict[compsids[i]] = values[i]
""".format(reac_inlet_name)
                if type(catalysts) == owlready2.prop.IndividualValueList: 
                    for cat in catalysts:
                        code_str += cat.hasEnzymeML_ID.first() + " = " + "comp_dict['" + cat.is_a.first().label.first() + "']*concentration_flow\n"
                else:
                    code_str += catalysts.hasEnzymeML_ID.first() + " = " + "comp_dict['" + catalysts.is_a.first().label.first() + "']*concentration_flow\n"
                    
                    
                reactants = kin_ind.RO_0002233  # has input
                if type(reactants) == owlready2.prop.IndividualValueList:
                    for react in reactants:
                        code_str += react.hasEnzymeML_ID.first() + " = " + "comp_dict['" + react.is_a.first().label.first() + "']*concentration_flow\n"
                else:
                    code_str += reactants.hasEnzymeML_ID.first() + " = " + "comp_dict['" + reactants.is_a.first().label.first() + "']*concentration_flow\n"
       
                variables = kin_ind.hasVariable
                if type(variables) == owlready2.prop.IndividualValueList:
                    for var in variables:
                        code_str += str(var.label.first()) + " = " + str(var.hasValue.first()) + "\n"
                else:
                    code_str += variables.label + " = " + str(variables.hasValue.first()) + "\n"
                    
                kin_equation = kin_ind.has_equation.first()
                code_str += "r =" + kin_equation
                
                custom_reac_script.ScriptText = code_str 
                
                new_reaction = sim.GetReaction(script_name)  
                new_reaction.ReactionKinetics = ReactionKinetics(1)
                new_reaction.ScriptTitle = script_name
                
                i +=1
    ##

    errors = interf.CalculateFlowsheet4(sim)
    if (len(errors) > 0):
        for e in errors:
            print("Error: " + e.ToString())    

    Directory.SetCurrentDirectory(working_dir)
    return sim, interf, streams, pfd_list

##
def extend_knowledgegraph(sim,onto,streams, pfd_list,pfd_iri):
    #sim = DWSIM simulation object
    #onto = Knowledge Graph to be extended
    #streams = Dictionary of {Stream_name : DWSIM-object,...}
    #pfd_list = list of all individuals connected to pfd_iri in Knowledge Graph
    #pfd_iri = IRI of PFD object 
    
    for datProp in ["overallMolarFlow","hasMolarFlowUnit", "hasMolarity","hasMolarityUnit"]:
        onto = ELNs_to_KG_modules.datProp_from_str(datProp,onto)
        
    pfd_ind = onto.search_one(iri = pfd_iri)
    pfd_dict = {} 
    phase_dict = {}
    
    for i in pfd_list:
        pfd_dict[i.label.first()]=i
    
    for stream in streams:
        dwsim_obj = streams[stream].GetAsObject()
        onto_obj = pfd_dict[stream]
        
        if "MaterialStream" in onto_obj.is_a.first().label:
            stream_comp_ids = list(dwsim_obj.ComponentIds)
            stream_composition = list(dwsim_obj.GetOverallComposition())
            molar_flow = dwsim_obj.GetMolarFlow()
            volume_flow = dwsim_obj.GetVolumetricFlow()
            
            ## get phase information
            for phase_no in range(dwsim_obj.GetNumPhases()):
            
                mol_flow = dict(dwsim_obj.get_Phases())[phase_no].Properties.get_molarflow() #mol/s
                vol_flow = dict(dwsim_obj.get_Phases())[phase_no].Properties.get_volumetric_flow() #m3/s
                
                #print(onto_obj.label)
                if mol_flow and vol_flow:                
                    f = mol_flow / vol_flow /1000 # mol/L
                    conc_dict = {}
                    for i in range(len(list(dwsim_obj.GetPhaseComposition(int(phase_no))))):
                        conc_dict[stream_comp_ids[i]] = f * list(dwsim_obj.GetPhaseComposition(int(phase_no)))[i]
                        #conc_list.append(conc_dict)
                    
                    phase_dict[str(onto_obj.label.first())] = {str(dict(dwsim_obj.get_Phases())[int(phase_no)].ComponentName): conc_dict}
            ##
            
            
            ## add information to ontology
            onto_obj.overallVolumetricFlow = [str(volume_flow)]
            onto_obj.hasVolumetricFlowUnit = ["m3/s"]
            onto_obj.overallMolarFlow = [str(molar_flow)]
            onto_obj.hasMolarFlowUnit = ["mol/s"]
            #

            # add Molarities to the sub-material streams
            if onto_obj.BFO_0000051: # has part (partial material stream)
                for submat_stream in onto_obj.BFO_0000051:
                    material_label = submat_stream.RO_0002473[0].is_a[0].label.first()
                    #submat_stream.label.first()
                    conc_dict = phase_dict[onto_obj.label.first()]
                    
                    for phase in conc_dict:
                        key_list = conc_dict[phase].keys()
                        #add molarities
                        if material_label in key_list:
                            submat_stream.hasMolarity = [conc_dict[phase][material_label]]
                            submat_stream.hasMolarityUnit = ["mol/L"]
                        
                        # assert phase
                        if "Liquid" in phase: #DWSIM asserts "OverallLiquid" for liquid phases
                            submat_stream.hasAggregateState.append("Liquid")
                        else:
                            submat_stream.hasAggregateState.append(phase)# Vapor,..
         
            
            else: #no partial material stream(s) detected or missing       
                conc_dict = phase_dict[onto_obj.label.first()]
                stream_name = onto_obj.label.first()
                
                for phase in conc_dict:
                    key_list = conc_dict[phase].keys()
                    
                    for subst in key_list:
                        onto, substream_uri = onto_substream_from_name(onto, stream_name, subst)
                        substream = onto.search_one(iri = substream_uri)
                        
                        onto_obj.BFO_0000051.append(substream)#hasPart
                        ## search for the correct substance individual in pfd_dict
                        for key in pfd_dict:
                            if pfd_dict[key].is_a.first().label.first() == material_label:
                                substream.RO_0002473 = [pfd_dict[key]] #consists primarily of
                    
                    # add molarities
                    if material_label in key_list:
                        substream.hasMolarity = [conc_dict[phase][material_label]]
                        substream.hasMolarityUnit = ["mol/L"]
                
                    # assert phase
                    if "Liquid" in phase: #DWSIM asserts "OverallLiquid" for liquid phases
                        substream.hasAggregateState.append("Liquid")
                    else:
                        substream.hasAggregateState.append(phase)# Vapor,..
                   
    return onto

##

def onto_substream_from_name(onto, stream_name, subst_name):
    uuid_str = "PFD_" + str(uuid.uuid4()).replace("-","_")
    substream = onto.search_one(label = "MaterialStream")(uuid_str)
    substream.label = stream_name + "_" + subst_name
    substream_iri = substream.iri  
    
    return onto, substream_iri



##
def save_simulation(sim,interface, filename):
    fileNameToSave = Path.Combine(os.getcwd(),filename)
    interface.SaveFlowsheet(sim, fileNameToSave, True)

##


def simulate_in_subprocess():
    command = ['python', 'run()']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.wait()


##
def ini():
    enz_str = "./ELNs/EnzymeML_Template_18-8-2021_KR.xlsm"
    eln_str = "./ELNs/New-ELN_Kinetik_1.xlsx"
    onto_str ="./ontologies/KG-DWSIM_EnzML_ELN.owl"
    
    enz_dict, pfd_dict, onto = data_ini(enz_str, eln_str, onto_str)
    return enz_dict, pfd_dict, onto

##


##
def run():
    enz_dict, pfd_dict, onto = ini()
    
    filename_DWSIM = "./DWSIM/ABTS_ox.dwxmz"
    filename_KG = "./ontologies/KG-DWSIM_EnzML_ELN_output.owl"
    
    pfd_ind = onto.search_one(label = "Experiment_"+enz_dict["name"])
    
    print("Data initialized, ontology loaded...")
    
    pfd_iri = pfd_ind.iri
    sim, interface, streams,pfd_list = flowsheet_simulation(onto,pfd_iri)
    
    print("Storing DWSIM-file: "+filename_DWSIM)
    save_simulation(sim,interface,filename_DWSIM)
    
    print("Integrating new information into Knowledge Graph")
    onto = extend_knowledgegraph(sim, onto, streams, pfd_list, pfd_iri)
    print("Storing Knowledge Graph: "+filename_KG)
    onto.save(file =filename_KG, format ="rdfxml")
    
    #return streams, pfd_list




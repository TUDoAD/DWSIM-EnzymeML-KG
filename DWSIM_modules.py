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
def flowsheet_ini(enz_dict, pfd_dict, onto, pfd_iri): 
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
    
    ## Test kinetic reaction
    #TODO: Decide later whether to deprecate this section?
    substrate_list = []
    for sub_ind in substrate_indv:
        # get label(s) of class of substrate individual(s)
        substrate_list.extend([i.is_a.first().label.first() for i in sub_ind])
    
    for reaction in enz_dict["reaction_dict"]:
        kr1 = sim.CreateKineticReaction(reaction, "", comps, dorders, rorders, substrate_list[0], "Mixture", "Molar Fraction", "", "mol/[m3.s]", 0.5, 0.0, 0.0, 0.0, "", "")  
        sim.AddReaction(kr1)
        sim.AddReactionToSet(kr1.ID, "DefaultSet", True, 0)   
    
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
    for module in pfd_list:
        # Add information to reactors
        if module.is_a[0].label.first() in ["RCT_PFR","RCT_Conversion","RCT_Equilibrium","RCT_Gibbs","RCT_CSTR"]:
            # WARNING: Reactors other than "RCT_PFR" might not work properly yet!    
            dwsim_obj = streams[module.label.first()].GetAsObject()
            dwsim_obj.ReactorOperationMode = Reactors.OperationMode(int(module.hasTypeOf_OperationMode.first()))
            if module.is_a[0].label.first() == "RCT_PFR":
                dwsim_obj.ReactorSizingType = Reactors.Reactor_PFR.SizingType.Length
           
            dwsim_obj.Volume= float(module.hasVolumeValue.first())
            dwsim_obj.Length= float(module.hasLengthValue.first())
            dwsim_obj.UseUserDefinedPressureDrop = True
            dwsim_obj.UserDefinedPressureDrop = float(module.hasDeltaP.first())


    Directory.SetCurrentDirectory(working_dir)
    return sim, interf, streams
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
    onto_str ="./ontologies/KG-DWSIM_Lab.owl"
    
    enz_dict, pfd_dict, onto = data_ini(enz_str, eln_str, onto_str)
    return enz_dict, pfd_dict, onto

##
enz_dict, pfd_dict, onto = ini()
pfd_ind = onto.search_one(label = "DWSIM_"+enz_dict["name"])
pfd_iri = pfd_ind.iri

##
def run():
    
    pfd_iri = pfd_ind.iri
    sim, interface, streams = flowsheet_ini(enz_dict,pfd_dict,onto,pfd_iri)
    filename = "ABTS_ox.dwxmz"
    save_simulation(sim,interface,filename)
    
    return sim, streams
##

#TODO: subprocess?
#TODO: reconstruct PFD from ontology
#TODO: set up pipeline for information retrieval from Knowledge gaph

"""
pfd_ind = onto.search_one(label = "DWSIM_"+enz_dict["name"])
pfd_list = pfd_ind.BFO_0000051

for module in pfd_list:
    if module.is_a[0].label.first() == "MaterialStream":
        materialstream = module.BFO_0000051
        for comp in materialstream:
            mat = comp.RO_0002473.first()
            subst = mat.is_a
            role = mat.RO_0000087.first().name
            print(mat,subst, role)
    try:
        if module.RO_0000087.first().name == "product":# has role
            print(module,module.is_a,module.RO_0000087.first().name)
    except:
        pass

##
"""

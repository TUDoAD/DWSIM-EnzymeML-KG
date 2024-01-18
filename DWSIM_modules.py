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
def flowsheet_ini(): 
    working_dir = os.getcwd()
    Directory.SetCurrentDirectory(dwsimpath)
    # Automatisierungsmanager erstellen
    # Create automatin manager
    interf = Automation3()
    sim = interf.CreateFlowsheet()

    # Komponenten für die Simulation laden
    compounds = [catalysts[0], main_substrates[0], main_products[0], reactants[0], reactants[1]]

    for comp in compounds:
        sim.AddCompound(comp)
             
    # Zugriff auf die Koeffizienten
    # Komponentenliste kann beliebig lang sein
    stoich_coeffs = {}  
    direct_order_coeffs = {}  
    reverse_order_coeffs = {}   

    for comp in compounds:
        stoich_coeffs[comp] = onto.search_one(label=comp).hasStoichiometriCoefficient.first()
        direct_order_coeffs[comp] = onto.search_one(label=comp).hasDirect_OrderCoefficient.first()
        reverse_order_coeffs[comp] = onto.search_one(label=comp).hasReverse_OrderCoefficient.first()

    # Dictionary, um Komponentennamen und Koeff zu sichern
    # Mit der zweiten Zeile können die jeweiligen Koeff geupdatet werden
    comps = {}
    comps.update(stoich_coeffs)

    dorders = {}
    dorders.update(direct_order_coeffs)

    rorders = {}
    rorders.update(reverse_order_coeffs)

    # Dictionary festlegen   
    comps = Dictionary[str, float]()
    dorders = Dictionary[str, float]()
    rorders = Dictionary[str, float]()
    
    Directory.SetCurrentDirectory(working_dir)
    return sim
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
##
def run():
    sim = flowsheet_ini()

##

#TODO: subprocess?


#TODO: reconstruct PFD from ontology
#TODO: set up pipeline for information retrieval from Knowledge gaph
pfd_ind = onto.search_one(label = "DWSIM_"+enz_dict["name"])
pfd_list = pfd_ind.BFO_0000051

for module in pfd_list:
    if module.is_a[0].label.first() == "MaterialStream":
        materialstream = module.BFO_0000051
        for comp in materialstream:
            mat = comp.RO_0002473.first()
            subst = mat.is_a
            role = mat.RO_0000087.first().name
            print(mat, role)

##


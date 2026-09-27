import os
import re
from typing import Tuple, List

from utilities.colour import prRed
from utilities.constants import (
    get_cross_sections_df_interference,
    maximum_leptoquark_mass,
    minimum_leptoquark_mass,
)
from utilities.data_classes import LeptoquarkParameters


def getAvailableCouplings(leptoquark_model: str) -> set:
    return {
        coupling
        for coupling in get_cross_sections_df_interference(leptoquark_model).columns
        if coupling != "Mass" and "_" not in coupling
    }


def _toDataCoupling(coupling: str) -> str:
    input_match = re.fullmatch(r"([XY])10([LR]{2})\[([1-3]),([1-3])\]", coupling)
    if input_match:
        particle, chirality, quark_generation, lepton_generation = input_match.groups()
        return (
            f"{particle}{quark_generation}{lepton_generation}{chirality}"
            f"{quark_generation}x{lepton_generation}"
        )

    data_match = re.fullmatch(r"([XY][1-3]{2}[LR]{2}[1-3])[xX]([1-3])", coupling)
    if data_match:
        return f"{data_match.group(1)}x{data_match.group(2)}"

    return coupling


def getUnavailableCouplings(couplings: List[str], leptoquark_model: str) -> List[str]:
    available_couplings = getAvailableCouplings(leptoquark_model)
    return [
        coupling
        for coupling in couplings
        if _toDataCoupling(coupling) not in available_couplings
    ]

def checkIfFilesExist(files: List[str]):
    for file in files:
        if not os.path.isfile(file):
            # create file if it does not exist
            with open(file, 'w') as file:
                pass

def validateInputData(
    leptoquark_model: str,
    leptoquark_mass: str, 
    couplings: str, 
    significance: str, 
    systematic_error: str,
    extra_width: str,
    luminosity: str,
    random_points: str = "0",
) -> Tuple[LeptoquarkParameters, int]:
    """
    Validate the data from both interactive and non-interactive modes and raise corresponding errors for the user to understand the issue
    After validating, convert the data to the appropriate type, & return a class that can be used throughout instead of passing multiple variables
    """

    # validate leptoquark mass
    try:
        leptoquark_mass = float(leptoquark_mass)
    except:
        raise ValueError("[Mass error]: Leptoquark mass should be a valid number")
    if leptoquark_mass < minimum_leptoquark_mass or leptoquark_mass > maximum_leptoquark_mass:
            raise ValueError(f"[Mass error]: Leptoquark mass should be from {minimum_leptoquark_mass} to {maximum_leptoquark_mass} GeV")


    # validate couplings
    couplings_list = couplings.strip().split()

    # Count frequency of each element
    frequency = {}
    for item in couplings_list:
        if item in frequency:
            raise ValueError(f"[Couplings error]: Coupling {item} is repeated. A coupling can only be inputted once")
        else:
            frequency[item] = 1
    if not len(couplings_list):
        raise ValueError("[Couplings error]: Couplings cannot be empty. For valid format, refer to README")
    unavailable_couplings = getUnavailableCouplings(couplings_list, leptoquark_model)
    if unavailable_couplings:
        raise ValueError(
            f"[Couplings error]: Coupling {unavailable_couplings[0]} is not "
            f"available for model {leptoquark_model}."
        )
    couplings = [_toDataCoupling(coupling) for coupling in couplings_list]

    # validate significance
    try:
        significance = int(significance)
    except:
        raise ValueError("[Significance error]: Significance should be a valid number: either 1 or 2")
    if significance != 1 and significance != 2:
        raise ValueError("[Significance error]: Significance should be a valid number: either 1 or 2")

    # validate Systematic error
    try:
        systematic_error = float(systematic_error)
        if systematic_error < 0 or systematic_error > 1:
            raise ValueError("[Systematic error]: [Systematic error should be a valid number from 0 to 1.")
    except:
        raise ValueError("[Systematic error]: [Systematic error should be a valid number from 0 to 1.")
    
    # validate extra width
    try:
        extra_width = float(extra_width)
    except:
        raise ValueError("[Extra width error]: Extra Width should be a valid number")

    # validate luminosity
    try:
        luminosity = float(luminosity)
    except:
        raise ValueError("Luminosity should be a valid number")
    
    # validate random points
    try:
        random_points = int(random_points)
        if random_points < 0:
            raise ValueError("Random points should be a non-negative integer")
    except:
        raise ValueError("Random points should be a valid number")
    
    # create Leptoquark data class
    leptoquark_parameters = LeptoquarkParameters(
        leptoquark_model=leptoquark_model,
        leptoquark_mass=leptoquark_mass,
        couplings=couplings,
        significance=significance,
        systematic_error=systematic_error,
        extra_width=extra_width,
        luminosity=luminosity,
    )

    # random points is returned seperately as it is not required during the calculations
    return leptoquark_parameters, random_points

    

def validateInteractiveInputCouplingValues(coupling_values_input_interactive: str, couplings_length: int) -> bool:
    """
    Check if queries are in correct form
    """
    coupling_values = coupling_values_input_interactive.split()
    if len(coupling_values) != couplings_length:
        prRed(f"[Query error]: Please input {couplings_length} couplings values input.")
        return False
    try:
        for i in range(couplings_length):
            _ = float(coupling_values[i])
    except ValueError:
        prRed(f"[Query error]: Please enter numerical values as input")
        return False
    return True

import os
import re
import warnings
import sympy as sym
from functools import lru_cache
from typing import Dict, Union, List
from sympy.utilities.iterables import flatten

from utilities.data_classes import SingleCouplingEfficiency, SingleCouplingEfficiencyTauTau, CrossTermsEfficiency, CrossTermsEfficiencyTauTau, TagsTauTau, SingleCouplingCrossSections, CrossTermsCrossSections
from utilities.data_classes import LeptoquarkParameters 
from utilities.constants import (
    chi_sq_limits_1,
    chi_sq_limits_2,
    get_cross_sections_df_cross_terms_tchannel,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)


@lru_cache(maxsize=None)
def _getCrossTermsHeaders(leptoquark_model: str) -> frozenset:
    return frozenset(
        get_cross_sections_df_cross_terms_tchannel(leptoquark_model).columns
    )


def resolveCrossTermsCoupling(coupling1: str, coupling2: str, leptoquark_model: str) -> str:
    cross_terms_headers = _getCrossTermsHeaders(leptoquark_model)
    coupling_orders = (
        f"{coupling1}_{coupling2}",
        f"{coupling2}_{coupling1}",
    )
    for coupling_order in coupling_orders:
        if coupling_order in cross_terms_headers:
            return coupling_order
    raise ValueError(
        f"No cross-term data found for {coupling1} and {coupling2} "
        f"in model {leptoquark_model}."
    )


def getR2CrossTermsEfficiencyCandidates(coupling1: str, coupling2: str) -> List[str]:
    coupling_pattern = re.compile(r"([XY][1-3]{2})(LR|RL)([1-3])x([1-3])")
    matches = [coupling_pattern.fullmatch(coupling) for coupling in (coupling1, coupling2)]
    if any(match is None for match in matches):
        return []

    first_match, second_match = matches
    if first_match.group(2) == second_match.group(2):
        return []

    def invert_flavours(match):
        prefix, chirality, first_flavour, second_flavour = match.groups()
        inverted_chirality = "RL" if chirality == "LR" else "LR"
        return f"{prefix}{inverted_chirality}{second_flavour}x{first_flavour}"

    first_inverted = invert_flavours(first_match)
    second_inverted = invert_flavours(second_match)
    matching_pairs = (
        (first_inverted, coupling2),
        (coupling1, second_inverted),
    )

    candidates = []
    for first, second in matching_pairs:
        candidates.extend((f"{second}_{first}", f"{first}_{second}"))
    return candidates


def shouldCalculateCrossTerms(
    coupling1: str, coupling2: str, leptoquark_model: str
) -> bool:
    if coupling1[2] == coupling2[2]:
        return True
    return leptoquark_model == "R2" and bool(
        getR2CrossTermsEfficiencyCandidates(coupling1, coupling2)
    )


def hasTauTagEfficiency(paths: List[str]) -> bool:
    return any(
        os.path.isfile(os.path.join(path, mass, tag_name))
        for path in paths
        if os.path.isdir(path)
        for mass in os.listdir(path)
        for tag_name in ("HHbT.csv", "HHbV.csv", "LHbT.csv", "LHbV.csv")
    )

def getNumbersFromCsvFiles(directory):
    """
    get masses list on the basis of the .csv files present in the directory
    """
    # List to store the numbers
    numbers = []
    
    # Iterate over all files in the given directory
    for filename in os.listdir(directory):
        # Check if the file ends with .csv
        if filename.endswith('.csv'):
            # Remove the .csv extension and convert to an integer
            number = int(filename[:-4])
            # Add the number to the list
            numbers.append(number)
    
    return numbers

def getImmediateSubdirectories(directory):
    """
    get masses list on the basis of the immediate subdirectories present in the directory
    """
    # List to store the names of subdirectories
    subdirectories = []
    
    # Iterate over all entries in the given directory
    for entry in os.listdir(directory):
        # Create the full path
        full_path = os.path.join(directory, entry)
        # Check if the entry is a directory
        if os.path.isdir(full_path):
            # Add the directory name to the list
            subdirectories.append(int(entry))
    
    return subdirectories

def transposeMatrix(matrix):
    # Use zip to transpose the rows to columns and convert them to lists
    columns = [list(column) for column in zip(*matrix)]
    return columns

def getCrossSectionFromProcess(process_path: str, coupling_to_process_cross_section_map: Dict[str, Union[SingleCouplingCrossSections, CrossTermsCrossSections]], coupling: str) -> float:
    singleCouplingCrossSection = coupling_to_process_cross_section_map[coupling]
    # Path: {DATA_PREFIX}/model/{model}/efficiency/i/{coupling}/
    if process_path.split('/')[4] == 'i':
        return singleCouplingCrossSection.cross_section_interference
    elif process_path.split('/')[4] == 't':
        return singleCouplingCrossSection.cross_section_tchannel
    return 0

def getEfficienciesFromProcess(process_path: str, coupling_to_process_efficiencies_map: Dict[str, Union[SingleCouplingEfficiency, SingleCouplingEfficiencyTauTau, CrossTermsEfficiency, CrossTermsEfficiencyTauTau]], coupling: str) -> List[float]:
    """
    return the correct efficiencies on the basis of process
    """
    efficienciesObject = coupling_to_process_efficiencies_map[coupling]
    # Path: {DATA_PREFIX}/model/{model}/efficiency/i/{coupling}/
    if process_path.split('/')[4] == 'i':
        return efficienciesObject.efficiency_interference
    elif process_path.split('/')[4] == 't':
        return efficienciesObject.efficiency_tchannel

    return []

def getEfficienciesFromProcessAndTagNameTauTau(process_path: str, tagName: str, coupling_to_process_efficiencies_map: Dict[str, Union[SingleCouplingEfficiency, SingleCouplingEfficiencyTauTau, CrossTermsEfficiency, CrossTermsEfficiencyTauTau]], coupling: str) -> List[float]:
    """
    return the correct efficiencies for tautau on the basis of process & tag
    """
    efficienciesObject = coupling_to_process_efficiencies_map[coupling]
    # Path: {DATA_PREFIX}/model/{model}/efficiency/i/{coupling}/
    # get TagsTauTau object
    tagsTauTau: TagsTauTau
    if process_path.split('/')[4] == 'i':
        tagsTauTau = efficienciesObject.efficiency_interference
    elif process_path.split('/')[4] == 't':
        tagsTauTau = efficienciesObject.efficiency_tchannel
    
    # from TagsTauTau object, we get the list of efficiencies
    if tagName == "HHbT.csv":
        return tagsTauTau.hhbt
    elif tagName == "HHbV.csv":
        return tagsTauTau.hhbv
    elif tagName == "LHbT.csv":
        return tagsTauTau.lhbt
    elif tagName == "LHbV.csv":
        return tagsTauTau.lhbv

    return []


def getDeltaChiSquare(leptoquark_parameters: LeptoquarkParameters, coupling_values_list: List[List[float]], chi_square_minima: float, numpy_chi_square_symbolic: sym.Symbol, numpy_chi_square_symbolic_zero_coupling: sym.Symbol, branching_fraction: sym.Symbol):
    """
    Use the lambdified function (numpy_chi_square_symbolic) to calculate chi-square for the given query input
    """
    validity_list = []
    delta_chi_square = []
    for coupling_values in coupling_values_list:
        try:
            # substitue values in branching fraction to check for zero division error
            # for single couplings the branching_fraction will be a float
            if len(coupling_values) > 1:
                flat_values = flatten(coupling_values)
                _ = branching_fraction.subs(dict(zip(flat_values[::2], flat_values[1::2])))
            chi_square_value = numpy_chi_square_symbolic(*flatten(coupling_values))
        except ZeroDivisionError:
            chi_square_value = numpy_chi_square_symbolic_zero_coupling(*flatten(coupling_values))
        delta_chi_square.append(chi_square_value - chi_square_minima)
        if leptoquark_parameters.significance == 1:
            if chi_square_value - chi_square_minima <= chi_sq_limits_1[len(leptoquark_parameters.sorted_couplings)-1]:
                validity_list.append("Yes")
            else:
                validity_list.append("No")
        elif leptoquark_parameters.significance == 2:
            if chi_square_value - chi_square_minima <= chi_sq_limits_2[len(leptoquark_parameters.sorted_couplings)-1]:
                validity_list.append("Yes")
            else:
                validity_list.append("No")
    
    return delta_chi_square, validity_list
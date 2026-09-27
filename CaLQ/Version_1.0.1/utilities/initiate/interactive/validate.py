from utilities.constants import minimum_leptoquark_mass, maximum_leptoquark_mass
from utilities.colour import prRed
from utilities.colour import prBlue
from utilities.validate import getUnavailableCouplings


def validateLeptoQuarkModel(leptoquark_model: str,) -> bool:
    prBlue("Leptoquark model updated!")
    prBlue("Please update the couplings if necessary.") 
    return True


def validateLeptoQuarkMass(
    leptoquark_mass: str, 
) -> bool:
    try:
        leptoquark_mass = float(leptoquark_mass)
        if leptoquark_mass < minimum_leptoquark_mass or leptoquark_mass > maximum_leptoquark_mass:
            prRed(f"[mass error]: Leptoquark mass should be between {minimum_leptoquark_mass} GeV and {maximum_leptoquark_mass} GeV")
            return False
    except:
        prRed("[mass error]: Leptoquark mass should be a valid number")
        return False
    return True

def validateLeptoQuarkCouplings(
    couplings: str, 
    leptoquark_model: str,
) -> bool:
    couplings_list = couplings.strip().split()

    # Count frequency of each element
    frequency = {}
    for item in couplings_list:
        if item in frequency:
            prRed(f"[ couplings error -- {item} ]: Multiple occurances of the input coupling was found! \nEach coupling can only be provided once.")
            return False
        else:
            frequency[item] = 1

    if not len(couplings_list):
        prRed("[couplings error]: Couplings cannot be empty!")
        return False
    
    unavailable_couplings = getUnavailableCouplings(couplings_list, leptoquark_model)
    if unavailable_couplings:
        prRed(
            f"[couplings error]: {unavailable_couplings[0]} is not available "
            f"for model {leptoquark_model}."
        )
        return False

    return True


def validateSignificance(
    significance: str, 
) -> bool:
    try:
        significance = int(significance)
        if significance != 1 and significance != 2:
            prRed("[significance error]: Significance should be a valid number, 1 or 2")
            return False
    except:
        prRed("[significance error]: Significance should be a valid number, 1 or 2")
        return False
    return True

def validateSystematicError(
    systematic_error: str,
) -> bool:
    try:
        systematic_error = float(systematic_error)
        if systematic_error < 0 or systematic_error > 1:
            prRed("[systematic_error error]: Systematic error should be a valid number between 0 and 1.")
            return False
    except:
        prRed("[systematic_error error]: Systematic error should be a valid number between 0 and 1.")
        return False
    return True

def validateExtraWidth(
    extra_width: str,
):
    # validate extra width
    try:
        extra_width = float(extra_width)
    except:
        prRed("[Extra width error]: Extra width should be a valid number in GeV")
        return False
    return True
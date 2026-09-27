from utilities.constants import (
    luminosity,
    default_significane,
    default_systematic_error,
    default_extra_width,
    InputMode,
)
from utilities.initiate.interactive.validate import (
    validateLeptoQuarkModel, 
    validateLeptoQuarkMass,
    validateLeptoQuarkCouplings,
    validateSignificance,
    validateSystematicError,
    validateExtraWidth
)
from utilities.parse import sortCouplingsAndValuesInteractive
from utilities.colour import prRed, prBlueNoNewLine, prBlue
from utilities.validate import validateInputData
from calculate import calculate

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory

# interactive mode commands
toolqit_cmds = ['import_model=', 'mass=', 'couplings=', 'extra_width=', 'significance=', 'systematic_error=', 'status', 'initiate', 'exit']
cmd_completer = WordCompleter(toolqit_cmds, ignore_case=True)

session_history = InMemoryHistory()


def initiateInteractive():
    """
    Initiate procedure for interactive mode
    """
    # initialize leptoquark model values
    leptoquark_model = "U1"
    leptoquark_mass = "1000"
    couplings = "X33LL3x3"
    significance = default_significane
    systematic_error = default_systematic_error
    extra_width = default_extra_width

    printDefaultValues(leptoquark_model, couplings, significance, systematic_error, extra_width) 

    # loop to input values. we will have to add validations here
    while True:
        # prBlueNoNewLine("calq > ")
        inpt = prompt("calq > ", completer=cmd_completer, 
                      history=session_history)
        s = inpt.split("=")
        if (":" in inpt):
            s = inpt.split(":")
        slen = len(s)
        if s[0].strip() == "import_model" and slen == 2:
            if validateLeptoQuarkModel(s[1].strip().upper()):
                leptoquark_model = s[1].strip().upper()
                printAvailableCouplings(leptoquark_model)
        elif s[0].strip() == "mass" and slen == 2:
            if validateLeptoQuarkMass(s[1].strip()):
                leptoquark_mass = s[1].strip()
        elif s[0].strip() == "couplings" and slen > 1:
            if validateLeptoQuarkCouplings(s[1].strip().upper(), leptoquark_model):
                couplings = s[1].strip().upper()
        elif s[0].strip() == "significance" and slen == 2:
            if validateSignificance(s[1].strip()):
                significance = int(s[1].strip())
        elif s[0].strip() == "systematic_error" and slen == 2:
            if validateSystematicError(s[1].strip()):
                systematic_error = s[1].strip()
        elif s[0].strip() == "extra_width" and slen == 2:
            if validateExtraWidth(s[1].strip()):
                extra_width = float(s[1].strip())
        elif s[0].strip() == "status":
            print(f" Leptoquark model= {leptoquark_model}")
            print(f" Leptoquark mass= {leptoquark_mass}")
            print(f" Couplings= {couplings}")
            print(f" Extra width= {extra_width}")
            print(f" Significance= {significance}")
            print(f" Systematic error= {systematic_error}")
        elif s[0].strip() == "help":
            printHelp()
        elif s[0].strip() == "initiate":
            if validateLeptoQuarkCouplings(couplings, leptoquark_model):
                leptoquark_parameters, _ = validateInputData(leptoquark_model, leptoquark_mass, couplings, significance, systematic_error, extra_width, luminosity)
                leptoquark_parameters.couplings_values = [" ".join(["0"] * len(couplings))]
                sortCouplingsAndValuesInteractive(leptoquark_parameters)
                calculate(leptoquark_parameters, InputMode.INTERACTIVE)
        elif s[0].strip().lower() in ["exit", "q", "quit", "exit()", ".exit", "e"]:
            return
        elif s[0].strip() == "":
            continue
        else:
            prRed(f" Command {s[0]} not recognised. Please retry or enter 'q', 'quit' or 'exit' to exit.")


def printDefaultValues(leptoquark_model: str, couplings: str, significance: int, systematic_error: str, extra_width: int):
    # also print initial message here
    prBlue("========================================================")
    prBlue("Commands available:")
    print(" import_model=, mass=, couplings=, extra_width=,\n  significance= (1 or 2), systematic_error=,\n status, initiate, help")     

    printAvailableCouplings(leptoquark_model)

    prBlue("Default values:")
    print(f" import_model= U1")
    print(f" mass= 1000")
    print(f" couplings= {couplings}")
    print(f" extra_width= {extra_width}")
    print(f" significance= {significance}")
    print(f" systematic_error= {systematic_error}")
    prBlue("========================================================")

def printAvailableCouplings(leptoquark_model: str):
    from utilities.constants import get_cross_sections_df_interference

    couplings = [
        coupling
        for coupling in get_cross_sections_df_interference(leptoquark_model).columns
        if coupling != "Mass" and "_" not in coupling
    ]
    prBlue(f"Coupling available for {leptoquark_model}:")
    print(", ".join(couplings))

def printHelp():
    """
    Content to be printed when help is inputted
    """
    prBlue("Commands with '=' expect a numerical value. Read README.md for more info on individual commands.")
    prBlue("Value input commands: ")
    print(" import_model= [Leptoquark model]")
    print(" mass= [Leptoquark mass] (should be between 1000 and 5000)")
    print(" couplings= [Couplings. For the format, refer to README.md]")
    print(" significance= [Significance of the limit in standard deviations. Possible values=1,2]")
    print(" systematic_error= [Systematic error to be included in the calculations. Should be between 0 and 1]")
    print(" extra_width= [extra width to account for additional unaccounted decays]")
    prBlue("Other commands:")
    print(" status [To print current values]")
    print(" initiate [To start the calcualation]")
    print(" exit [To exit the calculator]")
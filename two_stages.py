from sys import platform
import clr
from time import time
from jmetal.algorithm.singleobjective import GeneticAlgorithm
from jmetal.operator import SBXCrossover, PolynomialMutation
from jmetal.operator import BestSolutionSelection
from jmetal.util.termination_criterion import StoppingByEvaluations
from jmetal.core.problem import OnTheFlyFloatProblem
from jmetal.util.solution import (
    get_non_dominated_solutions,
    print_function_values_to_screen,
    print_variables_to_screen,
)


if platform == "win32":
    import pythoncom

    pythoncom.CoInitialize()
    PATH = "c:\\Users\\Volkan\\AppData\\Local\\DWSIM8\\"
elif platform == "linux":
    PATH = "/usr/local/lib/dwsim/"


clr.AddReference(PATH + "DWSIM.Automation.dll")
clr.AddReference(PATH + "DWSIM.Interfaces.dll")
clr.AddReference(PATH + "DWSIM.UnitOperations.dll")

from DWSIM.Automation import Automation2
from DWSIM.Interfaces.Enums import PropertyType

fs = Automation2()
sim = fs.LoadFlowsheet("two_stages.dwxmz")
wc1 = sim.GetFlowsheetSimulationObject("WC1")
wc2 = sim.GetFlowsheetSimulationObject("WC2")
comp1 = sim.GetFlowsheetSimulationObject("COMP1")


def f(p):
    # p = 100e3 + random() * (2e6 - 100e3)
    comp1.SetPropertyValue("PROP_CO_4", p[0])
    fs.CalculateFlowsheet2(sim)
    w1 = wc1.GetPropertyValue("PROP_ES_0")
    w2 = wc2.GetPropertyValue("PROP_ES_0")
    return w1 + w2


problem: OnTheFlyFloatProblem = (
    OnTheFlyFloatProblem()
    .set_name("Optimum intercooler pressure")
    .add_function(f)
    .add_variable(100e3, 2000e3)
)

algorithm = GeneticAlgorithm(
    problem=problem,
    population_size=10,
    offspring_population_size=10,
    mutation=PolynomialMutation(probability=1.0, distribution_index=20),
    crossover=SBXCrossover(probability=1.0, distribution_index=20),
    termination_criterion=StoppingByEvaluations(max_evaluations=1000),
    # termination_criterion=StoppingByKeyboard(),
    selection=BestSolutionSelection(),
)
start = time()
algorithm.run()
stop = time()
print(stop - start)

res = get_non_dominated_solutions(algorithm.solutions)
print_function_values_to_screen(res)
print_variables_to_screen(res)

from random import random
from sys import platform
import clr
from jmetal.algorithm.singleobjective import GeneticAlgorithm
from jmetal.operator import SBXCrossover, PolynomialMutation, RandomSolutionSelection
from jmetal.util.termination_criterion import StoppingByKeyboard
from jmetal.util.observer import PrintObjectivesObserver
from jmetal.core.quality_indicator import GenerationalDistance
from jmetal.core.problem import FloatProblem, FloatSolution, OnTheFlyFloatProblem
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
sim = fs.LoadFlowsheet("three_stages.dwxmz")
wc1 = sim.GetFlowsheetSimulationObject("WC1")
wc2 = sim.GetFlowsheetSimulationObject("WC2")
wc3 = sim.GetFlowsheetSimulationObject("WC3")
comp1 = sim.GetFlowsheetSimulationObject("COMP1")
comp2 = sim.GetFlowsheetSimulationObject("COMP2")
comp3 = sim.GetFlowsheetSimulationObject("COMP3")


def f(p):
    comp1.SetPropertyValue("PROP_CO_4", p[0])
    comp2.SetPropertyValue("PROP_CO_4", p[1])
    fs.CalculateFlowsheet2(sim)
    w1 = wc1.GetPropertyValue("PROP_ES_0")
    w2 = wc2.GetPropertyValue("PROP_ES_0")
    w3 = wc3.GetPropertyValue("PROP_ES_0")
    return w1 + w2 + w3


def c1(p):
    return p[0] - p[1]


def c2(p):
    return p[1] - 2000e3


class Problem(FloatProblem):
    def __init__(self):
        super(Problem, self).__init__()
        self.fs = Automation2()
        self.sim = self.fs.LoadFlowsheet("three_stages.dwxmz")
        self.number_of_constraints = 2
        self.number_of_variables = 2
        self.number_of_objectives = 1
        self.obj_directions = [self.MAXIMIZE, self.MINIMIZE]

    def get_name(self) -> str:
        return "Three stage compression"

    def evaluate(self, solution: FloatSolution) -> FloatSolution:
        p0 = solution.variables[0]
        p1 = solution.variables[1]
        comp1 = self.sim.GetFlowsheetSimulationObject("COMP1")
        comp2 = self.sim.GetFlowsheetSimulationObject("COMP2")
        comp1.SetPropertyValue("PROP_CO_4", p0)
        comp2.SetPropertyValue("PROP_CO_4", p1)
        self.fs.CalculateFlowsheet2(self.sim)
        wc1 = self.sim.GetFlowsheetSimulationObject("WC1")
        wc2 = self.sim.GetFlowsheetSimulationObject("WC2")
        wc3 = self.sim.GetFlowsheetSimulationObject("WC3")
        w1 = wc1.GetPropertyValue("PROP_ES_0")
        w2 = wc2.GetPropertyValue("PROP_ES_0")
        w3 = wc3.GetPropertyValue("PROP_ES_0")
        solution.constraints[0] = p0 - p1
        solution.constraints[1] = p1 - 2000e3
        solution.objectives[0] = w1 + w2 + w3

    def create_solution(self) -> FloatSolution:
        new_solution = FloatSolution(
            number_of_constraints=2,
            number_of_objectives=1,
            lower_bound=[100e3, 2000e3],
            upper_bound=[100e3, 2000e3],
        )
        p0 = random() * (2000e3 - 100e3) + 100e3
        p1 = random() * (2000e3 - p0) + p0
        new_solution.variables = [p0, p1]
        return new_solution


problem: OnTheFlyFloatProblem = (
    OnTheFlyFloatProblem()
    .set_name("Optimum intercooler pressure")
    .add_function(f)
    .add_variable(100e3, 2000e3)
    .add_variable(100e3, 2000e3)
)

# algorithm = SimulatedAnnealing(
#     problem=Problem(),
#     mutation=UniformMutation(probability=1.0),
#     termination_criterion=StoppingByEvaluations(max_evaluations=100),
#     solution_generator=RandomGenerator(),
# )


# problem = Problem()
algorithm = GeneticAlgorithm(
    problem=problem,
    population_size=10,
    offspring_population_size=10,
    mutation=PolynomialMutation(
        probability=1.0 / problem.number_of_variables, distribution_index=20
    ),
    crossover=SBXCrossover(probability=1.0, distribution_index=20),
    selection=RandomSolutionSelection(),
    # termination_criterion=StoppingByEvaluations(max_evaluations=10000),
    termination_criterion=StoppingByKeyboard(),
)

# algorithm = LocalSearch(
#     problem=problem,
#     termination_criterion=StoppingByEvaluations(max_evaluations=100),
#     comparator=Generic(),
#     mutation=SimpleRandomMutation(probability=1.0),
# )

# algorithm = E(
#     problem=problem,
#     population_size=25,
#     offspring_population_size=25,
#     mutation=PolynomialMutation(
#         probability=1 / problem.number_of_variables, distribution_index=10
#     ),
#     crossover=SBXCrossover(probability=1.0, distribution_index=10),
#     termination_criterion=StoppingByEvaluations(max_evaulations=1000),
# )

# algorithm = GeneticAlgorithm(
#     problem=problem,
#     population_size=10,
#     offspring_population_size=10,
#     mutation=PolynomialMutation(probability=1.0, distribution_index=20),
#     crossover=SBXCrossover(probability=1.0, distribution_index=20),
#     termination_criterion=StoppingByEvaluations(max_evaluations=100),
#     # termination_criterion=StoppingByKeyboard(),
#     selection=BestSolutionSelection(),
# )

print_to_screen = PrintObjectivesObserver()
algorithm.observable.register(print_to_screen)
algorithm.run()
print(f"Elapsed time: {algorithm.total_computing_time}")

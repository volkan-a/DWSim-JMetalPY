from random import random
from sys import platform
import clr
import numpy as np
import matplotlib.pyplot as plt
from jmetal.algorithm.singleobjective import GeneticAlgorithm
from jmetal.operator import SBXCrossover, PolynomialMutation, RandomSolutionSelection
from jmetal.util.termination_criterion import StoppingByKeyboard, StoppingByEvaluations
from jmetal.util.observer import PrintObjectivesObserver

from jmetal.core.quality_indicator import GenerationalDistance
from jmetal.core.problem import FloatProblem, FloatSolution, OnTheFlyFloatProblem
from jmetal.util.solution import (
    get_non_dominated_solutions,
    print_function_values_to_screen,
    print_variables_to_screen,
)
import random

if platform == "win32":
    import pythoncom

    pythoncom.CoInitialize()
    PATH = "c:\\Users\\volkan.akkaya\\AppData\\Local\\DWSIM8\\"
elif platform == "linux":
    PATH = "/usr/local/lib/dwsim/"


clr.AddReference(PATH + "DWSIM.Automation.dll")
clr.AddReference(PATH + "DWSIM.Interfaces.dll")
clr.AddReference(PATH + "DWSIM.UnitOperations.dll")

from DWSIM.Automation import Automation2
from DWSIM.Interfaces.Enums import PropertyType

fs = Automation2()
sim = fs.LoadFlowsheet("orc6.dwxmz")

def print_properties(uo_name:str):
    global sim
    a = sim.GetFlowsheetSimulationObject(uo_name)
    for p in a.GetProperties(PropertyType.ALL):
        print(f"{p}: {a.GetPropertyValue(p)}")

class Problem(FloatProblem):
    def __init__(self):
        super(Problem, self).__init__()
    
        self.number_of_objectives = 1
        self.number_of_constraints = 4
        self.number_of_variables = 4
        self.lower_bound = [2500e3, 1000e3, 300e3, 0.5]
        self.upper_bound = [3500e3, 2000e3, 400e3, 1.0]
        
    def evaluate(self, solution: FloatSolution)->FloatSolution:
        # decision variables
        p_feed_pump = solution.variables[0]
        p_hp_turbine = solution.variables[1]
        p_lp_turbine = solution.variables[2]
        sr1_splitter = solution.variables[3]
        
        # unit operations of decision variables
        feed_pump = sim.GetFlowsheetSimulationObject("FEED PUMP")
        hp_turbine = sim.GetFlowsheetSimulationObject("HP TURBINE")
        lp_turbine = sim.GetFlowsheetSimulationObject("LP TURBINE")
        splitter = sim.GetFlowsheetSimulationObject("SPLITTER")
        
        #unit operations of constraints
        orc10 = sim.GetFlowsheetSimulationObject("ORC10")
        f = sim.GetFlowsheetSimulationObject("f")
        g = sim.GetFlowsheetSimulationObject("g")
        orc11 = sim.GetFlowsheetSimulationObject("ORC11")
        
        # unit operations of objective function
        wthp = sim.GetFlowsheetSimulationObject("Wthp")
        wtlp = sim.GetFlowsheetSimulationObject("Wtlp")
        wp = sim.GetFlowsheetSimulationObject("Wp")
        
        feed_pump.SetPropertyValue("PROP_PU_5", p_feed_pump)
        hp_turbine.SetPropertyValue("PROP_TU_4", p_hp_turbine)
        lp_turbine.SetPropertyValue("PROP_TU_5", p_lp_turbine)
        splitter.SetPropertyValue("SR1", sr1_splitter)
        
        fs.CalculateFlowsheet2(sim)
        
        wlp = wtlp.GetPropertyValue("PROP_ES_0")
        whp = wthp.GetPropertyValue("PROP_ES_0")
        wp = wp.GetPropertyValue("PROP_ES_0")
        
        xorc10 = orc10.GetPropertyValue("PROP_MS_27")
        xf = f.GetPropertyValue("PROP_MS_27")
        xg = g.GetPropertyValue("PROP_MS_27")
        torc11 = orc11.GetPropertyValue("PROP_MS_1")
        
        solution.objectives= [-wlp-whp+wp]
        
        solution.constraints = [
            -xorc10+0.85,
            -xf+0.85,
            -xg+0.85,
            -torc11+310,
           # p_hp_turbine-p_feed_pump,
           # p_lp_turbine-p_hp_turbine            
        ]
        
        return solution
    
    def create_solution(self)->FloatSolution:
        new_solution = FloatSolution(
            number_of_objectives=self.number_of_objectives,
            number_of_constraints=self.number_of_constraints,
            lower_bound=self.lower_bound,
            upper_bound=self.upper_bound)
        
        new_solution.variables = [
            2500e3+(3500e3-2500e3)*random.random(),
            1000e3+(2000e3-1000e3)*random.random(),
            300e3+(400e3-300e3)*random.random(),
            0.5 + (1.0-0.5)*random.random()
        ]
        
        return new_solution
    
    def get_name(self)->str:
        return "ORC optimization"

problem = Problem()
algorithm = GeneticAlgorithm(
    problem=problem,
    population_size=50,
    offspring_population_size=50,
    mutation=PolynomialMutation(
        probability=1.0 / problem.number_of_variables, distribution_index=20
    ),
    crossover=SBXCrossover(probability=1.0, distribution_index=20),
    selection=RandomSolutionSelection(),
    # termination_criterion=StoppingByEvaluations(max_evaluations=10000),
    termination_criterion=StoppingByKeyboard(),
)
basic = PrintObjectivesObserver()
algorithm.observable.register(basic)

algorithm.run()


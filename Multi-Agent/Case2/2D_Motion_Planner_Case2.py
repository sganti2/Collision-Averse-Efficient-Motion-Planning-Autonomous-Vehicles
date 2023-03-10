# This file is not part of OMG-tools.
# Author: Sruti Ganti
# Date: March 8, 2023
import numpy as np

from omgtools import *

# create fleet
N = 2
vehicles = [Bicycle(length=0.4, options={'plot_type': 'car', 'substitution': False}) for l in range(N)]
for vehicle in vehicles:
    vehicle.define_knots(knot_intervals=5)

fleet = Fleet(vehicles)
configuration = [[1.], [-1.]]
init_positions = [[-1.5, 0.5], [0.8, 0.5]]
terminal_positions = [[2., 2.], [2., 2.]]

init_pose = np.c_[init_positions, np.zeros(N), np.zeros(N)]
term_pose = np.c_[terminal_positions, np.zeros(N)]

fleet.set_configuration(configuration)
fleet.set_initial_conditions(init_pose.tolist())
fleet.set_terminal_conditions(term_pose.tolist())

# create environment
environment = Environment(room={'shape': Square(5.), 'position': [0., 2.]})
environment.add_obstacle(Obstacle({'position': [0., 1.75]}, shape=Circle(0.5)))

# create a formation point-to-point problem
options = {'horizon_time': 5., 'codegen': {'jit': False}, 'rho': 3.}
problem = RendezVous(fleet, environment, options=options)
problem.init()

# create simulator
simulator = Simulator(problem)
problem.plot('scene')
fleet.plot('input', knots=True)

# run it!
simulator.run()
problem.save_movie('scene', format='gif', name='problemgif', number_of_frames=80, movie_time=4, axis=False)
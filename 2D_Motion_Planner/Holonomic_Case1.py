# This file is not part of OMG-tools.

from omgtools import *

# create vehicle
vehicle = Holonomic()
vehicle.define_knots(knot_intervals=5)  # choose lower amount of knot intervals

vehicle.set_initial_conditions([0., 0.])
vehicle.set_terminal_conditions([3., 3.])

# create environment
environment = Environment(room={'shape': Square(5.), 'position': [1.5, 1.5]})
environment.add_obstacle(Obstacle({'position': [1., 1.]}, shape=Circle(0.5)))

# create a point-to-point problem
problem = Point2point(vehicle, environment, freeT=True)
# extra solver settings which may improve performance
#problem.set_options({'solver_options': {'ipopt': {'ipopt.linear_solver': 'ma57'}}})
problem.init()

vehicle.problem = problem  # to plot error if using substitution

# create simulator
simulator = Simulator(problem)
problem.plot('scene')
vehicle.plot('input', knots=True, prediction=True, labels=['v_x (m/s)', 'v_y (m/s)'])

# run it!
simulator.run()
problem.save_movie('scene', format='gif', name='problemgif', number_of_frames=80, movie_time=4, axis=False)
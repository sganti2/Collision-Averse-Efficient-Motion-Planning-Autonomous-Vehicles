from omgtools import *

# create fleet
N = 2
vehicles = [Quadrotor(0.2) for l in range(N)]
fleet = Fleet(vehicles)

configuration = [[0.], [-0.]]
init_positions = [[0., 0.], [0.8, 0.5]]
terminal_positions = [[3., 3.], [3., 3.]]

fleet.set_configuration(configuration)
fleet.set_initial_conditions(init_positions)
fleet.set_terminal_conditions(terminal_positions)

# create environment
environment = Environment(room={'shape': Square(5.), 'position': [0., 2.]})
environment.add_obstacle(Obstacle({'position': [0., 1.5]}, shape=Circle(0.4)))

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
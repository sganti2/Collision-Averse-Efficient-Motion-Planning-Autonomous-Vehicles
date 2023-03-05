# This file is part of OMG-tools.
#
# OMG-tools -- Optimal Motion Generation-tools
# Copyright (C) 2016 Ruben Van Parys & Tim Mercy, KU Leuven.
# All rights reserved.
#
# OMG-tools is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from omgtools import *

# create fleet
N = 2
vehicles = [Bicycle(length=0.4, options={'plot_type': 'car', 'substitution': False}) for i in range(N)]

fleet = Fleet(vehicles)
configuration = RegularPolyhedron(0.2, N, np.pi/4.).vertices.T
init_positions = [0., 0.] + configuration
terminal_positions = [3., 3.] + configuration
init_pose = np.c_[init_positions, (0.)*np.ones(N), (0.)*np.ones(N)]
terminal_pose = np.c_[terminal_positions, (0.)*np.ones(N)]

fleet.set_configuration(configuration.tolist())
fleet.set_initial_conditions(init_pose.tolist())
fleet.set_terminal_conditions(terminal_pose.tolist())

# create environment
environment = Environment(room={'shape': Square(5.), 'position': [1.5, 1.5]})
trajectories = {'velocity': {'time': [0.5],
                             'values': [[0., 0.]]}}
environment.add_obstacle(Obstacle({'position': [1., 1.]}, shape=Circle(0.5),
                                  simulation={'trajectories': trajectories}))

# create a formation point-to-point problem
problem = FormationPoint2point(fleet, environment, options=None)
problem.init()

# create simulator
simulator = Simulator(problem)
fleet.plot('input', knots=True, predict=True, labels=['v_x (m/s)', 'v_y (m/s)'])
problem.plot('scene')

# run it!
simulator.run()

# save result
problem.save_movie('scene', format='gif', name='problemgif', number_of_frames=80, movie_time=4, axis=False)
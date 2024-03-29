# Collision-Averse and Efficient B-Spline Derived Motion Planning for Autonomous Vehicles (AVs)

In order to acquire a comprehensive understanding of the work present within this repository, please refer to the accompanying honors thesis within this repository.
 
## I. Research Objective
The primary objective of this research was to utilize the model-based approach to design a motion planner that optimizes collision aversion and efficiency for 2D vehicle dynamics. This research leverages the pre-existing motion planning toolkit, OMG-Tools, in order to generate smooth trajectories [1]. The simulation results included within this repository are specific to two interaction cases: Case 1 and Case 2. The setup for Case 1 and Case 2 are discussed thoroughly within the following section. 

## II. Simulation Setup
### A. Case 1
The setup for Case 1 is representative of a single-agent roundabout scenario. This environment consists of one agent (primary vehicle) and one obstacle (static roundabout). The aim of Case 1 is to solve the NLP for a very simplified environment in order to generate the most optimal trajectory. 

### B. Case 2
The setup for Case 2 is representative of a multi-agent roundabout scenario. This environment consists of two agents (primary vehicle and secondary vehicle), and one obstacle (static roundabout). The aim of Case 2 is to slightly increase the complexity of the Case 1 NLP in order to account for multiple vehicles when producing the optimal trajectory. 

## III. 2D_Motion_Planner Results
The '2D_Motion_Planner' directory consists of results for single-agent and multi-agent interactions within the roundabout scenario. These results are categorized by the following vehicle models: quadrotor model and bicycle model. In order to visualize the single-agent and multi-agent results, download OMG-tools here: https://github.com/meco-group/omg-tools. Once OMG-tools has been downloaded, copy the specific motion planning Python file from this repository into the OMG-tools repository. Be sure to copy the file into the 'examples' directory. Execute the copied file as you would an example within the OMG-tools repository. 

## IV. Frenet_Baseline Results
Frenet frames were utilized as a baseline for validating the computational efficiency of the extended motion planner. However, the Frenet frame approach does not incorporate minimization, or take the vehicle dynamics into account when generating the desired trajectory. In order to visualize the Frenet frame results, ensure that the 'cubic_spline_planner.py', 'quintic_polynomials_planner.py', and 'frenet_optimal_trajectory.py' files are included within the same package. Execute the 'frenet_optimal_trajectory.py' using the following terminal command: `python frenet_optimal_trajectory.py`

## Appendix
### Definitions
* NLP: Non-linear Programming Problem
* OCP: Optimal Control Problem 

### References 
[1] R. Van Parys and T. Mercy. (2016). OMG-Tools. [Online]. Available:
https://github.com/meco-group/omg-tools

# Social Navigation for Autonomous Vehicles
In order to acquire a comprehensive understanding of the work present within this repository, please refer to the accompanying honors thesis defense paper: https://keep.lib.asu.edu/collections/130827.

## I. Research Objective
The primary objective of this research was to utilize the model-based approach to design a motion planner that optimizes collision aversion and efficiency for 2D vehicle dynamics. This research leverages 

## III. Simulation Setup
### A. Case 1
The setup for Case 1 is representative of a single-agent roundabout scenario. This environment consists of one agent (primary vehicle) and one obstacle (static roundabout). The aim of Case 1 is to solve the NLP for a very simplified environment in order to generate the most optimal trajectory. 

### B. Case 2
The setup for Case 2 is representative of a multi-agent roundabout scenario. This environment consists of two agents (primary vehicle and secondary vehicle), and one obstacle (static roundabout). The aim of Case 2 is to slightly increase the complexity of the Case 1 NLP in order to account for multiple vehicles and produce the optimal trajectory. 

## II. 2D_Motion_Planner Results
The '2D_Motion_Planner' directory consists of results for single-agent and multi-agent interactions within the roundabout scenario. These results are categorized by the following vehicle models: quadrotor model and bicycle model. In order to visualize the single-agent and multi-agent results, download OMG-tools here: https://github.com/meco-group/omg-tools. Once OMG-tools has been downloaded, copy the specific motion planning Python file from this repository into the OMG-tools repository. Be sure to copy the file into the 'examples' directory. Execute the copied file as you would an example within the OMG-tools repository. 

## Frenet Baseline Results


## IV. Software Architecture 


## Appendix
### 1. Definitions
NLP: Non-linear Programming Problem

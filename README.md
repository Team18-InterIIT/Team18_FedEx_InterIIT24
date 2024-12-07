<h1 align="center">
<img src="media/int13.png" width="300">
<img src="media/fedex.png" width="300">

</h1>  
This is Team18's submission for the Fedex Midprep Problem Statement.

# Introduction
This encloses the code for a complete Packing Solution. After running this code on a dataset of packages, the optimal location of each package in their respective ULD's. The output is present in the required specifications. The base algorithm aims to minimsie the cost of delay while minimising the number of ULD's in which priority packages are packed.

Also additonal conditions have been implemented:  
* Express Priority Arrival   
* Families of packages   
* Stability   
* Gravitational Effects   
* This-Side-Up / Packages with Orientation Constraints 

Note: For 'Families of packages' and 'This-Side-Up' features an extra column must be added in the original dataset.

# Usage

## Prerequisites

It is highly recommended to use a virtual environment to run the code. 
It is also highly recommended to run in Linux or MacOS. Windows users may face some issues with the Stress Analysis feature.

- [A working installation of Python (3.12 or higher), with Python added to PATH.](https://www.python.org/downloads/)
- A working installation of `pip`.
- [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). (only for Windows users, and if using Stress Analysis)

## Installation

Run the following command in the project directory in your terminal:
```bash
python run.py
```

This will install the required packages for the code to run, and open a dashboard for the user to interact with the code.

## Navigating the Dashboard

### What should I do 

1. Drag and Drop/Select the test file data into the Browse Files Button. <br>
You should see a tabular form of your Packages and details about their number and number of ULD's
2. Adapt Parameters for the current requirements
3. Click the 'Run Packing Algorithm' button
<br>

### Input Options

A. Rotatinal Constraint --> An additional column of boolean values must be present in the input data <br>
B.Family of Packages --> An additional column of Family IDs must be present in the in the original dataset. They can have any name, but the name must be consistent for a given family.<br>

### Search Methods and Related Parameters

##### Normal Search
This is a quick search optimising for time to find Solution
##### Hyper Search
This is a deep search algorithm that optimises for "Cost" as defined by the Problem Statement
##### Layering (*Available only in Normal Search*)
Creates space and cost efficient layers according to the 2DBP logic sytems
##### Multi-Processing
Takes advantage of multiple cores of modern CPU's for a exponential decrase in runtime
##### Beam Width (*Available only in Hyper Search*)
Higher Beam Width = Better Solution
It is a parameter used to control how wide our search is in the solution space
##### Number of iterations
Higher Number of iterations = Better Solution
It is a parameter used to control how many internal cycles the programs utilises
##### Number of cores
Higher Number of Cores = Faster Runtime
It is a parameter used to control how many of your multicore CPU is used during running the solution





Our code provides:

- a powerful Parser + Solver system
- sophisticated application functions 
- tools for integrating various input types
- useful additional packing constraint capabilities



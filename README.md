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


## Running the code

There are two primary ways to run the code:

1. **Using the Dashboard** (Recommended):  
   After running the `run.py` file, a dashboard will open in your default browser. You can upload a dataset, and run the code using the dashboard.
    ```bash
    python run.py
    ```

2. **Using the Command Line**:
    You can also run the code using the command line. The following command will run the code on the dataset `Challenge_FedEx.txt`:
     ```bash
     python src/main.py test/Challenge_FedEx.txt
     ```

     NOTE: The path to the dataset should be relative to the project directory.
    
    Flags:
    - `--plot`: To plot the 3D view of the ULDs.
    - `--stress-analysis`: To run the stress analysis feature. (Might not work on Windows: see Prerequisites)
    - `--animate`: To animate the packing process.
    
    Example:
    ```bash
    python src/main.py test/Challenge_FedEx.txt --plot
    ```


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
Takes advantage of multiple cores of modern CPU's for a exponential decrease in runtime
##### Beam Width (*Available only in Hyper Search*)
Higher Beam Width = Better Solution
It is a parameter used to control how wide our search is in the solution space
##### Number of iterations
Higher Number of iterations = Better Solution
It is a parameter used to control how many internal cycles the programs utilises
##### Number of cores
Higher Number of Cores = Faster Runtime
It is a parameter used to control how many of your multicore CPU is used during running the solution

# Code Structure

## Directories

```
.
├── README.md
├── requirements.txt
├── run.py
├── src
│   ├── algorithm_interface.py
│   ├── dashboard.py
│   ├── entity.py
│   ├── environment.py
│   ├── family_cost.py
│   ├── geometry_helpers.py
│   ├── insert_package.py
│   ├── layering.py
│   ├── main.py
│   ├── parser.py
│   ├── solvers
│   │   ├── hybrid.py
│   │   ├── layerpack.py
│   │   └── NAC.py
│   └── util.py
├── test
│   ├── Challenge_FedEx_Raw.txt
│   ├── Challenge_FedEx.txt
│   ├── layer.txt
```

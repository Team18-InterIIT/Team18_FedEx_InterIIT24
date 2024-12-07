<h1 align="center">
<img src="media/int13.png" width="300">
<img src="media/fedex.png" width="300">

</h1>  
This is Team18's submission for the Fedex Midprep Problem Statement.

# Introduction
This encloses the code for a complete Packing Solution. After running this code on a dataset of packages, the optimal location of each package in their respective ULD's. The output is present in the required specifications. The base algorithm aims to minimsie the cost of delay while minimising the number of ULD's in which priority packages are packed.

# Usage

## Prerequisites

It is highly recommended to use a python virtual environment to run the code.
If not, make sure that your pip installation is able to install python packages on your machine.
It is also highly recommended to run in Linux or MacOS. Windows users may face some issues with the Stress Analysis feature.

- [A working installation of Python (3.12 or higher), with Python added to PATH.](https://www.python.org/downloads/)
- A working installation of `pip`.
- [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). (only for Windows users, and if using Stress Analysis)

## Installation

Run the following command in the project directory in your terminal:
```bash
python run.py
```

This will install the required packages for the code to run, and open a dashboard for the user to interact with the code. <br>

If Streamlit asks for an email, you can safely ignore and click the "Enter" Key. Subsequent runs will skip this step.
<br>

In some case, in Ubuntu, 3 links may appear. Try all three of these.

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

### What should I do?

1. Drag and Drop/Select the test file data into the Browse Files Button. <br>
You should see a tabular form of your Packages and details about their number and number of ULD's
2. Adapt Parameters for the current requirements
3. Click the 'Run Packing Algorithm' button
<br>

### Input Options

A. Rotatinal Constraint --> An additional column of boolean values must be present in the input data.  
    If 'True', then the package can be rotatated along all 3 axes.
    If 'False', the the package can only be roatated along z-axis.

B. Family of Packages --> An additional column of Family IDs must be present in the in the original dataset. These Family IDs must be integers. If Family Cost is enabled, then the algorithm tries to put family packages closer to each other.

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
├── AlgorithmicExplanation.mp4
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
└── test
    ├── Challenge_FedEx_Raw.txt
    ├── Challenge_FedEx.txt
    └── layer.txt
```
## More Useful Features
The following additonal conditions have been implemented:  
* Express Priority Arrival   
* Families of packages   
* Stability 
* This-Side-Up / Packages with Orientation Constraints 
* IATA ULD Regulations
* Helper Tool
* Stress Analysis

Note: For 'Families of packages' and 'This-Side-Up' features an extra column must be added in the original dataset.
### Express Priority Package

Assuming that the packing algorithm is completed and the packages have started being packed (physically). This is a useful additon which helps us accomadate a new priority package of specified dimensions with minimal disruption!

<br>
Method 1 --> Insert Package
Here we find an empty space which can fit the required package (Useful for small express packages) 
<br>
Method 2 --> Replace Package
Here we remove an economy package to make space for the new express package. This is done with minimal disturbance to the current package.

### Stability 
This feature makes sure that none of the packages are off balance.

### IATA ULD Regulations
Here we make sure the solutions adhere to this international standard for packing ULD's.

### Helper Tool
Using a combination of graph theory and topological sorting we create the package order. We show the most effiecient packing order such that real-world constraints are included

### Stress Analysis
Using a state-of-the-art physics engine we will calculate stress on each package. In future modifications of this code we can increase customer satisfaction with regard to fragile packages etc. 
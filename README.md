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


Our code provides:

- a powerful Parser + Solver system
- sophisticated application functions 
- tools for integrating various input types
- useful additional packing constraint capabilities

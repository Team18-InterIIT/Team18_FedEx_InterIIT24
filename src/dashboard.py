import sys
import streamlit as st
import time
import altair as alt
# Import your required classes and functions from your existing code
import parser
from environment import Environment
from util import Util
from insert_package import PackageInserter
from entity import Package
from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting as PackingAlgorithm


# Dynamically import the algorithm based on user selection
ALGORITHMS = {
    "ThreeDBP_Pivoting_Simul_Annealing": "solvers.threeDBP_Pivoting",
    "COA (Caving COA)": "solvers.Caving_COA",
    "LayerPacking (Layer Strat with OR)": "solvers.layerstratwithOR",
}

# Streamlit Setup
st.set_page_config(page_title="3D Bin Packing", layout="wide")
st.title("3D Bin Packing Dashboard")

# Default File (Always Used)
test_file = "test/Challenge_FedEx.txt"

# Algorithm Selection Section on the Left Sidebar
st.sidebar.header("Select Packing Algorithm")
algorithm_choice = st.sidebar.selectbox("Choose Algorithm", list(ALGORITHMS.keys()))

# Dynamically import the selected algorithm
if algorithm_choice == "ThreeDBP_Pivoting_Simul_Annealing":
    from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting_Simul_Annealing as PackingAlgorithm
elif algorithm_choice == "COA (Caving COA)":
    from solvers.Caving_COA import COA as PackingAlgorithm
elif algorithm_choice == "LayerPacking (Layer Strat with OR)":
    from solvers.layerstratwithOR import LayerPacking as PackingAlgorithm

# Parse the dataset using the parser
@st.cache_data
def load_data(file):
    # Use the parser directly to extract ULDs and packages from the file
    parser_instance = parser.Parser(file)
    K = parser_instance.get_K()
    uld_list = parser_instance.get_uld_list()
    pkg_list = parser_instance.get_pkg_list()
    return K, uld_list, pkg_list

# Load data (without CSV reading)
K, uld_list, pkg_list = load_data(test_file)

# Show dataset summary
st.subheader("Dataset Summary")
st.write(f"Number of Packages: {len(pkg_list)}")
st.write(f"Number of ULDs: {len(uld_list)}")

# Visualizing some of the package information (optional)
st.write("Package List:")
st.dataframe(pkg_list[:10])  # Display first 10 packages as a sample

# Algorithm Parameters Section
st.sidebar.header("Algorithm Parameters")
tlim = st.sidebar.slider("Time limit (seconds)", 1, 100, 10)
max_iters = st.sidebar.slider("Maximum iterations", 1, 5, 1)

# Run the Packing Algorithm
if st.button("Run Packing Algorithm"):
    # Initialize Environment and Model
    parser = parser.Parser(test_file)
    K = parser.get_K()
    uld_list = parser.get_uld_list()
    pkg_list = parser.get_pkg_list()

    # Create the environment
    env = Environment(K, uld_list, pkg_list)

    # Select and run the packing algorithm
    model = PackingAlgorithm()
    start_time = time.time()
    model.solve(env)
    end_time = time.time()
    st.write(f"Time taken to solve the packing problem: {end_time - start_time:.2f} seconds")

    # # Package Insertion
    # newPackage = Package(["401", "70", "70", "70", "0", "Priority", "0"])
    # start_time = time.time()
    # PackageInserter(env).parallel_replace_package(newPackage)
    # end_time = time.time()
    # st.write(f"Time taken to insert package: {end_time - start_time:.2f} seconds")

    # Show the packing animation (if implemented in your `env.animate()` method)
    st.subheader("Packing Animation")
    st.write("Showing packing animation...")

    # If `env.animate()` generates a matplotlib plot, use st.pyplot to show it
    # fig = env.animate_st()  # Assuming animate() returns a matplotlib figure
    # print(fig)
    # if fig is not None:
    #     st.pyplot(fig)  # Display the animation

    # If `env.animate()` generates a Plotly chart, use st.plotly_chart to show it
    # Uncomment this if you're using Plotly for animation
    # st.plotly_chart(env.animate())  # Assuming animate() returns a Plotly figure

    # Save the result
    solution_file = f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
    env.write(file_path=solution_file)
    st.write(f"Solution saved at {solution_file}")

    # Visualize the bin pool (original and compact bins)
    st.subheader("Bin Pool Visualization")
    st.write("Original Bin Pool")
    for i, bin in enumerate(env.get_original_bin_pool()):
        st.write(f"Bin #{i + 1}")
        st.dataframe(bin.layer_pool.describe())
        ax = bin.plot()  # Ensure your Bin class has a plot method
        st.pyplot(fig=ax)

    st.write("Compact Bin Pool")
    for i, bin in enumerate(env.compact_bins):
        st.write(f"Bin #{i + 1}")
        ax = bin.plot()
        st.pyplot(fig=ax)

# Success message
st.success("Bin packing procedure successfully completed.")
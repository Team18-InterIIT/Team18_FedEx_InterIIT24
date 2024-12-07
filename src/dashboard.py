import sys
import streamlit as st
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objs import Mesh3d
import pandas as pd
import parser
from environment import Environment
from util import Util
from insert_package import PackageInserter
from entity import Package
from algorithm_interface import PackingAlgorithm as PackingAlgorithm
from solvers.hybrid import Hybrid as PackingAlgorithm
import multiprocessing
import os

# Initialize the Plotly figure for 3D plotting
def st_animate(_env: Environment, repeat=False, stepped=True):
    """
    Animate the process of adding packages to the ULDs using Plotly and Streamlit.

    Parameters:
    repeat (bool): If True, the animation will loop after reaching the last frame.
    stepped (bool): If True, the animation will be drawn step-by-step.
    """
    # Create a subplot with a 3D scatter plot
    env.global_stability_check()
    fig = go.Figure()

    # Define the initial plot layout
    fig.update_layout(
        scene=dict(
            xaxis_title="Length",
            yaxis_title="Width",
            zaxis_title="Height",
            xaxis=dict(showbackground=True, backgroundcolor="white"),
            yaxis=dict(showbackground=True, backgroundcolor="white"),
            zaxis=dict(showbackground=True, backgroundcolor="white"),
            aspectmode="cube"
        ),
        title="3D Package Insertion Animation",
        showlegend=False
    )
    # Use a placeholder to dynamically update the plot
    plot_placeholder = st.empty()

    def update(frame):
        """
        Update function that adds the packages as 3D mesh to the plot for the given frame.
        """
        # Track ULD data (this keeps track of packages added to each ULD)
        uld_data = {uld.id: (0, 0, uld.weight_limit, 0) for uld in env.ULDs}
        
        # Clear all previous traces to prepare for the next frame
        fig.data = []

        # Add traces for packages in the current frame
        for pkg_id in env.pkg_addition_order[:frame + 1]: 
            pkg = next(pkg for pkg in env.packages if pkg.id == pkg_id)
            uld = next(uld for uld in env.ULDs if uld.id == pkg.uld_id)
            uld_data[uld.id] = (
                uld_data[uld.id][0] + 1,
                uld_data[uld.id][1] + pkg.weight,
                uld_data[uld.id][2],
                uld_data[uld.id][3] + pkg.volume() / uld.volume(),
            )
            summary = f"ULD {uld.id}\nNo. of packages: {uld_data[uld.id][0]}\nWeight: {uld_data[uld.id][1]}/{uld_data[uld.id][2]}\nVolume Utilisation: {round(uld_data[uld.id][3] * 100, 3)}%"

            # Package coordinates (vertices)
            x = [pkg.corners[0].x, pkg.corners[1].x]
            y = [pkg.corners[0].y, pkg.corners[1].y]
            z = [pkg.corners[0].z, pkg.corners[1].z]

            color = "green" if not pkg.is_priority else "cyan"
           
            if env.stable[pkg.id - 1] == -1:
                if pkg.is_priority:
                    color = "purple"
                else:
                    color = "orange"
            
            # Get the coordinates for the bottom-left and top-right corners
            x_min, y_min, z_min = pkg.corners[0].x, pkg.corners[0].y, pkg.corners[0].z
            x_max, y_max, z_max = pkg.corners[1].x, pkg.corners[1].y, pkg.corners[1].z
            
            # Define the 8 vertices of the cuboid (box)
            x = [x_min, x_min, x_max, x_max, x_min, x_min, x_max, x_max]
            y = [y_min, y_max, y_max, y_min, y_min, y_max, y_max, y_min]
            z = [z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max]

            # Define the faces of the triangular mesh
            i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
            j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
            k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]

            # Add the cuboid as a mesh (3D box)
            fig.add_trace(go.Mesh3d(
                x=x, y=y, z=z,
                i=i, j=j, k=k,
                color=color,  # Set color
                opacity=0.4,   # Set opacity
                name=f"Package {pkg.id}",
                showlegend=False,
            ))

            # Update the layout for the 3D plot
            fig.update_layout(
                title=summary,
            )

        # Display the plot step-by-step using Streamlit
        plot_placeholder.plotly_chart(fig, use_container_width=True)

    # Frame control (Next and Previous)
    if stepped:
        st.write("Step-by-step animation")
        st.write("Use the prev and next buttons below to navigate through the frames.")
        
        def next_frame():
            if st.session_state.current_frame < len(env.pkg_addition_order) - 1:
                st.session_state.current_frame += 1
                update(st.session_state.current_frame)

        def prev_frame():
            if st.session_state.current_frame >= 0:
                st.session_state.current_frame -= 1
                update(st.session_state.current_frame)

        # Create buttons for next/previous
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Previous"):
                prev_frame()
        with col2:
            if st.button("Next"):
                next_frame()

    else:
        frames = range(0, len(env.pkg_addition_order))
        for frame in frames:
            update(frame)

# Streamlit Setup
st.set_page_config(page_title="3D Bin Packing", layout="centered")  # Centering content
st.title("Team 18 Solution Dashboard")  # Title of the app

# Function to simulate streaming text (typewriter effect)
def stream_text(text, delay=0.005):
    """
    Generator function that yields text with a delay to simulate a typewriter effect.
    """
    for char in text:
        yield char
        time.sleep(delay)

# Main Content Section
st.subheader("Instructions")

# Check if the session state variable has been initialized for streaming text
if "instructions_shown" not in st.session_state:
    st.session_state.instructions_shown = False

# If the instructions have not been shown yet, stream the text
if not st.session_state.instructions_shown:
    st.write_stream(stream_text("""
        Welcome to Team-18 Solution! In this tool, you can upload your dataset, choose from various packing algorithms, and run the packing procedure. The sidebar allows you to control key parameters like search methods, orientation constraints, family packages, and more. You can enable advanced features like layering, multiprocessing, and fine-tune the beam width or number of iterations for better results. Once the algorithm is run, you can visualize the 3D packing process, view stress analysis (if enabled), and observe step-by-step animations of package insertions. The packing solution can be downloaded as a file once the process is complete.
    """))
    st.session_state.instructions_shown = True  # Set this to True to prevent rerunning the stream
else:
    st.write("""
        Welcome to Team-18 Solution. Here you can select a packing algorithm, upload your data, and 
        run the packing procedure. The sidebar allows you to control various parameters to adjust the packing 
        strategy.
    """)

# Toggle Buttons Section (Add more toggles as needed)
st.sidebar.header("Input Options")
rot_toggle = st.sidebar.toggle("Rotational Constraint", value=False)  # Example toggle
family_toggle = st.sidebar.toggle("Family Packages", value=False)  # Example toggle

if family_toggle:
    st.sidebar.write("Family Packages Enabled")
if rot_toggle:
    st.sidebar.write("Rotational Constraint Enabled")

# File Uploader Section
st.sidebar.header("Upload Test File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="txt", label_visibility="collapsed")

if uploaded_file is not None:
    # Get the uploaded file's name
    file_name = uploaded_file.name
    # Define the path to save the file (ensure the directory exists)
    save_path = os.path.join(os.getcwd(), file_name)  # Save it in the current directory
    # Save the file
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getvalue())  # Save the file content
    # Now, use the saved file as your test_file
    test_file = save_path
    # Resetting session state variables
    if "last_uploaded_file" in st.session_state:
        if st.session_state.last_uploaded_file != file_name:
            if "data_shown" in st.session_state:
                st.session_state.data_shown = False
            if "run_algorithm" in st.session_state:
                st.session_state.run_algorithm = False
    st.session_state.last_uploaded_file = file_name
else:
    # Use a default file if no file is uploaded
    default_file = "test/Challenge_FedEx.txt"
    # Check if the default file exists, else set to None
    test_file = default_file if os.path.exists(default_file) else None
    st.last_uploaded_file = None

# Slider for Algorithm Parameters Section
st.sidebar.header("Algorithm Parameters")
search_method = st.sidebar.segmented_control("Select Search Method", ["Normal Search", "Hyper Search"], key="search_method")
st.sidebar.write("Normal Search: Faster but more cost")
st.sidebar.write("Hyper Search: Slower but less cost")
if search_method == "Hyper Search":
    is_hyper = True
else:
    is_hyper = False

is_layering = st.sidebar.toggle("Enable Layering", key="layering_toggle", disabled=is_hyper)
if is_layering is None:
    is_layering = False

is_multiprocessing = st.sidebar.toggle("Enable Multiprocessing", key="multiprocessing_toggle", value=is_hyper, disabled=is_hyper)
if is_multiprocessing is None:
    is_multiprocessing = False

beam_width = st.sidebar.slider("Beam Width", min_value=1, max_value=20, value=10, key="beam_width", disabled=not is_hyper)
num_iterations = st.sidebar.slider("Number of Iterations", min_value=10, max_value=200, value=100, key="num_iterations")
num_cores = st.sidebar.slider("Number of Cores", min_value=1, max_value=multiprocessing.cpu_count(), value=multiprocessing.cpu_count(), key="num_cores", disabled=not is_multiprocessing)
# Parse the dataset using the parser
@st.cache_data
def load_data(file):
    # Use the parser directly to extract ULDs and packages from the file
    if file is None:
        return -1, [], []
    parser_instance = parser.Parser(file)
    K = parser_instance.get_K()
    uld_list = parser_instance.get_uld_list()
    pkg_list = parser_instance.get_pkg_list()
    return K, uld_list, pkg_list

# Load data (without CSV reading)
K, uld_list, pkg_list = load_data(test_file)

# Convert package list to a DataFrame and label the columns properly
df_pkg_list = pd.DataFrame(pkg_list, columns=[
    "Package Identifier", "Length (cm)", "Width (cm)", "Height (cm)", "Weight (kg)", "Type (P/E)", "Cost of Delay"
])

# Center-aligning the main content
st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)

# Check if the session state variable has been initialized for streaming text
if "data_shown" not in st.session_state:
    st.session_state.data_shown = False

# If the instructions have not been shown yet, stream the text
if not st.session_state.data_shown:
    # Show dataset summary
    st.subheader("Dataset Summary")
    st.write_stream(stream_text(f"Number of Packages: {len(pkg_list)}"))
    st.write_stream(stream_text(f"Number of ULDs: {len(uld_list)}"))

    # Visualizing some of the package information (optional)
    st.write_stream(stream_text("Package List:"))
    st.dataframe(df_pkg_list)  # Show the dataframe with proper column names
    st.session_state.data_shown = True  # Set this to True to prevent rerunning the stream
else:
    # Show dataset summary
    st.subheader("Dataset Summary")
    st.write(f"Number of Packages: {len(pkg_list)}")
    st.write(f"Number of ULDs: {len(uld_list)}")
    # Visualizing some of the package information (optional)
    st.write("Package List:")
    st.dataframe(df_pkg_list)  # Show the dataframe with proper column names

# Run the Packing Algorithm
if "run_algorithm" not in st.session_state:
    st.session_state.run_algorithm = False

@st.cache_data
def run_algo(file=test_file,
             orientation_constraint=False, 
             families=False, 
             search="Normal Search", 
             layering=True,
             multiprocessing=True,
             beam_width=None,
             n_calls=100,
             n_jobs=-1):
    # Load data (without CSV reading)
    K, uld_list, pkg_list = load_data(file)

    # Create the environment
    env = Environment(K, uld_list, pkg_list, orientation_constraint=orientation_constraint, families=family_packages)

    # Select and run the packing algorithm
    model = PackingAlgorithm()

    start_time = time.time()
    with st.spinner('Running packing algorithm...'):
        if search == "Normal Search":
            search_method = "normal"
        else:
            search_method = "hyper"
        model.solve(env=env, 
                    search=search_method, 
                    layering=layering, 
                    multiprocessing=multiprocessing, 
                    beam_width=beam_width, 
                    n_calls=n_calls,
                    n_jobs=n_jobs)
    end_time = time.time()
    st.write(f"Time taken to solve the packing problem: {end_time - start_time:.2f} seconds")
    st.write(f"Total Cost: {sum(env.cost())}")
    return env

@st.cache_data
def st_plot(_env, file=test_file, stress_plot=False):
    # Show the packing animation (if implemented in your `env.animate()` method)
    st.subheader("Packing Animation")
    st.write("Showing packing animation...")
    fig = env.plot(return_fig=True, stress_plot=stress_plot)
    st.pyplot(fig, clear_figure=False)

if st.session_state.run_algorithm or st.button("Run Packing Algorithm"):

    orientation_constraint = True if rot_toggle else False
    family_packages = True if family_toggle else False
    env = run_algo(file=test_file, 
                   orientation_constraint=orientation_constraint, 
                   families=family_packages, 
                   search=search_method, 
                   layering=is_layering,
                   multiprocessing= is_multiprocessing,
                   beam_width=beam_width,
                   n_calls=num_iterations,
                   n_jobs=num_cores)
    
    # Order the packages for insertion
    order = Util(env).order()
    env.pkg_addition_order = []
    for uld_id, order_list in order.items():
        env.pkg_addition_order.extend(order_list)
    
    is_stress_plot = st.toggle("Stress Plot", value=False)
    if is_stress_plot is None:
        is_stress_plot = False
    st_plot(env, file=test_file, stress_plot=is_stress_plot)

    if "current_frame" not in st.session_state:
        st.session_state.current_frame = -1

    st_animate(env) # Animate the package insertion process

    # Save the result
    solution_file = f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
    env.write(file_path=solution_file)
    st.write(f"Solution saved at {solution_file}")
    data = open(solution_file, "rb").read()
    st.download_button(label="Download Solution", data=data, file_name=solution_file)
    st.session_state.run_algorithm = True

# Closing the div tag for center-alignment
st.markdown('</div>', unsafe_allow_html=True)

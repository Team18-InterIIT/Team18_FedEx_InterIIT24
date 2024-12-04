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

# Initialize the Plotly figure for 3D plotting
def animate_st(env: Environment, repeat=False, stepped=True):
    """
    Animate the process of adding packages to the ULDs using Plotly and Streamlit.

    Parameters:
    repeat (bool): If True, the animation will loop after reaching the last frame.
    stepped (bool): If True, the animation will be drawn step-by-step.
    """
    # Create a subplot with a 3D scatter plot
    fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'scatter3d'}]])

    # Define the initial plot layout (Match Matplotlib style)
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

    # Updating the animation frame-by-frame
    def update(frame):
        fig.data = []  # Clear previous data
        
        uld_data = {uld.id: (0, 0, uld.weight_limit, 0) for uld in env.ULDs}
        
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

            # Add package as mesh (3D box)
            fig.add_trace(Mesh3d(
                x=x, y=y, z=z,
                color=color,
                opacity=0.5,
                name=f"Package {pkg.id}",
                showlegend=False
            ))

            # Update ULD title
            fig.update_layout(
                title=summary
            )

        # Display the plot step-by-step
        st.plotly_chart(fig, use_container_width=True)

    # Frame control (Next and Previous)
    if stepped:
        st.write("Step-by-step animation")
        current_frame = -1

        def next_frame():
            nonlocal current_frame
            if current_frame < len(env.pkg_addition_order) - 1:
                current_frame += 1
                update(current_frame)

        def prev_frame():
            nonlocal current_frame
            if current_frame >= 0:
                current_frame -= 1
                update(current_frame)

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

# Dynamically import the algorithm based on user selection
ALGORITHMS = {
    "ThreeDBP_Pivoting": "solvers.threeDBP_Pivoting",
    "COA (Caving COA)": "solvers.Caving_COA",
    "LayerPacking (Layer Strat with OR)": "solvers.layerstratwithOR",
}

# Streamlit Setup
st.set_page_config(page_title="3D Bin Packing", layout="centered")  # Centering content
st.title("3D Bin Packing")

# Function to simulate streaming text (typewriter effect)
def stream_text(text, delay=0.005):
    """
    Generator function that yields text with a delay to simulate a typewriter effect.
    """
    for char in text:
        yield char
        time.sleep(delay)

# Sidebar Section
st.sidebar.header("Instructions")

# Check if the session state variable has been initialized for streaming text
if "instructions_shown" not in st.session_state:
    st.session_state.instructions_shown = False

# If the instructions have not been shown yet, stream the text
if not st.session_state.instructions_shown:
    st.write_stream(stream_text("""
        Welcome to Team-18 Solution. Here you can select a packing algorithm, upload your data, and 
        run the packing procedure. The sidebar allows you to control various parameters to adjust the packing 
        strategy.
    """))
    st.session_state.instructions_shown = True  # Set this to True to prevent rerunning the stream
else:
    st.write("""
        Welcome to Team-18 Solution. Here you can select a packing algorithm, upload your data, and 
        run the packing procedure. The sidebar allows you to control various parameters to adjust the packing 
        strategy.
    """)

# File Uploader Section
st.sidebar.header("Upload Test File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="txt", label_visibility="collapsed")
test_file = uploaded_file if uploaded_file else "test/Challenge_FedEx.txt"

# Algorithm Selection Section
st.sidebar.header("Select Packing Algorithm")
algorithm_choice = st.sidebar.selectbox("Choose Algorithm", list(ALGORITHMS.keys()))

# Dynamically import the selected algorithm
if algorithm_choice == "ThreeDBP_Pivoting":
    from solvers.threeDBP_Pivoting import ThreeDBP_Pivoting as PackingAlgorithm
elif algorithm_choice == "COA (Caving COA)":
    from solvers.Caving_COA import COA as PackingAlgorithm
elif algorithm_choice == "LayerPacking (Layer Strat with OR)":
    from solvers.layerstratwithOR import LayerPacking as PackingAlgorithm

# Toggle Buttons Section (Add more toggles as needed)
st.sidebar.header("Input Options")
rot_toggle = st.sidebar.checkbox("Rotational Constraint", value=False)  # Example toggle
cluster_toggle = st.sidebar.checkbox("Cluster Packages", value=False)  # Example toggle
family_toggle = st.sidebar.checkbox("Family Packages", value=False)  # Example toggle

if cluster_toggle:
    st.sidebar.write("Cluster Packages Enabled")
if family_toggle:
    st.sidebar.write("Family Packages Enabled")
if rot_toggle:
    st.sidebar.write("Rotational Constraint Enabled")

# Slider for Algorithm Parameters Section
st.sidebar.header("Algorithm Parameters")
tlim = st.sidebar.slider("Time limit (seconds)", 1, 100, 10)
max_iters = st.sidebar.slider("Maximum iterations", 1, 5, 1)

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
if st.button("Run Packing Algorithm"):
   
    # Load data (without CSV reading)
    K, uld_list, pkg_list = load_data(test_file)

    # Create the environment
    env = Environment(K, uld_list, pkg_list)

    # Select and run the packing algorithm
    model = PackingAlgorithm()
    start_time = time.time()
    with st.spinner('Running packing algorithm...'):
        model.solve(env)
    end_time = time.time()
    st.write(f"Time taken to solve the packing problem: {end_time - start_time:.2f} seconds")

    # Show the packing animation (if implemented in your `env.animate()` method)
    st.subheader("Packing Animation")
    st.write("Showing packing animation...")

    fig = env.plot()
    st.pyplot(fig, clear_figure=False)

    # Save the result
    solution_file = f"solutions/{str(PackingAlgorithm.__name__)}/{test_file.split('/')[-1]}"
    env.write(file_path=solution_file)
    st.write(f"Solution saved at {solution_file}")

# Closing the div tag for center-alignment
st.markdown('</div>', unsafe_allow_html=True)

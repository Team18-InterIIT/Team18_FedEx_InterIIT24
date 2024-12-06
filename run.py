import os
import platform
import subprocess
import sys

def install_requirements():
    """Install dependencies from requirements.txt and print status for each requirement."""
    try:
        print("Checking and installing dependencies from requirements.txt...")
        with open("requirements.txt", "r") as req_file:
            requirements = req_file.readlines()

        for req in requirements:
            req = req.strip()  # Remove any leading/trailing whitespace
            if req:  # Skip empty lines
                # Check if the package is already installed
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", req]
                )
                
                if result.returncode == 0:
                    print(f"'{req}' found.")
                else:
                    print(f"Installing '{req}'...")
                    install_result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", req]
                    )
                    
                    if install_result.returncode != 0:
                        print(f"Failed to install '{req}': {install_result.stderr}")
                    else:
                        print(f"'{req}' installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to check or install requirements: {e}")
        sys.exit(1)

def run_streamlit():
    """Run the Streamlit dashboard."""
    try:
        print("Running Streamlit app...")
        subprocess.check_call([sys.executable, "-m", "streamlit", "run", "src/dashboard.py"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Streamlit: {e}")
        sys.exit(1)

def local_tc():
    """Run the local test case command."""
    try:
        print("Running local test case...")
        result = subprocess.run(
            ["python3", "src/main.py", "test/Challenge_FedEx.txt"]
        )
        
        if result.returncode != 0:
            print(f"Test case failed with return code {result.returncode}")
        else:
            print("Test case ran successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run test case: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Detect operating system
    os_type = platform.system()
    print(f"Detected OS: {os_type}")

    # Install dependencies
    install_requirements()

    # Run local test case
    local_tc()

    # Run Streamlit
    run_streamlit()

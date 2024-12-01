#!/bin/bash

# Paths
SOLVERS_DIR="src/solvers"
TEST_CASES_DIR="test/testcases"
OUTPUT_DIR="output"
ERROR_FILE="$OUTPUT_DIR/error.txt"

# Clear previous outputs
mkdir -p "$OUTPUT_DIR"
> "$ERROR_FILE"

# Check directories
if [[ ! -d "$SOLVERS_DIR" ]]; then
    echo "Error: Solvers directory '$SOLVERS_DIR' does not exist!" | tee -a "$ERROR_FILE"
    exit 1
fi

if [[ ! -d "$TEST_CASES_DIR" ]]; then
    echo "Error: Test cases directory '$TEST_CASES_DIR' does not exist!" | tee -a "$ERROR_FILE"
    exit 1
fi

# Iterate over all solvers
for solver_file in "$SOLVERS_DIR"/*.py; do
    solver_module="solvers.$(basename "$solver_file" .py)"
    echo "Using solver: $solver_module" | tee -a "$ERROR_FILE"

    # Process each test case with the current solver
    for test_case in "$TEST_CASES_DIR"/*; do
        if [[ -f "$test_case" ]]; then
            test_name=$(basename "$test_case")
            output_file="$OUTPUT_DIR/${test_name}_${solver_module##*.}.txt"

            echo "Processing test case: $test_name with solver $solver_module" | tee -a "$ERROR_FILE"

            # Run the main Python script, redirect both stdout and stderr to the output file
            {
                # Run Python script with test case and solver module
                python3 src/main.py "$test_case" "$solver_module"
            } > "$output_file" 2>&1  # Capture both stdout and stderr

            # Check for success
            if [[ $? -eq 0 ]]; then
                echo "Successfully processed $test_name with solver $solver_module." | tee -a "$output_file"
            else
                echo "Error processing $test_name with solver $solver_module. Check $ERROR_FILE." | tee -a "$ERROR_FILE"
            fi
        else
            echo "Skipping non-file item: $test_case" | tee -a "$ERROR_FILE"
        fi
    done
done

echo "All test cases processed. Results saved in $OUTPUT_DIR." | tee -a "$ERROR_FILE"

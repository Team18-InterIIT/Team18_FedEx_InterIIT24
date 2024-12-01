#!/bin/bash

# List of required libraries
DEPENDENCIES=("grep" "file" "pdftohtml" "tesseract" "exiftool")

# Function to detect Linux distribution and set package manager
detect_package_manager() {
    if command -v apt-get &>/dev/null; then
        PACKAGE_MANAGER="sudo apt-get install -y"
    elif command -v dnf &>/dev/null; then
        PACKAGE_MANAGER="sudo dnf install -y"
    elif command -v yum &>/dev/null; then
        PACKAGE_MANAGER="sudo yum install -y"
    elif command -v pacman &>/dev/null; then
        PACKAGE_MANAGER="sudo pacman -S --noconfirm"
    elif command -v zypper &>/dev/null; then
        PACKAGE_MANAGER="sudo zypper install -y"
    elif command -v apk &>/dev/null; then
        PACKAGE_MANAGER="sudo apk add"
    elif command -v brew &>/dev/null; then
        PACKAGE_MANAGER="brew install"
    else
        echo "Error: No compatible package manager found. Please install dependencies manually."
        exit 1
    fi
}

# Install missing dependencies
install_dependencies() {
#     echo "Checking for required dependencies..."
    for dep in "${DEPENDENCIES[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            echo "Installing missing dependency: $dep"
            eval "$PACKAGE_MANAGER $dep" &>/dev/null &
        # else
        #     echo "$dep is already installed."
        fi
    done
    wait
    # echo "Dependency check complete."
}

# Detect package manager
detect_package_manager

# Start installing dependencies in the background
install_dependencies &

PHRASES=("IITM" "Indian institute" "Madras") # List of case-insensitive terms to search for

shopt -s globstar
directory_to_scan="$1"
# Check if the directory was provided
if [ -z "$directory_to_scan" ]; then
    directory_to_scan="."
fi

# Check if the directory exists
if [ ! -d "$directory_to_scan" ]; then
    echo "The directory '$directory_to_scan' does not exist."
    exit 1
fi

for file in "$directory_to_scan"/**/*; do
    if [[ "$(basename "$file")" == "scan.sh" ]]; then
        continue
    fi 

    FILE_DATA=$(file "$file")
    
    # Process text or ASCII files
    if echo "$FILE_DATA" | grep -qE "text|ASCII"; then
        MATCH=0
        for PHRASE in "${PHRASES[@]}"; do
            grep -i -H -n --color "$PHRASE" "$file"
            if [ $? -eq 0 ]; then
                MATCH=1
            fi
        done
        if [ $MATCH -eq 0 ]; then
            echo -e "\e[32m$file OK\e[0m"
        fi
    # Process PDF files
    elif echo "$FILE_DATA" | grep -qE "pdf"; then
        TEMP_HTML_FILE="$(basename "$file" .pdf).html.xml" # Temporary HTML file
        TEMP_HTML_DIR="tmpscan_$(basename "$file" .pdf)" # Temporary directory for HTML file
        mkdir -p "$TEMP_HTML_DIR"
        pdftohtml -q -c -hidden -xml "$file" "$TEMP_HTML_DIR/$TEMP_HTML_FILE" # Convert PDF to HTML (with hidden elements)
        MATCH=0
        for PHRASE in "${PHRASES[@]}"; do
            # Search the HTML file for phrases
            grep -i -H -n --color "$PHRASE" "$TEMP_HTML_DIR/$TEMP_HTML_FILE"    
            if [ $? -eq 0 ]; then
                MATCH=1
            fi
        done
        if [ $MATCH -eq 0 ]; then
            echo -e "\e[32m$file OK\e[0m"
        fi
        # urls=$(grep -oE 'https?://[a-zA-Z0-9./?=_-]+' "$TEMP_HTML_DIR/$TEMP_HTML_FILE")
        # for url in $urls; do
        #     curl -s "$url" | grep -i -H -n --color "$PHRASES"
        # done

        # OCR on the image files
        TEMP_OCR_FILE="${file}_ocr.txt" # Create temp file for OCR text
        MATCH=0
        for subfile in "$TEMP_HTML_DIR"/*; do
            if echo "$subfile" | grep -qE "jpg|png"; then
                OCR_TEXT=$(tesseract "$subfile" - 2>/dev/null) # Perform OCR on image file
                if [ -z "$OCR_TEXT" ]; then
                    _TMP=$(echo "$OCR_TEXT" | grep -i -E -n --color "$PHRASES") # Perform OCR on image file
                    echo "OCR2 : $_TMP"
                    if( [ $? -ne 0 ] ); then
                        MATCH=1
                    else 
                        echo -e "\e[35m$subfile\e[0m : \e[31m$_TMP\e[0m"
                    fi
                fi
            fi
        done
        if [ $MATCH -eq 0 ]; then
            echo -e "\e[32m$file OCR OK\e[0m"
        fi
        rm -r -f "$TEMP_HTML_DIR" # Clean up temp HTML file after processing

    # Process metadata with ExifTool
        TEMP_METADATA_FILE="${file}_metadata.txt" # Create temp file for metadata
        exiftool "$file" > "$TEMP_METADATA_FILE" # Extract metadata to temp file
        MATCH=0
        for PHRASE in "${PHRASES[@]}"; do
            grep -i --color "$PHRASE" "$TEMP_METADATA_FILE"
            if [ $? -eq 0 ]; then
                MATCH=1
            fi
        done
        if [ $MATCH -eq 0 ]; then
            echo -e "\e[32m$file Metadata OK\e[0m"
        fi
        rm -f "$TEMP_METADATA_FILE" # Clean up temp file after processing
    fi
done
exit 0


shopt -s globstar

PHRASE=$"IITM" # Case insensitive term being searched for

for file in ./docs/**/*; do
    FILE_DATA=$(file "$file")
    if echo $FILE_DATA | grep -qE "text|ASCII"; then
        grep -i -H -n --color iitm $file 
        if [ $? -ne 0 ]; then
            echo -e "\e[32m$file OK\e[0m"
        fi
    elif echo $FILE_DATA | grep -qE "pdf"; then
        pdftotext $file - | grep -i -H -n --color $PHRASE
        if [ $? -ne 0 ]; then
            echo -e "\e[32m$file OK\e[0m"
        fi
    fi
done
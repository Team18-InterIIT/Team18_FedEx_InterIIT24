shopt -s globstar
for file in ./docs/**/*; do
    echo "$file"
    echo file "$file"
done

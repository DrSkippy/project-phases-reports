
dt=$(date +%Y-%m-%d:%H%M)
echo $dt
src=/Users/s.hendrickson/Documents/OneDrive\ -\ F5,\ Inc/Projects\ Folders/
dest=/Users/s.hendrickson/Working/project-phases-reports/tests/projects_snapshot/
cd "${dest}"
read -p "Warning-Deleting everything in ${dest}"
rm -r *
cd "${src}"
echo "Creating new snapshot..."
# find . -depth 3 -name "PROJECT_INFO.txt" -exec echo {} \; 
# OSX
find . -depth 3 -name "PROJECT_INFO.txt" -exec ditto "{}" "${dest}{}" \;
# Bash
# find . -depth 3 -name "PROJECT_INFO.txt" -exec cp --parents "{}" "${dest}{}" \;
cd "${dest}"
nfiles=5
echo "Culling files to ${nfiles} per phase..."
for phases in *; do
  echo "${phases}"
  cd "${phases}"
  count=0
  for projects in *; do
    if ((count < ${nfiles})); then
      echo "Keeping ${projects}..."
    else
      echo "Deleting ${projects}..."
      rm -r "${projects}"
    fi
    ((count++))
  done
  cd ..
done

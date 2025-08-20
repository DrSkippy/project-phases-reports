echo "Creating a new project snapshot tarball"
dt=$(date +%Y-%m-%d_%H%M)
echo "Started at $dt"
src=/Users/s.hendrickson/Documents/OneDrive\ -\ F5,\ Inc/Projects\ Folders/
dest=/Users/s.hendrickson/Working/project-phases-reports/tests/projects_snapshot/
cd "${dest}"
echo "*********************************************"
echo "Warning-Deleting everything in ${dest}"
read -p "Hit enter to continue or Ctrl-C to abort"
echo "*********************************************"
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
cd ..
echo "Creating tarball..."
tar -cvzf ./projects_snapshot.tar.gz projects_snapshot
echo "Creation complete"

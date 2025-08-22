# diff_snapshot.sh
# Compares PROJECT_INFO.txt files between two project snapshot directories.

# Exit immediately if a command exits with a non-zero status.
set -e

# Record the start time.
dt=$(date +%Y-%m-%d_%H%M)
echo "Started at $dt"

# Source and destination snapshot directories.
src=projects_snapshot_original/
dest=projects_snapshot/

# Change to the destination's Projects Folders directory.
cd "${dest}Projects Folders/"

echo "Comparing files per phase..."

# Loop through each phase directory.
for phases in */; do
  echo "${phases}"
  cd "${phases}"
  # Loop through each project in the phase.
  for projects in *; do
    echo "comparing ${projects}..."
    # Compare PROJECT_INFO.txt files and show differences.
    diff -r "../../../${src}Projects Folders/${phases}/${projects}/PROJECT_INFO.txt" "${projects}/PROJECT_INFO.txt" || true
  done
  cd ..
done

echo "Comparison complete"
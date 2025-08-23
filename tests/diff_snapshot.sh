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

echo "Copying files to temporary space for comparison..."
# temporary space for diff inputs (so we can move between phasews
tmp=/tmp/project_diff/
rm -rf "${tmp}"
mkdir -p "${tmp}/updated"
mkdir -p "${tmp}/original"

cd "${src}Projects Folders/"
# Loop through each phase directory.
for phases in */; do
  echo "${phases}"
  cd "${phases}"
  # Loop through each project in the phase.
  for projects in *; do
    cp -r "${projects}/PROJECT_INFO.txt" "${tmp}original/${projects}.txt"
  done
  cd ..
done

cd "../../${dest}Projects Folders/"
# Loop through each phase directory.
for phases in */; do
  echo "${phases}"
  cd "${phases}"
  # Loop through each project in the phase.
  for projects in *; do
    cp -r "${projects}/PROJECT_INFO.txt" "${tmp}updated/${projects}.txt"
  done
  cd ..
done

echo "Using temporary directory: ${tmp}"
# Copy the source snapshot to the temporary directory.
# Change to the destination's Projects Folders directory.

cd "${tmp}/updated"
echo "Comparing files per phase..."
echo "*************************************************************************"
# Loop through each phase directory.
for projects in *; do
  echo "-----------------------------------"
  echo "comparing ${projects}..."
  # Compare PROJECT_INFO.txt files and show differences.
  diff -r "${tmp}updated/${projects}" "${tmp}original/${projects}" || true
done

echo "*************************************************************************"
echo "Comparison complete!"
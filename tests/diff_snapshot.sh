set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"

# Record the start time.
dt=$(date +%Y-%m-%d_%H%M)

cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}/Projects Folders"
echo "Working in $(pwd)"

# Source and destination snapshot directories.
src="${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
src_orig="${PROJECT_PHASES_TEST_SNAPSHOT_ORIGINAL_DIRECTORY}"

echo "*************************************************************************"
echo "Copying files to temporary space for comparison..."

tmp=/tmp/project_diff
echo "Using temporary directory: ${tmp}"
# Copy the source snapshot to the temporary directory.
# Change to the src_origination's Projects Folders directory.

rm -rf "${tmp}"
mkdir -p "${tmp}/updated"
mkdir -p "${tmp}/original"

# Loop through each phase directory.
for phase in */; do
  #echo "${phase}"
  cd "${phase}"
  # Loop through each project in the phase.
  for project in *; do
    [ -f "${project}/PROJECT_INFO.txt" ] && cp "${project}/PROJECT_INFO.txt" "${tmp}/updated/${project}.txt"
  done
  cd ..
done

cd "${src_orig}/Projects Folders/"
# Loop through each phase directory.
for phase in */; do
  #echo "${phase}"
  cd "${phase}"
  # Loop through each project in the phase.
  for project in *; do
    [ -f "${project}/PROJECT_INFO.txt" ] && cp "${project}/PROJECT_INFO.txt" "${tmp}/original/${project}.txt"
  done
  cd ..
done

echo "*************************************************************************"
tree "${tmp}"
echo "*************************************************************************"
cd "${tmp}/updated"
echo "Comparing files per phase..."
echo "*************************************************************************"
# Loop through each phase directory.
for project in *; do
  echo "-----------------------------------"
  echo "comparing ${project}..."
  # Compare PROJECT_INFO.txt files and show differences.
  diff -r "${tmp}/updated/${project}" "${tmp}/original/${project}" || true
done

echo "*************************************************************************"
echo "Comparison complete!"
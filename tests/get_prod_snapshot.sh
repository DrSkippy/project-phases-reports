set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"
echo "Creating a new project snapshot tarball"

dt=$(date +%Y-%m-%d_%H%M)

src="${PROJECT_PHASES_PROD_PROJECTS_FOLDERS_DIRECTORY}"
dest="${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
cd "${dest}"

echo "*********************************************"
echo "Warning-Deleting everything in ${dest}"
read -p "Hit enter to continue or Ctrl-C to abort"
echo "*********************************************"
rm -r *

cd "${src}"
cd ..    # Go up to "Projects Folders" parent directory so the destination has the same structure.
echo "Creating new snapshot of ${src}..."
find . -depth 4 -name "PROJECT_INFO.txt" -exec echo {} \;
# OSX
echo "Copying files to ${dest}..."
find . -depth 4 -name "PROJECT_INFO.txt" -exec ditto "{}" "${dest}{}" \;

cd "${dest}Projects Folders/"
nfiles=5
echo "*************************************************************************"
echo "Culling files to ${nfiles} per phase..."
for phase in *; do
  echo "${phase}"
  cd "${phase}"
  count=0
  for project in *; do
    if ((count < ${nfiles})); then
      echo "Keeping ${project}..."
    else
      echo "Deleting ${project}..."
      rm -r "${project}"
    fi
    ((count++))
  done
  cd ..
done
cd ../.. # Go back to directory with projects snapshot

echo "*************************************************************************"
projects_snapshot=$(basename "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}")
echo "Creating tarball of ${projects_snapshot}..."
tar -cvzf "./projects_snapshot_${dt}.tar.gz" "${projects_snapshot}"
echo "Creation complete"

set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"
echo "use options -p to scan production"

if [ "${1:-}" = "-V1" ]; then
  echo "Using ../bin/update_summary.py (V1) executable"
  UPDATE_SUMMARY="${PROJECT_PHASES_REPOSITORY_DIRECTORY}/bin/update_summary.py"
else
  echo "Using ../bin/update_summary_V2.py (V2) executable"
  UPDATE_SUMMARY="${PROJECT_PHASES_REPOSITORY_DIRECTORY}/bin/update_summary_v2.py"
fi
echo "Executable set to ${UPDATE_SUMMARY}"

# Record the start time.
dt=$(date +%Y-%m-%d_%H%M)

echo "Working in $(pwd)"

# make directories if they don't exist
mkdir -p "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
mkdir -p "${PROJECT_PHASES_TEST_SNAPSHOT_ORIGINAL_DIRECTORY}"

echo "*************************************************************************"
echo "Remove old snapshot directories if they exist..."
cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
rm -rf *
cd "${PROJECT_PHASES_TEST_SNAPSHOT_ORIGINAL_DIRECTORY}"
rm -rf *

cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
cd ..

echo "Unpacking new snapshot of production data..."
tar -xvzf projects_snapshot.tar.gz
echo "Created comparison (original) copy of original snapshot as projects_snapshot_original/"
cp -r projects_snapshot/* projects_snapshot_original/

echo "*************************************************************************"
echo "Updating summary report for initial snapshot..."
poetry run python ${UPDATE_SUMMARY}

./diff_snapshot.sh

echo "*************************************************************************"
echo "Promoting some projects to next phase..."
./promote_projects.sh

echo "*************************************************************************"
echo "Updating summary report for initial snapshot..."
poetry run python ${UPDATE_SUMMARY}

./diff_snapshot.sh

echo "*************************************************************************"
echo "Check the diffs for appropriate changes -- complete!"

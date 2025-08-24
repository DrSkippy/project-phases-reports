set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"

# Record the start time.
dt=$(date +%Y-%m-%d_%H%M)

cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
cd ..
echo "Working in $(pwd)"

echo "*************************************************************************"
echo "Remove old snapshot directories if they exist..."
rm -r projects_snapshot/
rm -r projects_snapshot_original/

echo "Unpacking new snapshot of production data..."
tar -xvzf projects_snapshot.tar.gz
echo "Created comparison (original) copy of original snapshot as projects_snapshot_original/"
cp -r projects_snapshot projects_snapshot_original

echo "*************************************************************************"
echo "Updating summary report for initial snapshot..."
poetry run python ../bin/update_summary_v2.py

./diff_snapshot.sh

echo "*************************************************************************"
echo "Promoting some projects to next phase..."
./promote_projects.sh

echo "*************************************************************************"
echo "Updating summary report for initial snapshot..."
poetry run python ../bin/update_summary_v2.py

./diff_snapshot.sh

echo "*************************************************************************"
echo "Check the diffs for appropriate changes -- complete!"
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

######################################################################################
# TEST is to move a single project through all phases, starting with a clean snapshot.
#    "0-Ideas"
#    "1-Chartering"
#    "2-Committed"
#    "3-In Progress"
#    "4-On Hold"
#    "5-Rollout"
#    "6-Completed"
#
# STEPS:
#  1. Unpack a clean snapshot with a single project in 0-Ideas phase.
#  2. Update summary report.
#  3. Diff snapshot to show project in 0-Ideas phase.
#  4. Promote project to 1-Chartering.
#  5. Update summary report.
#  6. Diff snapshot to show project in 1-Proposals phase.
#  7. Promote project to 2-Committed.
#  8. Update summary report.
#  9. Diff snapshot to show project in 2-Committed phase.
# 10. Promote project to 3-In Progress.
# 11. Update summary report.
# 12. Diff snapshot to show project in 3-In Progress phase.
# 13. Promote project to 4-On Hold.
# 14. Update summary report.
# 15. Diff snapshot to show project in 4-On Hold phase.
# 16. Revert project back to 3-In Progress.
# 17. Update summary report.
# 18. Diff snapshot to show project back in 3-In Progress phase.
# 19. Promote project to 5-Rollout.
# 20. Update summary report.
# 21. Diff snapshot to show project in 5-Rollout phase.
# 22. Promote project to 6-Completed.
# 23. Update summary report.
# 24. Diff snapshot to show project in 6-Completed phase.
######################################################################################
phase_seq=("0-Ideas" "1-Chartering" "2-Committed" "3-In Progress" "4-On Hold" "3-In Progress" "5-Rollout" "6-Completed")
PROJECT_NAME="Sample Project for Testing"
CLEAN_PROJECT_FILE="${PROJECT_PHASES_REPOSITORY_DIRECTORY}/tests/clean_sample_PROJECT_INFO.txt"
echo "Using clean project file: ${CLEAN_PROJECT_FILE}"

cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}"
cd ..
echo "Working in $(pwd)"

echo "*************************************************************************"
echo "Remove old snapshot directories if they exist and build new empty ones..."
rm -rf "projects_snapshot/Projects Folders"
rm -rf "projects_snapshot_original/Projects Folders"

echo "Creating snapshot of production data..."
mkdir -p projects_snapshot
mkdir -p "projects_snapshot/Projects Folders"
for phase in "${phase_seq[@]}"; do
  mkdir -p "projects_snapshot/Projects Folders/${phase}"
done

echo "*************************************************************************"
echo "Adding clean project to initial phase..."
LAST_PHASE="${phase_seq[0]}"
mkdir -p "projects_snapshot/Projects Folders/${LAST_PHASE}/${PROJECT_NAME}"
cp "${CLEAN_PROJECT_FILE}" "projects_snapshot/Projects Folders/${LAST_PHASE}/${PROJECT_NAME}/PROJECT_INFO.txt"
cp -r projects_snapshot/* projects_snapshot_original

echo "*************************************************************************"
for next_phase in "${phase_seq[@]:1}"; do
  echo "Updating summary report for initial snapshot..."
  poetry run python ${UPDATE_SUMMARY}
  echo "Running diff to show project in ${LAST_PHASE} phase..."
  ./diff_snapshot.sh
  echo "Promoting project from ${LAST_PHASE} to ${next_phase}..."
  mv "projects_snapshot/Projects Folders/${LAST_PHASE}/${PROJECT_NAME}" "projects_snapshot/Projects Folders/${next_phase}/"
  LAST_PHASE="${next_phase}"
done

echo "Updating summary report for initial snapshot..."
poetry run python ${UPDATE_SUMMARY}
echo "Running diff to show project in ${LAST_PHASE} phase..."
./diff_snapshot.sh

echo "*************************************************************************"
echo "Check the diffs for appropriate changes -- complete!"
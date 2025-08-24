set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"

cd "${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}/Projects Folders/"
echo "Working in snapshot directory $(pwd)"

# reverse order is important (will move the sam file over and over if not
from_phases=("5-Rollout" "3-In Progress" "3-In Progress" "2-Committed"   "1-Chartering" "0-Ideas")
to_phases=("6-Completed" "6-Completed"   "4-On Hold"     "3-In Progress" "2-Committed"  "1-Chartering")

# move projects in working, destination snapshot directories.
for i in "${!from_phases[@]}"; do
  a="${from_phases[i]}"
  b="${to_phases[i]}"
  cd "${a}"
  projects=(*)
  # chose the second project to move (if it exists)
  first_project="${projects[0]}"
  echo "Moving ${first_project} from ${a} to ${b}..."
  mv "${first_project}" "../${b}/"
  cd ..
done

echo "*************************************************************************"
echo "Moves complete!"
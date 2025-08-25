set -e   # exit on error
set -u   # treat unset variables as an error
echo "Started at $(date)"
echo "*************************************************************************"
echo "use options -p to scan production"

if [ "${1:-}" = "-p" ]; then
  echo "Using PRODUCTION data"
  BASE_DIR="${PROJECT_PHASES_PROD_PROJECTS_FOLDERS_DIRECTORY}"
else
  echo "Using TEST data"
  BASE_DIR="${PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY}/Projects Folders"
fi
cd "${BASE_DIR}"

echo
echo "Working in ${BASE_DIR}"

echo
echo "*************************************************************************"
grep "^BUSINESS_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort
echo
echo "*************************************************************************"
grep "^ANALYTICS_DS_OWNER" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort
echo
echo "*************************************************************************"
grep "^DATA_OFFICE_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort
echo
echo "*************************************************************************"
grep "^Project_ID" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort 

set +e
echo
echo "Files with blank entries:"
echo "*************************************************************************"
grep -e "^BUSINESS_SPONSOR: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt
grep -e "^ANALYTICS_DS_OWNER: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt 
grep -e "^DATA_OFFICE_SPONSOR: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt 

echo
echo "Owners without email addresses:"
echo "*************************************************************************"
grep -e "^ANALYTICS_DS_OWNER" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v "@" | grep -v "Unassigned"
grep -e "^DATA_OFFICE_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v "@" | grep -v "Unassigned"


echo
echo "Files without an owner:"
echo "*************************************************************************"
for fl in  "${BASE_DIR}"/*/*/PROJECT_INFO.txt; do
  if ! grep -e "^ANALYTICS_DS_OWNER" "$fl" > /dev/null
  then
    echo $fl
  fi
done


echo
echo "Cleaning files with repeated None metrics:"
echo "*************************************************************************"
for fl in  "${BASE_DIR}"/*/*/PROJECT_INFO.txt; do
  cp "$fl" "$fl.bak"
  grep -v "COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS: None" "$fl" | uniq > "$fl.clean"
  mv "$fl.clean" "$fl"
done



echo
echo "Files with potential NOTES formatting problems:"
echo "*************************************************************************"
grep "^NOTE" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v -E "NOTES_[0-9]{4}-[0-9]{2}-[0-9]{2}_?[0-9]?:" | cut -d":" -f1,2

echo
echo "Creating local links to OneDrive-hosted Charter Documents for each Project:"
CHTR_BASE="https://f5.sharepoint.com/:w:/r/sites/salesandmktg/mktg/Enterprise%20Analytics/Shared%20Documents/Projects%20Folders/"
#   1-Chartering/APEX%20Test%20Log%20Analysis-All%20logs/Project%20Charter%20Template.docx
find "${BASE_DIR}" | grep "harter*.doc" 
find "${BASE_DIR}" | grep "PROJECT_INFO.txt$" 

cd -
echo "DONE"

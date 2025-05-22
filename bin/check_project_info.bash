
echo "Started at $(date)"

BASE_DIR='/Users/s.hendrickson/Documents/OneDrive - F5, Inc/Projects Folders'
cd "${BASE_DIR}"

echo
echo "Working in ${BASE_DIR}"

echo
grep "^BUSINESS_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort
echo
grep "^ANALYTICS_DS_OWNER" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort
echo
grep "^DATA_OFFICE_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | cut -d":" -f2,3 | sort | uniq -c | sort


echo
echo "Files with blank entries:"
grep -e "^BUSINESS_SPONSOR: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt 
grep -e "^ANALYTICS_DS_OWNER: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt 
grep -e "^DATA_OFFICE_SPONSOR: *$" "${BASE_DIR}"/*/*/PROJECT_INFO.txt 

echo
echo "Owners without email addresses:"
grep -e "^ANALYTICS_DS_OWNER" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v "@" | grep -v "Unassigned"
grep -e "^DATA_OFFICE_SPONSOR" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v "@" | grep -v "Unassigned"

echo
echo "Files without an owner:"
for fl in  "${BASE_DIR}"/*/*/PROJECT_INFO.txt; do
  if ! grep -e "^ANALYTICS_DS_OWNER" "$fl" > /dev/null
  then
    echo $fl
  fi
done


echo
echo "Files with NOTES formatting problems:"
grep "^NOTE" "${BASE_DIR}"/*/*/PROJECT_INFO.txt | grep -v -E "NOTES_[0-9]{4}-[0-9]{2}-[0-9]{2}_?[0-9]?:" | cut -d":" -f1,2 

echo "DONE"

# USAGE:
#
#   cd /Users/s.hendrickson/Documents/OneDrive - F5, Inc
#   python ~/Working/2023-08-23_project_visibility/bin/update_summary.py
#   cat "./Project Folders/summary.csv"
#
import os

# Locations
project_info_filename = "PROJECT_INFO.txt"
projects_tree_root = "/Users/s.hendrickson/Documents/OneDrive - F5, Inc"
projects_tree_project_folders = os.path.join(projects_tree_root, "Projects Folders")
# Files
summary_path = os.path.join(projects_tree_project_folders, "summary.csv")
data_product_links_path = os.path.join(projects_tree_project_folders, "data_product_links.md")
owner_views_active_path = os.path.join(projects_tree_project_folders, "owner_views_active.md")
owner_views_commit_path = os.path.join(projects_tree_project_folders, "owner_views_commit.md")
weekly_owner_views_active_path = os.path.join(projects_tree_project_folders, "weekly_owner_views_active.md")
owner_views_completed_path = os.path.join(projects_tree_project_folders, "owner_views_completed.md")
stakeholders_views_active_path = os.path.join(projects_tree_project_folders, "stakeholders_views_active.md")
title_phase_views_path = os.path.join(projects_tree_project_folders, "phase_views.md")
stakeholder_list_path = os.path.join(projects_tree_project_folders, "stakeholder_list.txt")

DATE_FMT = "%Y-%m-%d"
NOTES_DELIMITER = "; "

"""
These are the data elements to populate columns of the output csv for the status spreadsheet
  All-caps items are read from the project_info_file while normal case items are derived or computed.
"""
project_params_dict = {
    "Phases": None,
    "Project": None,
    "BUSINESS_SPONSOR": None,
    "ANALYTICS_DS_OWNER": None,
    "DATA_OFFICE_SPONSOR": None,
    "MISSION_ALIGNMENT": None,
    "T-SHIRT_SIZE": None,
    "Project Folder": None,
    "DATA_PRODUCT_LINK": None,
    "NOTES": None,
    "COMPUTED_AGE_DAYS": 0,
    "COMPUTED_IN_PROGRESS_AGE_DAYS": 0,
    "COMPUTED_PROJECT_START_DATE": None,
    "COMPUTED_PROJECT_IN_PROGRESS_DATE": None,
    "COMPUTED_PROJECT_END_DATE": None,
    "COMMIT_JUSTIFICATION": None
}

"""
Map columns to data elements
  One entry for each of the project_params_dict keys
  Maps to the column name in the output csv
"""
name_field_map = {
    "Phases": "Phases",
    "Project": "Project",
    "Business Sponsor": "BUSINESS_SPONSOR",
    "Analytics-DS Owner": "ANALYTICS_DS_OWNER",
    "Data Office Sponsor": "DATA_OFFICE_SPONSOR",
    "Mission Alignment": "MISSION_ALIGNMENT",
    "T-shirt Size": "T-SHIRT_SIZE",
    "Project Folder": "Project Folder",
    "Data Product Link": "DATA_PRODUCT_LINK",
    "Notes": "NOTES",
    "Age": "COMPUTED_AGE_DAYS",
    "In Progress Age": "COMPUTED_IN_PROGRESS_AGE_DAYS",
    "Project Start Date": "COMPUTED_PROJECT_START_DATE",
    "Project In-Progress Date": "COMPUTED_PROJECT_IN_PROGRESS_DATE",
    "Project End Date": "COMPUTED_PROJECT_END_DATE",
    "Commit Justification": "COMMIT_JUSTIFICATION"
}
# keep a reverse map for lookup
field_name_map = {v: k for k, v in name_field_map.items()}

# phase-dependent attributes
project_phases = {
    "0-Ideas": 0,
    "1-Chartering": 1,
    "2-Committed": 2,
    "3-In Progress": 3,
    "4-On Hold": 4,
    "5-Rollout": 5,
    "6-Completed": 6,
    "7-Maintenance": 7,
    "9-Ad Hoc": 9  # Ad Hoc projects are treated as In Progress WRT ordering and active status
}
# keep a reverse map for lookup
index_project_phases = {v: k for k, v in project_phases.items()}

# Ordering determined by Data Accelerator Analysts for Owners Reports etc.
active_projects_order = [
    "3-In Progress",
    "9-Ad Hoc",
    "4-On Hold",
    "2-Committed",
    "1-Chartering",
    "5-Rollout"
]


def order_strings_by_date(string_list):
    """
    Used for notes ordering in reports
        This works as desired if dates are yyyy-mm-dd format
    """
    res = sorted(string_list, reverse=True)
    return res

# USAGE:
#
#   cd /Users/s.hendrickson/Documents/OneDrive - F5, Inc
#   python ~/Working/2023-08-23_project_visibility/bin/update_summary.py
#   cat "./Project Folders/summary.csv"
#
import csv
import datetime
import os
from collections import defaultdict

# Locations
project_info_filename = "PROJECT_INFO.txt"
projects_tree_root = "/Users/s.hendrickson/Documents/OneDrive - F5, Inc"
projects_tree_project_folders = os.path.join(projects_tree_root, "Projects Folders")
# Files
summary_path = os.path.join(projects_tree_project_folders, "summary.csv")
data_product_links_path = os.path.join(projects_tree_project_folders, "data_product_links.md")
owner_views_active_path = os.path.join(projects_tree_project_folders, "owner_views_active.md")
weekly_owner_views_active_path = os.path.join(projects_tree_project_folders, "weekly_owner_views_active.md")
owner_views_completed_path = os.path.join(projects_tree_project_folders, "owner_views_completed.md")
stakeholders_views_active_path = os.path.join(projects_tree_project_folders, "stakeholders_views_active.md")

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
    "COMPUTED_PROJECT_START_DATE": None,
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
    "Project Start Date": "COMPUTED_PROJECT_START_DATE",
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


def extract_stakeholders(stake_str):
    """
    Stakeholders are comma-separated in the project_info_file
    Extract and return a list of stakeholders
    """
    sh_list = stake_str.split(",")
    sh_list = [x.strip() for x in sh_list]
    return sh_list


def order_strings_by_date(string_list):
    """
    Used for notes ordering in reports
        This works as desired if dates are yyyy-mm-dd format
    """
    res = sorted(string_list, reverse=True)
    return res


def parse_project_info(project_info_file):
    """
    Parse the project information file for required elements.
        Input is a file object.
        Output is a list of dictionaries
    """
    params_dict = project_params_dict.copy()
    for line in project_info_file:
        if line.startswith("#"):
            # comment lines
            continue
        fields = line.split(":")
        if fields[0].strip() in params_dict:
            # In Split on ":", so reassemble the rest of the line in case there were colons in it
            params_dict[fields[0].strip()] = ":".join(fields[1:]).strip().strip('"')
        elif fields[0].startswith("NOTE"):
            if params_dict["NOTES"] is None:
                params_dict["NOTES"] = []
            params_dict["NOTES"].append(line.strip())    # records include date field and colon
        elif fields[0].startswith("COMMIT_JUSTIFICATION"):
            if params_dict["COMMIT_JUSTIFICATION"] is None:
                params_dict["COMMIT_JUSTIFICATION"] = []
            params_dict["COMMIT_JUSTIFICATION"].append(line.strip())  # lines will be concatenated in order they appear
    # order the notes by date
    if  params_dict["NOTES"] is not None:
        params_dict["NOTES"] = order_strings_by_date(params_dict["NOTES"])
    if  params_dict["COMMIT_JUSTIFICATION"] is not None:
        # Concatenated in order they appear
        params_dict["COMMIT_JUSTIFICATION"] = " ".join(params_dict["COMMIT_JUSTIFICATION"])
    return params_dict


def extract_params(root):
    """
    Extract phase and project names for the file path.
        Assume start one directory above "Projects Folders"
    """
    names = root.split("/")    # phase, project
    assert(len(names) == 4 and names[1] == "Projects Folders")
    return names[2], names[3]


def synthesize_sharepoint_url(project_phase, project_name):
    """
    Example URL:
    
    https://f5.sharepoint.com/sites/salesandmktg/mktg/Enterprise%20Analytics/Shared%20Documents/Forms/
        AllItems.aspx?RootFolder=%2Fsites%2Fsalesandmktg%2Fmktg%2FEnterprise%20Analytics%2FShared%20Documents%2F
        Projects%20Folders%2F3%2DIn%20Progress%2FSaaS%20Customer%20Journey&
        FolderCTID=0x0120006FDE31278A0C8D49A676FC398BF8CFB9
    """
    base_sharepoint_url = (
        "https://f5.sharepoint.com/sites/salesandmktg/mktg/Enterprise%20Analytics/Shared%20Documents/"
        "Forms/AllItems.aspx?RootFolder=%2Fsites%2Fsalesandmktg%2Fmktg%2FEnterprise%20Analytics%2F"
        "Shared%20Documents%2FProjects%20Folders%2F")
    # URL encode basic path elements
    suffix = f"{project_phase}%2F{project_name}".replace(" ", "%20"
                                                         ).replace(".", "%2E").replace("-", "%2D")
    return base_sharepoint_url + suffix


def summarize_phase_counts(count_dict):
    res = "\n| Phase| # Projects|\n"
    res += "|----------------|----------|\n"
    for k, v in count_dict.items():
        res += f"|{index_project_phases[k]:10}| {v:5d}|\n"
    res += "\n\n"
    return res


def create_stakeholders_views(project_records_list):
    # find unique stakeholders
    owners = []
    for lines in project_records_list:
        owners.extend(extract_stakeholders(lines["BUSINESS_SPONSOR"]))
    owners = set(owners)

    with open(stakeholders_views_active_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Stakeholders Views - ACTIVE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(owner, project_owner_key="BUSINESS_SPONSOR"))


def create_weekly_owners_views(project_records_list):
    """
    Create output units by owner for weekly meeting update table
    """
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])
    with open(weekly_owner_views_active_path, "w") as outfile:
        outfile.write("# Data Accelerator Weekly - Project Owner Views - ACTIVE\n\n")
        outfile.write("| Projects | Info | Notes |\n")
        outfile.write("|---|---|---|\n")
        for owner in owners:
            outfile.write(f"| **{owner:}** | | |\n")
            counts = defaultdict(lambda: 0)
            for next_phase in active_projects_order:
                for lines in project_records_list:
                    _phase = lines["Phases"]
                    if lines["ANALYTICS_DS_OWNER"] == owner and _phase == next_phase:
                        counts[_phase] += 1
                        outfile.write(f'|{lines["Project"]}|[{_phase}]|\n')
                        for c, note in enumerate(lines["NOTES"].split(NOTES_DELIMITER)):
                            if c < 3:
                                outfile.write(f'| |{note.strip()[6:]}| |\n')


def synthesize_owner_block(owner, phase_filter='active', project_owner_key='ANALYTICS_DS_OWNER'):
    """
    Create output units by owner
        Skip empty blocks
    phase_filter allows reports for specific phases or the range defined in active_projects_order
    """
    ret = ""
    result = [f"## {owner:}\n\n"]
    counts = defaultdict(lambda: 0)

    if isinstance(phase_filter, list):
        if isinstance(phase_filter[0], int):
            # phase_filter is a list of phase numbers
            phases_order = phase_filter
        else:
            # convert phase names to sequence numbers
            phases_order = [project_phases[x] for x in phase_filter]
    elif phase_filter.lower() == "active":
        # convert phase names to sequence numbers
        phases_order = [project_phases[x] for x in active_projects_order]
    else:
        return "ERROR: Invalid phase_filter"

    for next_phase in phases_order:
        for lines in project_records_list:
            # step through the project list to find owners and active projects of the ordered type
            _current_project_phase = project_phases[lines["Phases"]]   # convert phase name to sequence number
            if owner in lines[project_owner_key] and _current_project_phase == next_phase:
                counts[_current_project_phase] += 1
                result.append(f'### {lines["Project"]} | *Mission: {lines["MISSION_ALIGNMENT"]}*\n\n')
                result.append( f'Project currently in phase _[{lines["Phases"]}]_ ')
                result.append(f'has been active for {lines["COMPUTED_AGE_DAYS"]} days\n\n')
                result.append(f'Project sponsor(s): {lines["BUSINESS_SPONSOR"]}\n\n')
                for note in lines["NOTES"].split(NOTES_DELIMITER):
                    result.append(f'  - {note.strip()[6:]}\n')
    if len(counts) > 0:
        # Only include this block if 1 or more projects found
        result.append(summarize_phase_counts(counts))
        ret = "".join(result)
    return ret


def create_owners_views(project_records_list):
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])

    with open(owner_views_active_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - ACTIVE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(owner))

    with open(owner_views_completed_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - COMPLETED & MAINTENANCE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(owner, phase_filter=["6-Completed", "7-Maintenance"]))


def create_data_product_links(project_records_list):
    """
    Markdown data project links page
    """
    prototype = "- [{}]({}) {}\n"
    links = []
    for line_dict in project_records_list:
        if line_dict["DATA_PRODUCT_LINK"] is not None and not line_dict["DATA_PRODUCT_LINK"].startswith("None") and \
                line_dict["DATA_PRODUCT_LINK"].strip() != "":
            links.append(prototype.format(line_dict["Project"], line_dict["DATA_PRODUCT_LINK"], line_dict["Phases"]))
    if len(links) > 0:
        with open(data_product_links_path, "w") as outfile:
            outfile.write("### Dashboard Links:\n\n")
            for link in links:
                outfile.write(link)


def create_summary_csv(project_records_list):
    """
    Create the summary csv file of all the projects in the tree
    """
    with open(summary_path, "w") as outfile:
        # Table header
        w = csv.DictWriter(outfile, project_params_dict.keys(), dialect='excel')
        w.writerow(field_name_map)
        # Write the project data, 1 project per line
        for line in project_records_list:
            w.writerow(line)


if __name__ == "__main__":
    os.chdir(projects_tree_root)
    project_records_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
        if dirs != [] or project_info_filename not in files:
            continue
        new_project_start_date = None
        new_project_end_date = None
        # Process Project Info file
        with open(os.path.join(root, project_info_filename), "r") as project_info_file:
            projects_processed_counter += 1
            phase, project = extract_params(root)  # harvest parameters from path
            params = parse_project_info(project_info_file)
            params["Phases"] = phase
            params["Project"] = project

            print(f"Processing file {projects_processed_counter} ({phase}: {project})")

            params["Project Folder"] = synthesize_sharepoint_url(phase, project)
            params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"])

            project_end_date = datetime.datetime.now()  # current last day of unfinished projects
            if project_phases[phase] >= 6:
                # Completed projects
                if params["COMPUTED_PROJECT_END_DATE"] is None:
                    # First time we processed file since project phase changed to completed
                    project_end_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_END_DATE"] = project_end_date.strftime(DATE_FMT)
                    new_project_end_date = project_end_date
                else:
                    project_end_date = datetime.datetime.strptime(params["COMPUTED_PROJECT_END_DATE"][:10], DATE_FMT)

            if project_phases[phase] >= 2:
                # Active projects
                if params["COMPUTED_PROJECT_START_DATE"] is None:
                    # First time we processed file since project phase changed to active
                    project_start_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_START_DATE"] = project_start_date.strftime(DATE_FMT)
                    new_project_start_date = project_start_date
                else:
                    project_start_date = datetime.datetime.strptime(params["COMPUTED_PROJECT_START_DATE"][:10],
                                                                    DATE_FMT)
                    dt_delta = project_end_date - project_start_date
                    params["COMPUTED_AGE_DAYS"] = dt_delta.days

            project_records_list.append(params)

        if new_project_start_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_START_DATE: {project_start_date.strftime(DATE_FMT)}\n')

        if new_project_end_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_END_DATE: {project_end_date.strftime(DATE_FMT)}\n')

    # Create reports
    create_summary_csv(project_records_list)
    create_data_product_links(project_records_list)
    create_owners_views(project_records_list)
    create_weekly_owners_views(project_records_list)
    create_stakeholders_views(project_records_list)

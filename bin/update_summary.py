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
owner_views_commit_path = os.path.join(projects_tree_project_folders, "owner_views_commit.md")
weekly_owner_views_active_path = os.path.join(projects_tree_project_folders, "weekly_owner_views_active.md")
owner_views_completed_path = os.path.join(projects_tree_project_folders, "owner_views_completed.md")
stakeholders_views_active_path = os.path.join(projects_tree_project_folders, "stakeholders_views_active.md")
title_phase_views_path = os.path.join(projects_tree_project_folders, "phase_views.md")

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
            params_dict["NOTES"].append(line.strip())  # records include date field and colon
        elif fields[0].startswith("COMMIT_JUSTIFICATION"):
            if params_dict["COMMIT_JUSTIFICATION"] is None:
                params_dict["COMMIT_JUSTIFICATION"] = []
            params_dict["COMMIT_JUSTIFICATION"].append(
                line.split(":")[1].strip())  # lines will be concatenated in order they appear
    # order the notes by date
    if params_dict["NOTES"] is not None:
        params_dict["NOTES"] = order_strings_by_date(params_dict["NOTES"])

    return params_dict


def extract_params(root):
    """
    Extract phase and project names for the file path.
        Assume start one directory above "Projects Folders"
    """
    names = root.split("/")  # phase, project
    assert (len(names) == 4 and names[1] == "Projects Folders")
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


def summarize_phase_counts(phase_counts):
    """
    Generate a markdown formatted summary table of project phases and their counts.

    Parameters:
    phase_counts (dict): A dictionary where keys are phase identifiers (ints) and 
                         values are the counts of projects in each phase.

    Returns:
    str: A string representing a markdown formatted table summarizing the phase counts.
    """
    # Initialize the markdown table header
    markdown_table = "\n| Phase | # Projects |\n"
    markdown_table += "|----|----|\n"

    # Iterate over each phase and its count, adding rows to the table
    for phase_id, project_count in phase_counts.items():
        phase_name = index_project_phases[phase_id]  # Retrieve phase name from the global variable
        markdown_table += f"| {phase_name:10} | {project_count:5d} |\n"

    markdown_table += "\n\n"  # Add extra newlines for readability
    return markdown_table


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


def create_title_phase_views(project_records_list):
    """
    Create output units by phase for throughput and backlog overview
    """
    with open(title_phase_views_path, "w") as outfile:
        outfile.write("# Data Accerator Projects by Phase\n\n")
        counts = defaultdict(lambda: 0)
        for _phase, index in project_phases.items():
            if index in [0, 9]:
                continue
            outfile.write(f'### {_phase.split("-")[1]}\n\n')
            outfile.write('| <div style="width:450px">Projects</div> |\n')
            outfile.write("|---|\n")
            for lines in project_records_list:
                if _phase == lines["Phases"]:
                    counts[index] += 1
                    outfile.write(f'|{lines["Project"]} (👕:{size_repr(lines["T-SHIRT_SIZE"])})|\n')
        if len(counts) > 0:
            # Only include this block if 1 or more projects found
            outfile.write(summarize_phase_counts(counts))


def create_weekly_owners_views(project_records_list):
    """
    Create output units by owner for weekly meeting update table
    """
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])
    with open(weekly_owner_views_active_path, "w") as outfile:
        outfile.write("# DA Weekly - Project Owner Views - ACTIVE\n\n")
        outfile.write("| Projects | Info |\n")
        outfile.write("|---|---|\n")
        for owner in owners:
            outfile.write(f"| **{owner:}** | | |\n")
            counts = defaultdict(lambda: 0)
            for next_phase in active_projects_order:
                for lines in project_records_list:
                    _phase = lines["Phases"]
                    if lines["ANALYTICS_DS_OWNER"] == owner and _phase == next_phase:
                        counts[_phase] += 1
                        outfile.write(f'|{lines["Project"]}|[{_phase}] active {lines["COMPUTED_AGE_DAYS"]} days &'
                                      f' In-progress {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days '
                                      f' (👕:{size_repr(lines["T-SHIRT_SIZE"])})|\n')
                        for c, note in enumerate(lines["NOTES"].split(NOTES_DELIMITER)):
                            if c < 3:
                                outfile.write(f'| |{note.strip()[6:]}| |\n')


def size_repr(size_string):
    """
    Convert a size string to a standardized size representation.

    Parameters:
    size_string (str): A string representing the size, which can be "small", "medium", 
                       "large", "extra large", etc., or their abbreviations.

    Returns:
    str: A standardized one-letter size representation ("S", "M", "L", "XL"). 
         Returns "Unsized" if the input does not match any recognized size.
    """
    # Trim and convert the input to lower case for standardization
    standardized_size = size_string.strip().lower()

    # Determine the size representation based on the first character
    if standardized_size.startswith("s"):
        return "S"
    elif standardized_size.startswith("m"):
        return "M"
    elif standardized_size.startswith("l"):
        return "L"
    elif standardized_size.startswith("x") or standardized_size.startswith("e"):
        return "XL"

    # Default return value for unrecognized sizes
    return "Unsized"


def synthesize_owner_block(owner, phase_filter='active', project_owner_key='ANALYTICS_DS_OWNER',
                           justification_block=False):
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
            _current_project_phase = project_phases[lines["Phases"]]  # convert phase name to sequence number
            if owner in lines[project_owner_key] and _current_project_phase == next_phase:
                counts[_current_project_phase] += 1
                result.append(f'### {lines["Project"]}<br>*Mission: {lines["MISSION_ALIGNMENT"]}*\n\n')
                result.append(f'<u>Project phase</u>: _{lines["Phases"]}_ ')
                result.append(f'&nbsp; &nbsp; &nbsp; 📆 Active for {lines["COMPUTED_AGE_DAYS"]} days &'
                              f' In-Progress for {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days\n\n')
                result.append(f'<u>Project sponsor(s)</u>: {lines["BUSINESS_SPONSOR"]} ')
                result.append(f'&nbsp; &nbsp; &nbsp;  👕 <u>Size</u>: {size_repr(lines["T-SHIRT_SIZE"])} \n\n')
                if project_owner_key != "ANALYTICS_DS_OWNER":
                    result.append(f'<u>Data Analyst</u>: {lines["ANALYTICS_DS_OWNER"]}\n\n')
                for note in lines["NOTES"].split(NOTES_DELIMITER):
                    result.append(f'  - {note.strip()[6:]}\n')
                result.append("\n\n")
                if justification_block and lines["COMMIT_JUSTIFICATION"] is not None:
                    result.append(f'#### Case for Commit \n{lines["COMMIT_JUSTIFICATION"]}\n\n')
    if len(counts) > 0:
        # Only include this block if 1 or more projects found
        result.append(summarize_phase_counts(counts))
        ret = "".join(result)
    return ret


def create_owners_commit_views(project_records):
    """
    Creates a file with synthesized owner blocks for each unique project owner.

    This function finds unique owners in the provided project records and writes
    synthesized information for each owner to a file. The information includes
    project phases and justifications.

    Parameters:
    project_records (list of dict): A list of dictionaries, each representing a project record.
    """
    # Extracting unique owners
    unique_owners = {record["ANALYTICS_DS_OWNER"] for record in project_records}

    # Open the file for writing
    with open(owner_views_commit_path, "w") as outfile:
        # Write the header
        outfile.write("# Data Accelerator - Project Owner Views - COMMIT\n\n")
        # Timestamp
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outfile.write(f"({current_timestamp})\n\n")

        # Write synthesized owner blocks
        for owner in unique_owners:
            owner_block = synthesize_owner_block(owner, phase_filter=["2-Committed", "1-Chartering"],
                                                 justification_block=True)
            outfile.write(owner_block)


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


def create_data_product_links(project_records):
    """
    Writes markdown links for data products to a file, based on provided project records.

    Each project record in the input list should be a dictionary containing keys:
    'Project', 'DATA_PRODUCT_LINK', and 'Phases'. The markdown links are created only 
    for records with valid 'DATA_PRODUCT_LINK'.

    Parameters:
    project_records (list of dict): A list of dictionaries, each representing a project record.
    """
    markdown_link_template = "- [{}]({}) {}\n"
    markdown_links = []

    # Filtering and formatting links
    for record in project_records:
        data_product_link = record["DATA_PRODUCT_LINK"]
        if data_product_link and not data_product_link.lower().startswith("none") and data_product_link.strip():
            formatted_link = markdown_link_template.format(record["Project"], data_product_link, record["Phases"])
            markdown_links.append(formatted_link)

    # Writing to file if there are links to write
    if markdown_links:
        with open(data_product_links_path, "w") as outfile:
            outfile.write("### Dashboard Links:\n\n")
            outfile.writelines(markdown_links)


def create_summary_csv(project_records):
    """
    Writes a summary CSV file containing data for each project.

    The CSV file includes headers as specified by 'project_params_dict.keys()' and
    maps field names using 'field_name_map'. Each project record in 'project_records'
    is written as a row in the CSV file.

    Parameters:
    project_records (list of dict): A list of dictionaries, each representing a project record.
    """
    # Open the file for writing
    with open(summary_path, "w", newline='') as outfile:
        # Initialize a CSV DictWriter with the specified field names and dialect
        csv_writer = csv.DictWriter(outfile, fieldnames=project_params_dict.keys(), dialect='excel')

        # Write the header row based on field_name_map
        csv_writer.writeheader()

        # Write each project record as a row in the CSV file
        csv_writer.writerows(project_records)


if __name__ == "__main__":
    os.chdir(projects_tree_root)
    project_records_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
        # if dirs != [] or project_info_filename not in files:
        if project_info_filename not in files:
            continue
        new_project_start_date = None
        new_project_end_date = None
        new_project_in_progress_date = None
        # Process Project Info file
        with open(os.path.join(root, project_info_filename), "r") as project_info_file:
            projects_processed_counter += 1
            phase, project = extract_params(root)  # harvest parameters from path
            params = parse_project_info(project_info_file)
            params["Phases"] = phase
            params["Project"] = project

            print(f"Processing file {projects_processed_counter} ({phase}: {project})")

            params["Project Folder"] = synthesize_sharepoint_url(phase, project)
            params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"]) + "\n\n"
            if isinstance(params["COMMIT_JUSTIFICATION"], list) and len(params["COMMIT_JUSTIFICATION"]) > 0:
                # Concatenated in order they appear
                params["COMMIT_JUSTIFICATION"] = " ".join(params["COMMIT_JUSTIFICATION"]) + "\n\n"
            else:
                params["COMMIT_JUSTIFICATION"] = "Commit justification required!\n\n"

            # Compute derived values for timing of phases
            project_end_date = datetime.datetime.now()  # current last day of unfinished projects
            if project_phases[phase] >= 6:
                # Completed projects
                if params["COMPUTED_PROJECT_END_DATE"] is None:
                    # First time we processed file since project phase changed to completed
                    project_end_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_END_DATE"] = project_end_date.strftime(DATE_FMT)
                    new_project_end_date = project_end_date
                else:
                    project_end_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_END_DATE"][:10],
                        DATE_FMT)

            if project_phases[phase] >= 3:
                # In Progress projects
                if params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] is None:
                    # First time we processed file since project phase changed to In Progress
                    project_in_progress_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] = project_in_progress_date.strftime(DATE_FMT)
                    new_project_in_progress_date = project_in_progress_date
                else:
                    project_in_progress_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_IN_PROGRESS_DATE"][:10],
                        DATE_FMT)
                    dt_delta = project_end_date - project_in_progress_date
                    params["COMPUTED_IN_PROGRESS_AGE_DAYS"] = dt_delta.days

            if project_phases[phase] >= 1:
                # Chartering - Active projects
                if params["COMPUTED_PROJECT_START_DATE"] is None:
                    # First time we processed file since project phase changed to active
                    project_start_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_START_DATE"] = project_start_date.strftime(DATE_FMT)
                    new_project_start_date = project_start_date
                else:
                    project_start_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_START_DATE"][:10],
                        DATE_FMT)
                    dt_delta = project_end_date - project_start_date
                    params["COMPUTED_AGE_DAYS"] = dt_delta.days

            project_records_list.append(params)

        # Update the project info file with time values for phase transitions
        if new_project_start_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_START_DATE: {new_project_start_date.strftime(DATE_FMT)}\n')

        if new_project_in_progress_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_PROJECT_IN_PROGRESS_DATE: {new_project_in_progress_date.strftime(DATE_FMT)}\n')

        if new_project_end_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_END_DATE: {new_project_end_date.strftime(DATE_FMT)}\n')

    # Create reports
    create_summary_csv(project_records_list)
    create_data_product_links(project_records_list)
    create_owners_views(project_records_list)
    create_owners_commit_views(project_records_list)
    create_weekly_owners_views(project_records_list)
    create_stakeholders_views(project_records_list)
    create_title_phase_views(project_records_list)

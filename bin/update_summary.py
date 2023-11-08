# USAGE:
#
#   cd /Users/s.hendrickson/Documents/OneDrive - F5, Inc
#   python ~/Working/2023-08-23_project_visibility/bin/update_summary.py
#   cat "./Project Folders/summary.csv"
#
import sys
import csv
import os
import datetime
from collections import defaultdict

project_info_filename = "PROJECT_INFO.txt"
projects_tree_root = "/Users/s.hendrickson/Documents/OneDrive - F5, Inc"
project_summary_path = "./Projects Folders/summary.csv"
data_product_links_path = "./Projects Folders/data_product_links.md"
owner_views_path = "./Projects Folders/owner_views_active.md"
weekly_owner_views_path = "./Projects Folders/weekly_owner_views_active.md"
owner_views_completed_path = "./Projects Folders/owner_views_completed.md"
stakeholders_views_path = "./Projects Folders/stakeholders_views.md"


DATE_FMT = "%Y-%m-%d"
NOTES_DELIMITER = "; "

#
# These are the data elements to populate columns of the output csv for the status spreadsheet
#
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
    "COMPUTED_PROJECT_END_DATE": None
}

#
# Map columns to data elements
#
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
    "Project End Date": "COMPUTED_PROJECT_END_DATE"
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
        "9-Ad Hoc": 3
        }

active_projects_order = [
        "3-In Progress",
        "4-On Hold",
        "2-Committed",
        "1-Chartering",
        "5-Rollout"
        ]

def extract_stakeholders(stake_str):
    sh = stake_str.split(",")
    sh = [x.strip() for x in sh]
    return sh


def order_strings_by_date(string_list):
    # This works if dates are yyyy-mm-dd format
    # Maybe parse dates later?
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
            params_dict[fields[0].strip()] = ":".join(fields[1:]).strip().strip('"')
        elif fields[0].startswith("NOTE"):
            if params_dict["NOTES"] is None:
                params_dict["NOTES"] = []
            params_dict["NOTES"].append(line.strip())
    # order the notes by date
    params_dict["NOTES"] = order_strings_by_date(params_dict["NOTES"])

    return params_dict


def extract_params(root):
    """
    Extract phase and project names for the file path.
    """
    names = root.split("/")
    return names[2], names[3]


def make_sharepoint_url(project_phase, project_name):
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


def create_summary_csv(outlines):
    with open(project_summary_path, "w") as outfile:
        # Table header
        w = csv.DictWriter(outfile, project_params_dict.keys(), dialect='excel')
        w.writerow(field_name_map)
        # Project data
        for line in out_lines:
            w.writerow(line)


def create_data_product_links(out_lines):
    prototype = "- [{}]({}) {}\n"
    links = []
    for line_dict in out_lines:
        if line_dict["DATA_PRODUCT_LINK"] is not None and not line_dict["DATA_PRODUCT_LINK"].startswith("None") and line_dict["DATA_PRODUCT_LINK"].strip() != "" :
            links.append(prototype.format(line_dict["Project"], line_dict["DATA_PRODUCT_LINK"], line_dict["Phases"]))
    if len(links) > 0:
        with open(data_product_links_path, "w") as outfile:
            outfile.write("### Dashboard Links:\n\n")
            for link in links:
                outfile.write(link)

def owner_summary(count_dict):
    res = "\n| Phase| # Projects|\n"
    res += "|----------------|----------|\n"
    for k,v in count_dict.items():
        res += f"|{k:10}| {v:5d}|\n"
    res += "\n\n"
    return res


def create_stakeholders_views(out_lines):
    # find unique stakeholders
    owners = []
    for lines in out_lines:
        owners.extend(extract_stakeholders(lines["BUSINESS_SPONSOR"]))
    owners = set(owners)

    with open(stakeholders_views_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Stakeholders Views - ACTIVE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(f"## {owner:}\n\n")
            counts = defaultdict(lambda: 0)
            for order in active_projects_order:
                for lines in out_lines:
                    _phase = lines["Phases"]
                    if owner in lines["BUSINESS_SPONSOR"] and  _phase == order:
                        counts[_phase] += 1
                        outfile.write(f'<div tag="{owner}"><div>\n\n')
                        outfile.write(f'### {lines["Project"]} | *Mission: {lines["MISSION_ALIGNMENT"]}* [{_phase}]\n\n')
                        outfile.write(f'  _Data Office Owner:_ {lines["ANALYTICS_DS_OWNER"]} [{lines["COMPUTED_AGE_DAYS"]} days]\n\n')
                        outfile.write(f'  _Project Sponsors:_ {lines["BUSINESS_SPONSOR"]}\n\n')
                        for note in lines["NOTES"].split(NOTES_DELIMITER):
                            outfile.write(f'  - {note.strip()[6:]}\n')
            outfile.write(owner_summary(counts))


def create_weekly_owner_views(out_lines):
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in out_lines])
    with open(weekly_owner_views_path, "w") as outfile:
        outfile.write("# Data Accelerator Weekly - Project Owner Views - ACTIVE\n\n")
        outfile.write("| Projects | Info | Notes |\n")
        outfile.write("|---|---|---|\n")
        for owner in owners:
            outfile.write(f"| **{owner:}** | | |\n")
            counts = defaultdict(lambda: 0)
            for order in active_projects_order:
                for lines in out_lines:
                    _phase = lines["Phases"]
                    if lines["ANALYTICS_DS_OWNER"] == owner and  _phase == order:
                        counts[_phase] += 1
                        outfile.write(f'|{lines["Project"]}|[{_phase}]|\n')
                        for c, note in enumerate(lines["NOTES"].split(NOTES_DELIMITER)):
                            if c < 3:
                                outfile.write(f'| |{note.strip()[6:]}| |\n')
            


def create_analytics_ds_owner_views(out_lines):
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in out_lines])
    with open(owner_views_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - ACTIVE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(f"## {owner:}\n\n")
            counts = defaultdict(lambda: 0)
            for order in active_projects_order:
                for lines in out_lines:
                    _phase = lines["Phases"]
                    if lines["ANALYTICS_DS_OWNER"] == owner and  _phase == order:
                        counts[_phase] += 1
                        outfile.write(f'### {lines["Project"]} | *Mission: {lines["MISSION_ALIGNMENT"]}* [{_phase}]\n\n')
                        outfile.write(f'  {lines["BUSINESS_SPONSOR"]} [{lines["COMPUTED_AGE_DAYS"]} days]\n\n')
                        for note in lines["NOTES"].split(NOTES_DELIMITER):
                            outfile.write(f'  - {note.strip()[6:]}\n')
            outfile.write(owner_summary(counts))

    with open(owner_views_completed_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - COMPLETED & MAINTENANCE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(f"## {owner:}\n\n")
            for lines in out_lines:
                if lines["ANALYTICS_DS_OWNER"] == owner and  5 < project_phases[lines["Phases"]] < 8:
                    outfile.write(f'### {lines["Project"]} | *Mission: {lines["MISSION_ALIGNMENT"]}* [{lines["Phases"]}]\n\n')
                    outfile.write(f'  {lines["BUSINESS_SPONSOR"]} [{lines["COMPUTED_AGE_DAYS"]} days]\n\n')
                    for note in lines["NOTES"].split(NOTES_DELIMITER):
                        outfile.write(f'  - {note.strip()[6:]}\n')

##### Main #####
os.chdir(projects_tree_root)
out_lines = []
counter = 0

# Walk the file system from the root directory
for root, dirs, files in os.walk(".", topdown=False):
    # print("root=", root, "dirs=", dirs, "files=", files)
    if dirs != [] or project_info_filename not in files:
        continue
    new_project_start_date = None
    new_project_end_date = None
    with open(os.path.join(root, project_info_filename), "r") as pi:
        counter += 1
        phase, project = extract_params(root)
        params = parse_project_info(pi)
        params["Phases"] = phase
        params["Project"] = project
        print(f"Processing file {counter} ({phase}: {project})")

        params["Project Folder"] = make_sharepoint_url(phase, project)
        params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"])

        project_end_date =  datetime.datetime.now()  # current last day of unfinished projects
        if project_phases[phase] >= 6:
            if params["COMPUTED_PROJECT_END_DATE"] is None:
                project_end_date = datetime.datetime.now()
                params["COMPUTED_PROJECT_END_DATE"] = project_end_date.strftime(DATE_FMT)
                new_project_end_date = project_end_date
            else:
                proect_end_date = datetime.datetime.strptime(params["COMPUTED_PROJECT_END_DATE"][:10], DATE_FMT)

        if project_phases[phase] >= 1:
            if params["COMPUTED_PROJECT_START_DATE"] is None:
                project_start_date = datetime.datetime.now()
                params["COMPUTED_PROJECT_START_DATE"] = project_start_date.strftime(DATE_FMT)
                new_project_start_date = project_start_date
            else:
                project_start_date = datetime.datetime.strptime(params["COMPUTED_PROJECT_START_DATE"][:10], DATE_FMT)
                dt_delta = project_end_date - project_start_date
                params["COMPUTED_AGE_DAYS"] = dt_delta.days
        
        out_lines.append(params)

    if new_project_start_date is not None:
        with open(os.path.join(root, project_info_filename), "a") as pi:
            pi.write(f'COMPUTED_PROJECT_START_DATE: {project_start_date.strftime(DATE_FMT)}\n')

    if new_project_end_date is not None:
        with open(os.path.join(root, project_info_filename), "a") as pi:
            pi.write(f'COMPUTED_PROJECT_END_DATE: {project_end_date.strftime(DATE_FMT)}\n')

create_summary_csv(out_lines)
create_data_product_links(out_lines)
create_analytics_ds_owner_views(out_lines)
create_weekly_owner_views(out_lines)
create_stakeholders_views(out_lines)

import csv
import datetime
from collections import defaultdict

from reports.configurations import *

########################################################################################
# Utilities
########################################################################################

def extract_stakeholders(stake_str):
    """
    Stakeholders are comma-separated in the project_info_file
    Extract and return a list of stakeholders
    """
    sh_list = stake_str.split(",")
    sh_list = [x.strip() for x in sh_list]
    return sh_list


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

def synthesize_email(name_set):
    result = []
    for x in name_set:
        v = x.strip().replace("- V", "")
        try:
            a, b = v.split(" ")
            result.append([f"{v}", f"{a[0].lower()}.{b.lower()}@f5.com"])
        except ValueError:
            pass
    return result


########################################################################################
# Reusable report components
########################################################################################
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


def synthesize_owner_block(project_records_list, owner, phase_filter='active', project_owner_key='ANALYTICS_DS_OWNER',
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
                if justification_block and lines["COMMIT_JUSTIFICATIONS"] is not None:
                    result.append(f'#### Case for Commit \n{lines["COMMIT_JUSTIFICATIONS"]}\n\n')
    if len(counts) > 0:
        # Only include this block if 1 or more projects found
        result.append(summarize_phase_counts(counts))
        ret = "".join(result)
    return ret

########################################################################################
# Reports
########################################################################################
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
            outfile.write(synthesize_owner_block(project_records_list, owner, project_owner_key="BUSINESS_SPONSOR"))


def create_title_phase_views(project_records_list):
    """
    Create output units by phase for throughput and backlog overview
    """
    with open(title_phase_views_path, "w") as outfile:
        outfile.write("# Data Accelerator Projects by Phase\n\n")
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




def create_owners_commit_views(project_records_list):
    """
    Creates a file with synthesized owner blocks for each unique project owner.

    This function finds unique owners in the provided project records and writes
    synthesized information for each owner to a file. The information includes
    project phases and justifications.

    Parameters:
    project_records (list of dict): A list of dictionaries, each representing a project record.
    """
    # Extracting unique owners
    unique_owners = {record["ANALYTICS_DS_OWNER"] for record in project_records_list}

    # Open the file for writing
    with open(owner_views_commit_path, "w") as outfile:
        # Write the header
        outfile.write("# Data Accelerator - Project Owner Views - COMMIT\n\n")
        # Timestamp
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outfile.write(f"({current_timestamp})\n\n")

        # Write synthesized owner blocks
        for owner in unique_owners:
            owner_block = synthesize_owner_block(project_records_list, owner,
                                                 phase_filter=["2-Committed", "1-Chartering"],
                                                 justification_block=True)
            outfile.write(owner_block)


def create_owners_views(project_records_list):
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])

    with open(owner_views_active_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - ACTIVE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(project_records_list, owner))

    with open(owner_views_completed_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - COMPLETED & MAINTENANCE\n\n")
        outfile.write(f"({str(datetime.datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(
                synthesize_owner_block(project_records_list, owner, phase_filter=["6-Completed", "7-Maintenance"]))


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



def create_complete_stakeholder_list(project_records):
    """
    Creates a list of stakeholders from the provided project records.

    Parameters:
    project_records (list of dict): A list of dictionaries, each representing a project record.

    Returns:
    list of str: A list of unique stakeholders.
    """
    stakeholders = set()

    # Iterate over each project record and extract the stakeholders
    for record in project_records:
        stakeholders.update(extract_stakeholders(record["BUSINESS_SPONSOR"]))

    stakeholderlist = synthesize_email(stakeholders)

    # Return the list of unique stakeholders
    with open(stakeholder_list_path, "w") as outfile:
        wrt = csv.writer(outfile)
        wrt.writerows(stakeholderlist)

def create_reports(project_records_list):
    # Create all the standard reports
    create_summary_csv(project_records_list)
    create_data_product_links(project_records_list)
    create_owners_views(project_records_list)
    create_owners_commit_views(project_records_list)
    create_weekly_owners_views(project_records_list)
    create_stakeholders_views(project_records_list)
    create_title_phase_views(project_records_list)
    create_complete_stakeholder_list(project_records_list)

import csv
import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd

# Import Project Module(s) Below
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


def recent_notes(notes_text, recent_days=400, limit=200):
    """
    Return a list of notes with the most recent first
    """
    notes = [x.strip()[6:] for x in notes_text.split(NOTES_DELIMITER)]
    # check for recent notes
    recent = datetime.now() - timedelta(days=recent_days)
    notes_list = []
    for count, note in enumerate(notes):
        if count < limit:
            update_note = note
            if note.endswith("::"):
                # notes with sequence within a date. Make bulleted list.
                pre, sequence_number, post = note.split("::")
                update_note = f"  {int(sequence_number)}. {pre[11:]}"
            if datetime.strptime(note[:10].replace("_", "-"), DATE_FMT) >= recent:
                notes_list.append(update_note)
    return notes_list


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
    logging.info(f"Synthesize Owner Block: project_owner_key={project_owner_key} owner={owner}")

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
        logging.error("ERROR: Invalid phase_filter")
        return "ERROR: Invalid phase_filter"

    for next_phase in phases_order:
        for lines in project_records_list:
            # step through the project list to find owners and active projects of the ordered type
            _current_project_phase = project_phases[lines["Phases"]]  # convert phase name to sequence number
            if owner in lines[project_owner_key] and _current_project_phase == next_phase:
                logging.info(f"Processing {lines['Project']} in Phase {next_phase} for {owner}")
                counts[_current_project_phase] += 1
                result.append(f'### {lines["Project"]}<br>*Mission: {lines["MISSION_ALIGNMENT"]}*\n\n')
                result.append(f'<u>Project phase</u>: _{lines["Phases"]}_ ')
                result.append(f'&nbsp; &nbsp; &nbsp; 📆 Active for {lines["COMPUTED_AGE_DAYS"]} days &'
                              f' In-Progress for {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days\n\n')
                result.append(f'<u>Project sponsor(s)</u>: {lines["BUSINESS_SPONSOR"]} ')
                result.append(f'&nbsp; &nbsp; &nbsp;  👕 <u>Size</u>: {size_repr(lines["T-SHIRT_SIZE"])} \n\n')
                if project_owner_key != "ANALYTICS_DS_OWNER":
                    result.append(f'<u>Data Analyst</u>: {lines["ANALYTICS_DS_OWNER"]}\n\n')
                notes_block = "\n\n".join(recent_notes(lines["NOTES"]))
                result.extend(notes_block)
                result.append("\n\n")
                if justification_block and lines["COMMIT_JUSTIFICATIONS"] is not None:
                    result.append(f'#### Case for Commit \n{lines["COMMIT_JUSTIFICATIONS"]}\n\n')
    if len(counts) > 0:
        # Only include this block if 1 or more projects found
        result.append(summarize_phase_counts(counts))
        ret = "".join(result)
    return ret


def synthesize_owner_maintenance_block(project_records_list, owner, project_owner_key='ANALYTICS_DS_OWNER'):
    """
    Create output units by owner
        Include items with only recent notes or triggers for maintenance
    """
    ret = ""
    result = [f"### Maintenance Projects\n\n"]
    counts = defaultdict(lambda: 0)
    for lines in project_records_list:
        # step through the project list to find owners and active projects of the ordered type
        _current_project_phase = project_phases[lines["Phases"]]  # convert phase name to sequence number
        if _current_project_phase == 7 and owner in lines[project_owner_key]:
            recent = recent_notes(lines["NOTES"], 14)
            if len(recent) > 0:
                logging.info(f"Processing recent notes for {lines['Project']} in Phase 7 for {owner}")
                counts[_current_project_phase] += 1
                result.append(f'### {lines["Project"]}\n\n')
                result.append(f'<u>Project sponsor(s)</u>: {lines["BUSINESS_SPONSOR"]}\n\n')
                if project_owner_key != "ANALYTICS_DS_OWNER":
                    result.append(f'<u>Data Analyst</u>: {lines["ANALYTICS_DS_OWNER"]}\n\n')
                for note in recent:
                    result.append(f'{note}\n\n')
            result.append("\n\n")
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
        outfile.write(f"({str(datetime.now())[:19]})\n\n")
        for owner in owners:
            block_string = synthesize_owner_block(project_records_list, owner, project_owner_key="BUSINESS_SPONSOR")
            if block_string:
                outfile.write(block_string)


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

    This is an HTML document to take advantage of full table formatting control.
    """
    # Timestamp
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # find unique owners
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])
    with open(weekly_owner_views_active_path, "w") as outfile:
        outfile.write(CSS_STYLE)
        outfile.write("<h1>DA Weekly - Project Owner Views - ACTIVE</h1>\n\n")
        outfile.write('<table border=0.1>\n')
        outfile.write(f"<tr><th>Projects</th><th>Info <span>(updated: {current_timestamp})</span></th></tr>\n")
        for owner in owners:
            owner_header = False;
            counts = defaultdict(lambda: 0)
            for next_phase in active_projects_order:
                for lines in project_records_list:
                    _phase = lines["Phases"]
                    if lines["ANALYTICS_DS_OWNER"] == owner and _phase == next_phase:
                        if not owner_header:
                            owner_header = True
                            outfile.write(f'<tr class="tr-owner"><td colspan=2><b>{owner:}</b></td></tr>\n')
                        counts[_phase] += 1
                        outfile.write(f'<tr class="tr-project"><td>{lines["Project"]}</td>'
                                      f'<td>[{_phase}] active {lines["COMPUTED_AGE_DAYS"]} days &'
                                      f' In-progress {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days '
                                      f' (👕:{size_repr(lines["T-SHIRT_SIZE"])})</td></tr>\n')
                        notes_block = recent_notes(lines["NOTES"], limit=4)
                        for note in notes_block:
                            note = note.strip().replace("|", ":")
                            outfile.write(f'<tr><td></td><td>{note}</td></tr>\n')
        outfile.write('</table>')
        outfile.write(HTML_FOOTER)


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
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        outfile.write(f"({str(datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(project_records_list, owner))
            outfile.write(synthesize_owner_maintenance_block(project_records_list, owner))

    with open(owner_views_completed_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - COMPLETED & MAINTENANCE\n\n")
        outfile.write(f"({str(datetime.now())[:19]})\n\n")
        for owner in owners:
            outfile.write(
                synthesize_owner_block(project_records_list, owner,
                                       phase_filter=["6-Completed", "7-Maintenance"]))


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
        logging.info(f'project_params_dict.keys(): {project_params_dict.keys()}')
        csv_writer = csv.DictWriter(outfile, fieldnames=project_params_dict.keys(), dialect='excel')

        # Write the header row based on field_name_map
        csv_writer.writeheader()

        # Write each project record as a row in the CSV file
        csv_writer.writerows(project_records)


def create_analytics_summary_csv(project_records):
    df_proj_records = pd.DataFrame(project_records, columns=project_params_dict.keys())
    df_proj_records = df_proj_records.drop(['NOTES', 'CharterLink'], axis=1)
    df_proj_records.to_csv(analytics_summary_path, index=False)
#     """
#     Writes a summary CSV file containing data for each project.
#     The CSV file includes headers as specified by 'project_params_dict.keys()',
#     omitting the "NOTES" key. Each project record in 'project_records' is written
#     as a row in the CSV file.
#
#     Parameters:
#     project_records (list of dict): A list of dictionaries, each representing a project record.
#     project_params_dict (dict): A dictionary containing parameters for projects whose keys are column headers.
#     analytics_summary_path (str): The file path where the summary CSV file will be written.
#     """
#
#     # Open the file for writing
#     with open(analytics_summary_path, "w", newline='', encoding="utf-8") as analytics_csv_out:
#         # Filter out the "NOTES" key from the field names
#         csv_columns = [key for key in project_params_dict.keys() if key != "NOTES"]
#         logging.info(f"Filtered csv_columns (excluding 'NOTES'): {csv_columns}")
#
#         # Initialize a CSV DictWriter with the filtered csv_columns
#         csv_writer = csv.DictWriter(analytics_csv_out, fieldnames=csv_columns, dialect='excel')
#
#         # Write the header row
#         csv_writer.writeheader()
#
#         # Write each project record as a row in the CSV file, filtered to exclude "NOTES"
#         for record in project_records:
#             filtered_record = {key: value for key, value in record.items() if key in csv_columns}
#             csv_writer.writerow(filtered_record)
# # There’s a warning in PyCharm stating “Expected type 'SupportsWrite[str]', got 'TextIO' instead”


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
#    Create all the standard reports
    create_summary_csv(project_records_list)
    create_analytics_summary_csv(project_records_list)
    create_data_product_links(project_records_list)
    create_owners_views(project_records_list)
    create_owners_commit_views(project_records_list)
    create_weekly_owners_views(project_records_list)
    create_stakeholders_views(project_records_list)
    create_title_phase_views(project_records_list)
    create_complete_stakeholder_list(project_records_list)

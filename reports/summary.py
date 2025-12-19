import csv
import datetime
import logging
import os
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

from reports.configurations import *


########################################################################################
# Utilities
########################################################################################

def extract_stakeholders(stake_str):
    """
    Stakeholders are comma-separated in the project_info_file
    Extract and return a list of stakeholders
    """
    sh_list = stake_str.strip().split(",")
    sh_list = [x.strip() for x in sh_list if x.strip() is not None and x.strip() != '']
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
    # Remove "NOTES_" prefix and split into individual notes
    notes = [x.strip()[6:] for x in notes_text.split(NOTES_DELIMITER)]
    # check for recent notes
    recent = today_date_obj - timedelta(days=recent_days)
    notes_list = []
    for count, note in enumerate(notes):
        if count < limit:
            update_note = note
            if note.endswith("::"):
                # notes with sequence within a date. Make bulleted list.
                pre, sequence_number, post = note.split("::")
                update_note = f"  {int(sequence_number)}. {pre[11:]}"
            if datetime.strptime(note[:10].replace("_", "-"), DATE_FMT).date() >= recent:
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
                    result.append(f'<u>Data Analyst</u>: {lines["ANALYTICS_DS_OWNER"]} | '
                                  f'[Charter]({lines["COMPUTED_CHARTER_LINK"]}) | '
                                  f'[Project Info]({lines["COMPUTED_PROJECT_INFO_LINK"]})\n\n')
                else:
                    result.append(f'[Charter]({lines["COMPUTED_CHARTER_LINK"]}) | '
                                  f'[Project Info]({lines["COMPUTED_PROJECT_INFO_LINK"]})\n\n')

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


########################################################################################
# Reports
########################################################################################
def create_stakeholders_views(project_records_list):
    # find unique stakeholders
    owners = []
    for lines in project_records_list:
        owners.extend(extract_stakeholders(lines["BUSINESS_SPONSOR"]))
    owners = set(owners)
    logging.debug(f"Processing {len(owners)} stakeholders: {owners}")

    with open(stakeholders_views_active_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Stakeholders Views - ACTIVE\n\n")
        outfile.write(f"({str(today_date_obj)[:19]})\n\n")
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
    # Timestamp exception to using common object - this is report generation time
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
                        outfile.write(f'<tr class="tr-project">'
                                      f'<td>{lines["Project"]}</td>'
                                      f'<td>[{_phase}] active {lines["COMPUTED_AGE_DAYS"]} days &'
                                      f' In-progress {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days '
                                      f' (👕:{size_repr(lines["T-SHIRT_SIZE"])}) <br/>'
                                      f'<a href="{lines["COMPUTED_CHARTER_LINK"]}" target="_blank">Charter</a> | '
                                      f'<a href="{lines["COMPUTED_PROJECT_INFO_LINK"]}" target="_blank">Project Info</a>'
                                      f'</td></tr>\n')
                        notes_block = recent_notes(lines["NOTES"], limit=7)
                        for note in notes_block:
                            note = note.strip().replace("|", ":")
                            outfile.write(f'<tr><td></td><td>{note}</td></tr>\n')
        outfile.write('</table>')
        outfile.write(HTML_FOOTER)


def create_gtm_r1_weekly_owners_views(project_records_list):
    """
    Create output units by owner for weekly meeting update table (ACTIVE)
    Split into two sections:
      1) GTM R1 Projects (Project starts with 'GTM R1 -')
      2) Non-GTM R1 Projects
    """

    def softwrap_project_name(name: str) -> str:
        # Allow wrapping at spaces naturally, plus add extra wrap opportunities:
        # - after " - "
        # - after underscores
        zwsp = "&#8203;"  # zero-width space
        return (name
                .replace(" - ", f" - {zwsp}")
                .replace("_", f"_{zwsp}"))

    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    owners = set([lines["ANALYTICS_DS_OWNER"] for lines in project_records_list])
    gtm_prefix = "GTM R1 -"

    with open(gtm_r1_weekly_owner_views_active_path, "w") as outfile:
        outfile.write(css_style_gtm)
        outfile.write("<h1>DA Weekly - Project Owner Views - ACTIVE</h1>\n\n")

        # -----------------------------
        # GTM R1 Projects
        # -----------------------------
        outfile.write("<h2>GTM R1 Projects</h2>\n\n")
        outfile.write('<table border=0.1>\n')
        outfile.write(f"<tr><th>Projects</th><th>Info <span>(updated: {current_timestamp})</span></th></tr>\n")

        for owner in owners:
            owner_header = False
            for next_phase in active_projects_order:
                for lines in project_records_list:
                    _phase = lines["Phases"]
                    if (lines["ANALYTICS_DS_OWNER"] == owner
                            and _phase == next_phase
                            and lines["Project"].startswith(gtm_prefix)):

                        if not owner_header:
                            owner_header = True
                            outfile.write(f'<tr class="tr-owner"><td colspan=2><b>{owner:}</b></td></tr>\n')

                        outfile.write(
                            f'<tr class="tr-project">'
                            f'<td><div class="project-name">{softwrap_project_name(lines["Project"])}</div></td>'
                            f'<td>'
                            f'  <div class="info-block">'
                            f'    <div class="info-phase">'
                            f'      [{_phase}] active {lines["COMPUTED_AGE_DAYS"]} days &'
                            f'      In-progress {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days '
                            f'      (👕:{size_repr(lines["T-SHIRT_SIZE"])})'
                            f'    </div>'
                            f'    <div class="info-links">'
                            f'      <a href="{lines["COMPUTED_CHARTER_LINK"]}" target="_blank">Charter</a> | '
                            f'      <a href="{lines["COMPUTED_PROJECT_INFO_LINK"]}" target="_blank">Project Info</a>'
                            f'    </div>'
                            f'  </div>'
                            f'</td>'
                            f'</tr>\n'
                        )

                        notes_block = recent_notes(lines["NOTES"], limit=7)
                        for note in notes_block:
                            note = note.strip().replace("|", ":")
                            outfile.write(f'<tr><td></td><td><div class="info-block">{note}</div></td></tr>\n')

        outfile.write("</table>\n\n")

        # -----------------------------
        # Non-GTM R1 Projects (unchanged formatting)
        # -----------------------------
        outfile.write("<h2>Non-GTM R1 Projects</h2>\n\n")
        outfile.write('<table border=0.1>\n')
        outfile.write(f"<tr><th>Projects</th><th>Info <span>(updated: {current_timestamp})</span></th></tr>\n")

        for owner in owners:
            owner_header = False
            for next_phase in active_projects_order:
                for lines in project_records_list:
                    _phase = lines["Phases"]
                    if (lines["ANALYTICS_DS_OWNER"] == owner
                            and _phase == next_phase
                            and not lines["Project"].startswith(gtm_prefix)):

                        if not owner_header:
                            owner_header = True
                            outfile.write(f'<tr class="tr-owner"><td colspan=2><b>{owner:}</b></td></tr>\n')

                        outfile.write(
                            f'<tr class="tr-project">'
                            f'<td>{lines["Project"]}</td>'
                            f'<td>[{_phase}] active {lines["COMPUTED_AGE_DAYS"]} days &'
                            f' In-progress {lines["COMPUTED_IN_PROGRESS_AGE_DAYS"]} days '
                            f' (👕:{size_repr(lines["T-SHIRT_SIZE"])}) <br/>'
                            f'<a href="{lines["COMPUTED_CHARTER_LINK"]}" target="_blank">Charter</a> | '
                            f'<a href="{lines["COMPUTED_PROJECT_INFO_LINK"]}" target="_blank">Project Info</a>'
                            f'</td></tr>\n'
                        )

                        notes_block = recent_notes(lines["NOTES"], limit=7)
                        for note in notes_block:
                            note = note.strip().replace("|", ":")
                            outfile.write(f'<tr><td></td><td>{note}</td></tr>\n')

        outfile.write("</table>")
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
        current_timestamp = today_date_obj.strftime("%Y-%m-%d %H:%M:%S")
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
        outfile.write(f"({str(today_date_obj)[:19]})\n\n")
        for owner in owners:
            outfile.write(synthesize_owner_block(project_records_list, owner))
            # Deprecated SH 2025-08-25
            # outfile.write(synthesize_owner_maintenance_block(project_records_list, owner))

    with open(owner_views_completed_path, "w") as outfile:
        outfile.write("# Data Accelerator - Project Owner Views - COMPLETED & MAINTENANCE\n\n")
        outfile.write(f"({str(today_date_obj)[:19]})\n\n")
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
    df_proj_records = df_proj_records.drop(['NOTES', 'COMPUTED_CHARTER_LINK', 'COMPUTED_PROJECT_INFO_LINK'], axis=1)
    df_proj_records.to_csv(analytics_summary_path, index=False)


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

def create_kanban_board(project_records):
    """ Use makrup language from Mermaid to create a kanban board of active projects
    E.g.

---
config:
  kanban:
    ticketBaseUrl: 'https://mermaidchart.atlassian.net/browse/#TICKET#'
---
kanban
  Todo
    [Create Documentation]
    docs[Create Blog about the new diagram]
  [In progress]
    id6[Create renderer so that it works in all cases. We also add some extra text here for testing purposes. And some more just for the extra flare.]
  id9[Ready for deploy]
    id8[Design grammar]@{ assigned: 'knsv' }
  id10[Ready for test]
    id4[Create parsing tests]@{ ticket: MC-2038, assigned: 'K.Sveidqvist', priority: 'High' }
    id66[last item]@{ priority: 'Very Low', assigned: 'knsv' }
  id11[Done]
    id5[define getData]
    id2[Title of diagram is more than 100 chars when user duplicates diagram with 100 char]@{ ticket: MC-2036, priority: 'Very High'}
    id3[Update DB function]@{ ticket: MC-2037, assigned: knsv, priority: 'High' }

  id12[Can't reproduce]
    id3[Weird flickering in Firefox]
"""
    projects_by_phases = defaultdict(list)
    for lines in project_records:
        projects_by_phases[lines["Phases"]].append((lines["Project"], lines["ANALYTICS_DS_OWNER"]))

    base_url = sharepoint_url + sharepoint_path
    with open(kanban_board_path, "w") as outfile:
        outfile.write(mermaid_kanban_prefix)
        outfile.write("kanban\n")
        for _phase, index in project_phases.items():
            if index in [0, 6, 7,  8, 9]:
                continue
            id_cnt = index*100
            outfile.write(f'  cid{id_cnt}[{_phase.split("-")[1]}]\n')
            for project, owner in projects_by_phases[_phase]:
                project = project.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
                owner = owner.split('(')[0].strip()
                id_cnt += 1
                outfile.write(f'    pid{id_cnt}[{project}]@{{ assigned: \'{owner}\' }}\n')
        outfile.write(mermaid_kanban_posfix)

    
def create_reports(project_records_list):
    # Create all the standard reports
    create_summary_csv(project_records_list)
    create_analytics_summary_csv(project_records_list)
    create_data_product_links(project_records_list)
    create_owners_views(project_records_list)
    create_owners_commit_views(project_records_list)
    create_weekly_owners_views(project_records_list)
    create_stakeholders_views(project_records_list)
    create_title_phase_views(project_records_list)
    create_complete_stakeholder_list(project_records_list)
    create_kanban_board(project_records_list)
    create_gtm_r1_weekly_owners_views(project_records_list)

def configure_report_path_globals(projects_tree_root, today_dt):
    global today_date_obj
    global projects_tree_project_folders
    global summary_path
    global analytics_summary_path
    global data_product_links_path
    global owner_views_active_path
    global owner_views_commit_path
    global weekly_owner_views_active_path
    global owner_views_completed_path
    global stakeholders_views_active_path
    global title_phase_views_path
    global stakeholder_list_path
    global kanban_board_path
    global gtm_r1_weekly_owner_views_active_path
    today_date_obj = today_dt
    # TODO fix this between test and prod
    if projects_tree_root.endswith("Projects Folders"):
        projects_tree_project_folders = projects_tree_root
    else:
        projects_tree_project_folders = os.path.join(projects_tree_root, project_folders_root)
    summary_path = os.path.join(projects_tree_project_folders, "summary.csv")
    analytics_summary_path = os.path.join(projects_tree_project_folders, "analytics_summary.csv")
    data_product_links_path = os.path.join(projects_tree_project_folders, "data_product_links.md")
    owner_views_active_path = os.path.join(projects_tree_project_folders, "owner_views_active.md")
    owner_views_commit_path = os.path.join(projects_tree_project_folders, "owner_views_commit.md")
    weekly_owner_views_active_path = os.path.join(projects_tree_project_folders, "weekly_owner_views_active.html")
    owner_views_completed_path = os.path.join(projects_tree_project_folders, "owner_views_completed.md")
    stakeholders_views_active_path = os.path.join(projects_tree_project_folders, "stakeholders_views_active.md")
    title_phase_views_path = os.path.join(projects_tree_project_folders, "phase_views.md")
    stakeholder_list_path = os.path.join(projects_tree_project_folders, "stakeholder_list.txt")
    kanban_board_path = os.path.join(projects_tree_project_folders, "kanban_board.html")
    gtm_r1_weekly_owner_views_active_path = os.path.join(projects_tree_project_folders, "gtm_r1_weekly_owner_views_active.html")


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

import logging
import dateutil.utils
from datetime import datetime, time
import re

# Import Project Module(s) Below
from reports.configurations import *


dt_today = dateutil.utils.today()

def normalize_note_date(note_line):
    """
    Extract the date from the note string and return it in a sortable format.

    Expected format is "NOTES_yyyy-mm-dd: note text".
    Occasionally there are types or lapses from the pattern. Deal with these:
        notes, Notes, or note --> NOTES
        missing : after date --> add it
        transposed _ and - in dates --> use - in dates
        date string not in yyyy-mm-dd format --> correct it when possible
    """
    date_re =  re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
    date_seq_re =  re.compile(r"\d{4}-\d{1,2}-\d{1,2}-\d{1,2}")   # date with sequence number
    conforming_head_date = None
    try:
        head, tail = note_line.strip().split(":", 1)
    except ValueError:
        logging.warning(f"WARN: Note is poorly formed ({note_line})")
        # assume first space is between head and tail
        head, tail = note_line.strip().split(" ", 1)
    head = head.replace("_","-")   # in case someone transposed in typing

    try:
        head_date = date_seq_re.search(head).group(0)
        y, m, d, sequence_number = head_date.split("-")
        conforming_head_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        logging.info(f"Sequence number {sequence_number} found")
        tail += f"::{sequence_number}::"  # append a sequence number to build bulleted list
    except (ValueError, AttributeError):
        logging.warn(f"WARNING:  Note date is not in yyyy-mm-dd format: {head}")
        try:
            head_date = date_re.search(head).group(0)
            y, m, d = head_date.split("-")
            conforming_head_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        except ValueError:
            logging.error(f"ERROR: Note date is not in yyyy-mm-dd format: {head}")

    try:
        d = datetime.strptime(conforming_head_date, "%Y-%m-%d")
    except ValueError:
        logging.error(f"ERROR: Invalid date ({conforming_head_date})")

    return ":".join(["NOTES_"+conforming_head_date, " "+tail.strip()])

def parse_project_info(project_info_file):
    """
    Parse the project information file for required elements.
        Input is a file object.
        Output is a list of dictionaries
    """
    params_dict = project_params_dict.copy()
    for line in project_info_file:
        if line.startswith("#") or len(line.strip()) == 0:
            # comment lines
            continue
        logging.info(f"Processing line: {line.strip()}")
        fields = [x.strip() for x in line.split(":")]
        if fields[0] in params_dict:
            # In Split on ":", so reassemble the rest of the line in case there were colons in it
            params_dict[fields[0].strip()] = ":".join(fields[1:]).strip().strip('"')
            logging.info(f"Found {fields[0].strip()} in project info file")
        elif fields[0].startswith("NOTE"):
            if params_dict["NOTES"] is None:
                params_dict["NOTES"] = []
            params_dict["NOTES"].append(normalize_note_date(line))  # records include date field and colon
            logging.info(f"Found NOTE in project info file")
        elif fields[0].startswith("COMMIT_JUSTIFICATION"):
            if params_dict["COMMIT_JUSTIFICATIONS"] is None:
                params_dict["COMMIT_JUSTIFICATIONS"] = []
            params_dict["COMMIT_JUSTIFICATIONS"].append(fields[1])
            logging.info(f"Found COMMIT_JUSTIFICATION in project info file")
    # order the notes by date
    if params_dict["NOTES"] is not None:
        params_dict["NOTES"] = order_strings_by_date(params_dict["NOTES"])

    if params_dict["ANALYTICS_DS_OWNER"] is None:
        logging.error("ERROR: No owner specified. This is required! (Check of typos in file tags!)")
    
    return params_dict


def record_timestamp(root, project_info_txt):
    timestamp_key = "Report_Date"
    timestamp_value = datetime.now().strftime(DATE_FMT)

    file_path = os.path.join(root, project_info_txt)
    updated_lines = []
    key_found = False

    with open(file_path, "r") as project_info_file:
        for line in project_info_file:
            if line.startswith(f"{timestamp_key}:"):
                # Overwrite existing timestamp key in updated_line list
                updated_lines.append(f"{timestamp_key}: {timestamp_value}\n")
                key_found = True
            else:
                updated_lines.append(line)

        # If key not found, append to file
        if not key_found:
            updated_lines.append(f"{timestamp_key}: {timestamp_value}\n")

        # Write updated lines from list back to the file
        with open(file_path, "w") as project_info_file:
            project_info_file.writelines(updated_lines)


def compute_phase_dwell(root, project_info_txt, param_key, phase_date, today=dt_today):
    file_path = os.path.join(root, project_info_txt)
    updated_lines = []
    key_found = False

    phase_datetime = datetime.combine(phase_date, time.min)     # parse_date(phase_date, datetime)
    time_in_phase = dt_today - phase_datetime
    with open(file_path, "r") as project_info_file:
        for line in project_info_file:
            if line.startswith(f"{param_key}:"):
                updated_lines.append(f"{param_key}: {time_in_phase}\n")
                key_found = True
            else:
                updated_lines.append(line)

        if not key_found:
            updated_lines.append(f"{param_key}: {time_in_phase}\n")

        with open(file_path, "w") as project_info_file:
            project_info_file.writelines(updated_lines)


def extract_params(root):
    """
    Extract phase and project names for the file path.
        Assume start one directory above "Projects Folders"
    """
    names = root.split("/")  # Split the path into components

    # Ensure names[1] matches expected values
    assert len(names) == 4, f"Unexpected path length: {len(names)} (expected 4)"
    assert names[1] == "Projects Folders", f"Unexpected value for names[1]: {repr(names[1])}"

    # Log extracted phase and project
    logging.info(f"Extracted phase: {names[2]}, project: {names[3]}")
    return names[2], names[3]
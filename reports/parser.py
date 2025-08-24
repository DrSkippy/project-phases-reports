import logging
import re
from datetime import datetime, time
from urllib.parse import quote

# Import Project Module(s) Below
from reports.configurations import *

def set_date_obj(_today_date_obj):
    global today_date_obj
    today_date_obj = _today_date_obj

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
    date_re = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
    date_seq_re = re.compile(r"\d{4}-\d{1,2}-\d{1,2}-\d{1,2}")  # date with sequence number
    conforming_head_date = None
    try:
        head, tail = note_line.strip().split(":", 1)
    except ValueError:
        logging.warning(f"WARN: Note is poorly formed ({note_line})")
        # assume first space is between head and tail
        head, tail = note_line.strip().split(" ", 1)
    head = head.replace("_", "-")  # in case someone transposed in typing

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

    return ":".join(["NOTES_" + conforming_head_date, " " + tail.strip()])


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
    timestamp_value = today_date_obj.strftime(DATE_FMT)

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


def compute_stage_date(params, stage_key):
    """
    Compute the date for a given stage key in the params dictionary.
    Returns (stage_date: datetime, needs_write: bool, value_to_write: str or None)
    """
    if params[stage_key] is None:
        # return date as dt & str and flag for future write
        stage_date = today_date_obj
        params[stage_key] = stage_date.strftime(DATE_FMT)
        return stage_date, True, stage_date.strftime(DATE_FMT)
    else:
        # Just parse, no write required
        stage_date = datetime.strptime(params[stage_key][:10], DATE_FMT)
        return stage_date, False, None


def compute_phase_dwell(root, project_info_txt, param_key, phase_date, today):
    file_path = os.path.join(root, project_info_txt)
    updated_lines = []
    key_found = False
    phase_datetime = datetime.combine(phase_date, time.min)
    time_in_phase = today - phase_datetime
    with open(file_path, "r") as project_info_file:
        for line in project_info_file:
            if line.startswith(f"{param_key}:"):
                updated_lines.append(f"{param_key}: {time_in_phase}\n")
                key_found = True
            else:
                updated_lines.append(line)
    if not key_found:
        updated_lines.append(f"{param_key}: {time_in_phase}\n")
    return updated_lines


def extract_params(root):
    """
    Extract phase and project names for the file path.
        Assume start one directory above "Projects Folders"
    """
    names = root.split("/")  # phase, project
    for i_loc, name in enumerate(names):
        if name == "Projects Folders":
            break
    names = names[i_loc - 1:]
    assert (len(names) == 4 and names[1] == "Projects Folders")
    logging.info(f"Extracted phase: {names[2]}, project: {names[3]}")
    if names[2] is None or names[3] is None:
        raise ValueError(
            f"Invalid project root path: {self.project_root}. Expected format: '/Projects Folders/<phase>/<project>'")
    return names[2], names[3]


def create_charter_link(root, dirs, files):
    """
    Create a link to the charter file.
    """
    res = []  # list of urls to charter files in directory
    for file in files:
        if file.endswith(".docx") and "charter" in file.lower():
            names = extract_params(root)
            if len(names) == 2:
                logging.info(f"Found charter file: {file} for phase: {names[0]}, project: {names[1]}")
                url = sharepoint_url + quote(f"{sharepoint_path}/{names[0]}/{names[1]}/{file}")
                logging.info(f"Charter URL: {url}")
                res.append(url)
    return res

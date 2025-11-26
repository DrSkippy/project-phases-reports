import logging
import re
from urllib.parse import quote
from datetime import datetime

# Import Project Module(s) Below
from reports.configurations import *


# 2025-11-26 def set_date_obj(_today_date_obj):
# 2025-11-26     """
# 2025-11-26     Sets the global date object value for usage across the application.
# 2025-11-26
# 2025-11-26     Args:
# 2025-11-26         _today_date_obj: The date object to be set as the global date object.
# 2025-11-26     """
# 2025-11-26     global today_date_obj
# 2025-11-26     today_date_obj = _today_date_obj


def normalize_note_date(note_line):
    """
    Normalizes the date format within a note and appends necessary sequence numbers if present. This
    function processes the note to ensure it follows the proper "NOTES_yyyy-mm-dd: content" format,
    handling cases where the note format is inconsistent or dated incorrectly.

    Args:
        note_line (str): The raw note line to be normalized, expected to contain a leading date
            followed by content separated by a colon or space.

    Returns:
        str: The normalized note string with the proper format.

    Raises:
        ValueError: Raised if invalid date formatting is encountered.
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


# 2025-11-26 def parse_project_info(project_info_file):
# 2025-11-26     """
# 2025-11-26     Parses a project information file and extracts relevant fields into a dictionary.
# 2025-11-26
# 2025-11-26     This function processes each line in the provided project information file, extracts
# 2025-11-26     key-value pairs, and stores them in a dictionary. It also processes specific fields like
# 2025-11-26     notes and commit justifications with special handling.
# 2025-11-26
# 2025-11-26     Args:
# 2025-11-26         project_info_file: A file-like object representing the project information
# 2025-11-26             file. Each line in the file represents a field or comment.
# 2025-11-26
# 2025-11-26     Returns:
# 2025-11-26         dict: A dictionary containing the parsed project information, including
# 2025-11-26             standard fields and any additional notes or commit justifications.
# 2025-11-26     """
# 2025-11-26     params_dict = project_params_dict.copy()
# 2025-11-26     for line in project_info_file:
# 2025-11-26         if line.startswith("#") or len(line.strip()) == 0:
# 2025-11-26             # comment lines
# 2025-11-26             continue
# 2025-11-26         logging.info(f"Processing line: {line.strip()}")
# 2025-11-26         fields = [x.strip() for x in line.split(":")]
# 2025-11-26         if fields[0] in params_dict:
# 2025-11-26             # In Split on ":", so reassemble the rest of the line in case there were colons in it
# 2025-11-26             params_dict[fields[0].strip()] = ":".join(fields[1:]).strip().strip('"')
# 2025-11-26             logging.info(f"Found {fields[0].strip()} in project info file")
# 2025-11-26         elif fields[0].startswith("NOTE"):
# 2025-11-26             if params_dict["NOTES"] is None:
# 2025-11-26                 params_dict["NOTES"] = []
# 2025-11-26             params_dict["NOTES"].append(normalize_note_date(line))  # records include date field and colon
# 2025-11-26             logging.info(f"Found NOTE in project info file")
# 2025-11-26         elif fields[0].startswith("COMMIT_JUSTIFICATION"):
# 2025-11-26             if params_dict["COMMIT_JUSTIFICATIONS"] is None:
# 2025-11-26                 params_dict["COMMIT_JUSTIFICATIONS"] = []
# 2025-11-26             params_dict["COMMIT_JUSTIFICATIONS"].append(fields[1])
# 2025-11-26             logging.info(f"Found COMMIT_JUSTIFICATION in project info file")
# 2025-11-26     # order the notes by date
# 2025-11-26     if params_dict["NOTES"] is not None:
# 2025-11-26         params_dict["NOTES"] = order_strings_by_date(params_dict["NOTES"])
# 2025-11-26
# 2025-11-26     if params_dict["ANALYTICS_DS_OWNER"] is None:
# 2025-11-26         logging.error("ERROR: No owner specified. This is required! (Check of typos in file tags!)")
# 2025-11-26
# 2025-11-26     return params_dict
# 2025-11-26
# 2025-11-26
# 2025-11-26 def record_timestamp(root, project_info_txt, date_obj):
# 2025-11-26     """
# 2025-11-26     Updates or appends a timestamp entry in a project information file.
# 2025-11-26
# 2025-11-26     This function reads the specified project info file and searches for a specific
# 2025-11-26     timestamp key to either update its value or append it if it does not already exist.
# 2025-11-26     The timestamp is generated based on the provided `date_obj`.
# 2025-11-26
# 2025-11-26     Args:
# 2025-11-26         root (str): The root directory where the project info file is located.
# 2025-11-26         project_info_txt (str): The name of the project info file to be updated.
# 2025-11-26         date_obj (datetime): A datetime object used to generate the timestamp value.
# 2025-11-26     """
# 2025-11-26     timestamp_key = "Report_Date"
# 2025-11-26     timestamp_value = date_obj.strftime(DATE_FMT)
# 2025-11-26
# 2025-11-26     file_path = os.path.join(root, project_info_txt)
# 2025-11-26     updated_lines = []
# 2025-11-26     key_found = False
# 2025-11-26
# 2025-11-26     with open(file_path, "r") as project_info_file:
# 2025-11-26         for line in project_info_file:
# 2025-11-26             if line.startswith(f"{timestamp_key}:"):
# 2025-11-26                 # Overwrite existing timestamp key in updated_line list
# 2025-11-26                 updated_lines.append(f"{timestamp_key}: {timestamp_value}\n")
# 2025-11-26                 key_found = True
# 2025-11-26             else:
# 2025-11-26                 updated_lines.append(line)
# 2025-11-26
# 2025-11-26         # If key not found, append to file
# 2025-11-26         if not key_found:
# 2025-11-26             updated_lines.append(f"{timestamp_key}: {timestamp_value}\n")
# 2025-11-26
# 2025-11-26         # Write updated lines from list back to the file
# 2025-11-26         with open(file_path, "w") as project_info_file:
# 2025-11-26             project_info_file.writelines(updated_lines)

def extract_params(root):
    """
    Extracts phase and project name from the given root path.

    This function takes a file path and parses it to extract specific components:
    'phase' and 'project'. The expected format of the input path is
    '/Projects Folders/<phase>/<project>'. The function validates that the path
    is well-formed and logs the extracted components.

    Args:
        root (str): The file path to parse and extract phase and project names.

    Returns:
        Tuple[str, str]: A tuple containing the extracted phase and project name.

    Raises:
        ValueError: If the provided root path is invalid or does not conform to
        the expected format.
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
    Generates a list of URLs for charter files located in a specified directory and constructs a base URL.

    The function scans through files in a given directory, identifying charter files based on specific naming
    criteria. It builds URLs to these files using predefined paths and names extracted from the directory structure.
    The function also constructs a base URL for linking purposes.

    Args:
        root (str): The root directory path being scanned.
        dirs (list[str]): A list of subdirectories in the root directory (unused in this function).
        files (list[str]): A list of file names in the root directory.

    Returns:
        tuple[list[str], str]: A tuple containing:
            - A list of URLs (list[str]) pointing to the charter files found in the directory.
            - A base URL (str) constructed using the directory structure.

    Raises:
        None
    """
    res = []  # list of urls to charter files in directory
    names = extract_params(root)
    base_url = sharepoint_url + quote(f"{sharepoint_path}/{names[0]}/{names[1]}/")
    logging.info(f"Base URL: {base_url}")
    for file in files:
        if file.endswith(".docx") and "charter" in file.lower():
            if len(names) == 2:
                logging.info(f"Found charter file: {file} for phase: {names[0]}, project: {names[1]}")
                url = sharepoint_url + quote(f"{sharepoint_path}/{names[0]}/{names[1]}/{file}")
                url += '?web=1'
                logging.info(f"Charter URL: {url}")
                res.append(url)
    return res, base_url


def order_strings_by_date(string_list):
    """
    Orders a list of strings by the embedded date in descending order.

    This function processes a list of strings where each string contains a
    date embedded in a specific format. It extracts and replaces underscores
    ('_') with hyphens ('-') in the date portion, then sorts the list
    in reverse chronological order.

    Args:
        string_list (List[str]): A list of strings, each containing a date
            substring in the format YYYY_MM_DD_HH_MM.

    Returns:
        List[str]: A list of strings sorted by their embedded date in
            descending order.
    """
    res = sorted(string_list, reverse=True, key=lambda x: x[:16].replace("_", "-"))
    return res

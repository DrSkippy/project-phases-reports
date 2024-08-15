import logging
import datetime
from reports.configurations import *

def normalize_note_date(note):
    """
    Extract the date from the note string and return it in a sortable format.
    """
    try:
        head, tail = note.strip().split(":", 1)
    except ValueError:
        logging.error(f"ERROR: Note is poorly formed ({note})")
        return note.strip()
    head = head.upper()  # eg note or Note to NOTE
    head = head.replace("_", "-")
    head = head.replace("NOTES-","NOTES_")
    if not head.startswith("NOTES_"):
        logging.error(f"ERROR: Note does not start with 'NOTES': {head}")
    else:
        hdate = head.split("_")[1]
        try:
            d = datetime.datetime.strptime(hdate, "%Y-%m-%d")
        except ValueError:
            logging.error(f"ERROR: Note date is not in yyyy-mm-dd format: {hdate}")
    return ":".join([head, tail.strip()])

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

    return params_dict


def extract_params(root):
    """
    Extract phase and project names for the file path.
        Assume start one directory above "Projects Folders"
    """
    names = root.split("/")  # phase, project
    assert (len(names) == 4 and names[1] == "Projects Folders")
    logging.info(f"Extracted phase: {names[2]}, project: {names[3]}")
    return names[2], names[3]

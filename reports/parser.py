import logging
from reports.configurations import *


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
        logging.info(f"Processing line: {line}")
        fields = line.split(":")
        if fields[0].strip() in params_dict:
            # In Split on ":", so reassemble the rest of the line in case there were colons in it
            params_dict[fields[0].strip()] = ":".join(fields[1:]).strip().strip('"')
            logging.info(f"Found {fields[0].strip()} in project info file")
        elif fields[0].startswith("NOTE"):
            if params_dict["NOTES"] is None:
                params_dict["NOTES"] = []
            params_dict["NOTES"].append(line.strip())  # records include date field and colon
            logging.info(f"Found NOTE in project info file")
        elif fields[0].startswith("COMMIT_JUSTIFICATION"):
            if params_dict["COMMIT_JUSTIFICATION"] is None:
                params_dict["COMMIT_JUSTIFICATION"] = []
            params_dict["COMMIT_JUSTIFICATION"].append(
                line.split(":")[1].strip())  # lines will be concatenated in order they appear
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

import logging
import fileinput
import uuid
from datetime import datetime

from reports.configurations import *
from reports.parser import normalize_note_date, create_charter_link


class ProjectFileObject:
    def __init__(self, root, files, project_info_filename: str):
        self.project_info_filepath = project_info_filename
        self.project_root = root
        self.files = files
        self.params_dict = project_params_dict.copy()
        self.parse_file()
        self.setup_special_fields()

    def setup_special_fields(self):
        self.uuid()
        self.record_timestamp()
        self.determine_phase_change()

    def uuid(self):
        """
        Generate a UUID for the project based on the root path.
        The UUID is stored in the params_dict under the key "UUID".
        """
        if "Project_ID" not in self.params_dict or self.params_dict["Project_ID"] is None:
            self.params_dict["Project_ID"] = StringLine(key="Project_ID", value=str(uuid.uuid1()), new=True)
        self.uuid = self.params_dict["Project_ID"].value

    def record_timestamp(self):
        if "Report_Date" not in self.params_dict or self.params_dict["Report_Date"] is None:
            self.params_dict["Report_Date"] = StringLine(key="Report_Date", value=datetime.now().strftime(DATE_FMT), new=True)
        else:
            self.params_dict["Report_Date"].update_value(datetime.now().strftime(DATE_FMT))

    def determine_phase_change(self):
        """
        Determine if the phase or project has changed based on the file path.
        If the phase or project has changed, update the params_dict accordingly.
        """
        if "COMPUTED_PREVIOUS_PHASE" not in self.params_dict or self.params_dict["COMPUTED_PREVIOUS_PHASE"] is None:
            self.params_dict["COMPUTED_PREVIOUS_PHASE"] = StringLine(key="COMPUTED_PREVIOUS_PHASE", value=self.phase, new=True)
            logging.info(f"Setting initial phase: {self.phase} for project: {self.project}")
        elif self.phase != self.params_dict["COMPUTED_PREVIOUS_PHASE"].value:
            logging.info(f"Phase has changed: {self.phase}, {self.project}")
            current_phase = self.params_dict["COMPUTED_PREVIOUS_PHASE"].value
            self.params_dict["COMPUTED_PREVIOUS_PHASE"].update_value(self.phase)
            new_line = f'{current_phase} -> {self.phase} DATE: {datetime.now().strftime(DATE_FMT)}\n'
            self.params_dict["PHASE_CHANGE"] = StringLine(key="PHASE_CHANGE", value=new_line, new=True)

    def extract_params(self):
        """
        Extract phase and project names for the file path.
            Assume start one directory above "Projects Folders"
        """
        names = self.project_root.split("/")  # phase, project
        assert (len(names) == 4 and names[1] == "Projects Folders")
        logging.info(f"Extracted phase: {names[2]}, project: {names[3]}")
        if names[2] is None or names[3] is None:
            raise ValueError(f"Invalid project root path: {self.project_root}. Expected format: '/Projects Folders/<phase>/<project>'")
        self.phase, self.project = names[2], names[3]

    def parse_file(self):
        # Process Project Info file
        projects_processed_counter = 0
        with open(os.path.join(self.project_root, project_info_filename), "r") as project_info_file:
            logging.info(f"Processing file {projects_processed_counter} ({self.project_root})")
            projects_processed_counter += 1
            self.extract_params()  # harvest parameters from path
            ##########################################################################
            ## Meta parmaeters not parsed from file
            self.params_dict["Phases"] = StringLine(key="Phases", value=self.phase)
            self.params_dict["Project"] = StringLine(key="Project", value=self.project)
            self.params_dict["CharterLink"] = StringLine(key="CharterLink",
                                            value=create_charter_link(self.project_root,
                                                                      "refactor me away", self.files))

            ###########################################################################
            ## Parse the file line by line
            agg_lines = AggregateLines()
            for line in project_info_file:
                obj = StringLine(line)
                if obj.key is not None and obj.key in self.params_dict:
                    self.params_dict[obj.key] = obj
                elif obj.aggregate_key is not None and obj.aggregate_key in self.params_dict:
                    agg_lines.add_line(obj)
                    self.params_dict[obj.aggregate_key] = agg_lines
                elif obj.comment:
                    logging.info(f"Comment line found: {obj.line}")
                else:
                    logging.error(f"Key {obj.key} not found in params_dict, line: {line.strip()}")

    def get_legacy_params(self):
        """
        Get legacy parameters from the params_dict.
        Returns a dictionary with keys as parameter names and values as StringLine objects.
        """
        legacy_params = {}
        for key, line_obj in self.params_dict.items():
            if isinstance(line_obj, StringLine) or isinstance(line_obj, AggregateLines):
                legacy_params[key] = line_obj.get(key)
            else:
                logging.info(f'In "{self.project_root}": at key={key} line_obj={line_obj} is not a StringLine or AggregateLines')
                legacy_params[key] = line_obj
        return legacy_params

    def finalize_file(self):
        # In place changes
        replaced_in_file = False
        appended_in_file = False
        for line in fileinput.input(os.path.join(self.project_root, project_info_filename), inplace=True):
            for key, obj in self.params_dict.items():
                if isinstance(obj, StringLine) and obj.updated and line.startswith(key):
                    print(f"{key}: {obj.value}")
                    replaced_in_file = True
                    break
            else:
                print(line, end='')
        # Append new lines to the file
        with open(os.path.join(self.project_root, project_info_filename), "a") as project_info_file:
            for key, obj in self.params_dict.items():
                if isinstance(obj, StringLine) and obj.new:
                    append_in_file = True
                    project_info_file.write(str(obj) + "\n")

        return replaced_in_file, appended_in_file

class AggregateLines:
    def __init__(self):
        self.aggregate_dict = {}

    def add_line(self, line_obj):
        """
        Add a line object to the aggregate dictionary under the specified key.
        If the key does not exist, create a new list for that key.
        """
        if line_obj.aggregate_key not in self.aggregate_dict:
            self.aggregate_dict[line_obj.aggregate_key] = []
        self.aggregate_dict[line_obj.aggregate_key].append(line_obj)

    def get_notes(self):
        if "NOTES" in self.aggregate_dict:
            notes_list = [normalize_note_date(obj.line) for obj in self.aggregate_dict["NOTES"]]
            notes_list = order_strings_by_date(notes_list)
            return NOTES_DELIMITER.join(notes_list) + "\n\n"
        else:
            return "No notes found.\n\n"

    def get_commit_justifications(self):
        if "COMMIT_JUSTIFICATIONS" in self.aggregate_dict:
            commit_justifications = [obl.value for obl in self.aggregate_dict["COMMIT_JUSTIFICATIONS"]]
            return " ".join(commit_justifications) + "\n\n"
        else:
            return "No commit justifications found.\n\n"

    def get(self, key):
        """
        Get the list of StringLine objects for the specified key.
        If the key does not exist, return an empty list.
        """
        if key.lower().startswith("note"):
            return self.get_notes()
        elif key.lower().startswith("commit_justification"):
            # Return the list of StringLine objects for the specified key
            return self.get_commit_justifications()
        else:
            return ""


class StringLine:
    def __init__(self, line=None, key=None, value=None, new=False):
        self.line = line
        self.suffix = None           # raw line after "key:
        self.date_value = None
        self.int_value = None
        # Flags
        self.parsed = False
        self.updated = False
        self.new = False
        self.comment = False
        # Parse lines
        self.route_line_for_parsing(key, new, value)
        self.parse_date()
        self.parse_int()
        # Deal with aggregates
        self.aggregate_key = None
        self.compute_aggregate_key()

    def route_line_for_parsing(self, key, new, value):
        if key is not None and value is not None:
            # if key and value are provided, set them directly and create the line
            self.key = key.strip()
            if isinstance(value, str):
                self.value = value.strip()
            else:
                # is a python number type or structure`
                self.value = value
            self.suffix = self.value
            self.line = f"{key}: {value}"
            self.new = new
        elif key is None or value is None or new is False:
            if self.line is None or self.line == "":
                raise ValueError(f"Line must be provided if key or value is not specified. ({line}, {key}, {value})")
            self.line = self.line.strip()  # raw line from the file
            # if key or value is not provided, parse the line
            self.key = None
            self.value = None
            fields = [x.strip() for x in self.line.split(":")]
            self.parse(fields)
            self.set_parsed_value()
        elif self.line.startswith("#"):
            self.line = line.strip()  # raw line from the file
            # if the line starts with a comment, set it as a comment
            self.key = None
            self.value = None
            self.suffix = self.line[1:].strip()
            self.comment = True


    def parse(self, fields) -> str:
        self.key = fields[0].strip()
        self.suffix = ":".join(fields[1:]).strip().strip('"')

    def set_parsed_value(self):
        if self.line is not None and self.line != "":
            self.value = self.suffix
            self.parsed = True
        else:
            self.value = None
            self.parsed = False

    def compute_aggregate_key(self):
        """
        Compute the aggregate key based on the key and value.
        If the key is None, set the aggregate key to None.
        """
        if self.key is not None:
            if self.key.lower().startswith("note"):
                self.aggregate_key = "NOTES"
            elif self.key.lower().startswith("commit_justification"):
                self.aggregate_key = "COMMIT_JUSTIFICATIONS"

    def parse_int(self):
        """
        Parse the value as an integer if possible.
        """
        if self.value is not None:
            try:
                self.int_value = int(self.value)
            except (ValueError, TypeError):
                logging.warning(f"Invalid integer format in line: {self.line}")
                self.int_value = None

    def parse_date(self):
        """
        Parse the date from the line and set the date attribute.
        """
        if self.value is not None:
            try:
                self.date_value = datetime.strptime(self.value, DATE_FMT).date()
            except (ValueError, TypeError):
                self.date_value = None
                logging.warning(f"Invalid date format in line: {self.line}")

    def update_value(self, value: str):
        """
        Update the value of the line and mark it as updated.
        """
        if value is None or value == "":
            self.updated = False
        elif value.strip() == self.value:
            self.updated = False
        else:
            self.value = value.strip()
            self.updated = True
            self.parse_date()
            self.parse_int()

    def get(self, key: str = None):
        if key != self.key:
            logging.error(f"Key {key} does not match the key of the line: {self.key}")
            return None
        # Return most parsed value of line
        if self.date_value is not None:
            return self.date_value
        elif self.int_value is not None:
            return self.int_value
        elif self.value is not None:
            return self.value
        else:
            return None

    def __str__(self):
        """
        Return the string representation of the line.
        """
        if self.comment:
            return f"# {self.line}"
        elif self.key is not None and self.value is None:
            return f"{self.key}:"
        elif self.key is not None and self.value is not None:
            return f"{self.key}: {self.value}"
        else:
            return self.line

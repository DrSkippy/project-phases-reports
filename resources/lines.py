import logging
from datetime import datetime

from reports.configurations import *
from reports.parser import normalize_note_date, order_strings_by_date


class AggregateLines:
    def __init__(self):
        self.aggregate_dict = {}
        self.is_in_reports = True

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
    def __init__(self, line=None, key=None, value=None, new=False, in_reports=True):
        self.line = line  # Single line from project file
        self.date_value = None  # Parsed date value if applicable
        self.int_value = None  # Parsed integer value if applicable
        self.key = None
        self.value = None
        # Flags
        self.is_in_reports = in_reports  # Set to false if field is only in file and not in reports
        self.existing_variable_updated = False
        self.add_new_variable = False
        self.is_comment = False
        # Parse lines
        self.route_line_for_parsing(key, value, new)
        # Deal with aggregate lines e.g. notes and justifications
        self.aggregate_key = None  # This line belongs to which aggregate key...
        self.compute_aggregate_key()

    def route_line_for_parsing(self, key, value, new):
        if key is not None and value is not None:
            # if key and value are provided, set them directly and create the line
            self.key = key.strip()
            if isinstance(value, str):
                self.value = value.strip()
            else:
                # is a python number type or structure`
                self.value = value
            self.line = f"{key}: {value}"  # construct the file line
            self.add_new_variable = new
        elif key is None or value is None or new is False:
            if self.line is None or self.line == "":
                raise ValueError(f"Line must be provided if key or value is not specified. ({line}, {key}, {value})")
            self.line = self.line.strip()  # raw line from the file
            # if key or value is not provided, parse the line
            self.parse_line()
        elif self.line.startswith("#"):
            self.line = line.strip()  # raw line from the file
            # if the line starts with a comment, set it as a comment
            self.value = self.line[1:].strip()
            self.is_comment = True

    def parse_line(self) -> str:
        if self.line is not None and self.line != "":
            fields = [x.strip() for x in self.line.split(":")]
            self.key = fields[0].strip()
            self.value = ":".join(fields[1:]).strip().strip('"')
            self.parse_date_if_present()
            self.parse_int_if_present()
        else:
            raise ValueError(
                f"Line must be provided if key or value is not specified. ({self.line}, {self.key}, {self.value})")

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

    def parse_int_if_present(self):
        """
        Parse the value as an integer if possible.
        """
        if self.value is not None:
            try:
                self.int_value = int(self.value)
            except (ValueError, TypeError):
                logging.debug(f"Invalid integer format in line: {self.line}")

    def parse_date_if_present(self):
        """
        Parse the date from the line and set the date attribute.
        """
        if self.value is not None:
            try:
                self.date_value = datetime.strptime(self.value, DATE_FMT).date()
            except (ValueError, TypeError):
                logging.debug(f"Invalid date format in line: {self.line}")

    def update_value(self, value: str):
        """
        Update the value of the line and mark it as updated.
        """
        if value is None or value == "" or str(value).strip() == self.value:
            self.existing_variable_updated = False
        else:
            self.value = str(value).strip()
            self.existing_variable_updated = True
            self.parse_date_if_present()
            self.parse_int_if_present()

    def get(self, key: str = None):
        if key != self.key:
            logging.error(f"Key {key} does not match the key of the line: {self.key}")
            return None
        # Return highest info parsed value of line
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
        return self.line

import logging
from datetime import date, datetime

from reports.configurations import *
from reports.parser import normalize_note_date, order_strings_by_date


class AggregateLines:
    def __init__(self):
        self.aggregate_dict = {}
        self.is_in_reports = True

    def add_line(self, line_obj):
        """
        Adds a line object to the aggregation dictionary based on its aggregate key.

        The method checks if the aggregate key of the given line object is not already
        present in the aggregation dictionary. If not, it initializes an empty list
        for that key. Then, it appends the line object to the corresponding list.

        Args:
            line_obj: An object containing an `aggregate_key` attribute used as the
                key in the dictionary and other data associated with the key.
        """
        if line_obj.aggregate_key not in self.aggregate_dict:
            self.aggregate_dict[line_obj.aggregate_key] = []
        self.aggregate_dict[line_obj.aggregate_key].append(line_obj)

    def get_notes(self):
        """
        Retrieves and processes notes from the aggregate dictionary.

        This method extracts notes from the "NOTES" section of the aggregate dictionary,
        normalizes their date format, orders them chronologically, and concatenates
        them into a single string with a specified delimiter. If no notes are found
        in the aggregate dictionary, a default message is returned.

        Returns:
            str: A single string containing all formatted and sorted notes, separated by the
            defined delimiter, or a default message if no notes are available.
        """
        if "NOTES" in self.aggregate_dict:
            notes_list = [normalize_note_date(obj.line) for obj in self.aggregate_dict["NOTES"]]
            notes_list = order_strings_by_date(notes_list)
            return NOTES_DELIMITER.join(notes_list) + "\n\n"
        else:
            return "No notes found.\n\n"

    def get_commit_justifications(self):
        """
        Fetches and formats the commit justifications if available.

        This method checks for the presence of commit justifications in the
        `aggregate_dict` dictionary under the key "COMMIT_JUSTIFICATIONS". If present, it
        concatenates their values into a single string separated by spaces and appends
        two newlines. If not available, it returns a default string indicating no
        commit justifications were found.

        Returns:
            str: Formatted string of commit justifications or a default message.
        """
        if "COMMIT_JUSTIFICATIONS" in self.aggregate_dict:
            commit_justifications = [obl.value for obl in self.aggregate_dict["COMMIT_JUSTIFICATIONS"]]
            return " ".join(commit_justifications) + "\n\n"
        else:
            return "No commit justifications found.\n\n"

    def get(self, key):
        """
        Fetches a value based on the provided key. If the key matches specific patterns,
        such as those starting with "note" or "commit_justification", it retrieves
        corresponding information. Returns an empty string for unmatched keys.

        Args:
            key: The string used to determine the type of information to retrieve.

        Returns:
            The requested information, either as notes or commit justifications, based
            on the key. Returns an empty string if the key does not match any
            predefined patterns.
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
        """
        Sets or parses a line for processing and extraction while maintaining proper formatting
        and handling conditions based on provided inputs. The function adjusts behavior whether
        key and value are provided or not and ensures proper parsing of data types.

        Args:
            key: The key to associate with the line if explicitly provided.
            value: The value corresponding to the key to associate with the line. If not a
                string, it is assigned as-is.
            new: A flag to indicate whether this is a new variable to add or override.

        Raises:
            ValueError: If both key and value are not provided and the existing line is either
                missing or empty. This situation mandates the presence of at least one of
                the key, value, or valid existing line contents.
        """
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
        elif key is None or value is None:
            if self.line is None or self.line == "":
                raise ValueError(
                    f"Line must be provided if key or value is not specified. ({self.line}, {key}, {value})")
            self.line = self.line.strip()  # raw line from the file
            # if key or value is not provided, parse the line
            self.parse_line()
        elif self.line.startswith("#"):
            self.line = line.strip()  # raw line from the file
            # if the line starts with a comment, set it as a comment
            self.value = self.line[1:].strip()
            self.is_comment = True
        self.parse_date_if_present()
        self.parse_int_if_present()

    def parse_line(self) -> str:
        if self.line is not None and self.line != "":
            fields = [x.strip() for x in self.line.split(":")]
            self.key = fields[0].strip()
            self.value = ":".join(fields[1:]).strip().strip('"')
        else:
            raise ValueError(
                f"Line must be provided if key or value is not specified. ({self.line}, {self.key}, {self.value})")

    def compute_aggregate_key(self):
        """
        Determines and sets an aggregate key based on the value of the current key.

        This function evaluates the current value of `self.key` and determines an
        appropriate aggregate category. If `self.key` starts with specific prefixes
        (case-insensitive), the function assigns a corresponding predefined aggregate
        key value to `self.aggregate_key`.

        Raises:
            AttributeError: If `self.key` or `self.aggregate_key` is not properly
                defined as attributes of the class instance.
        """
        if self.key is not None:
            if self.key.lower().startswith("note"):
                self.aggregate_key = "NOTES"
            elif self.key.lower().startswith("commit_justification"):
                self.aggregate_key = "COMMIT_JUSTIFICATIONS"

    def parse_int_if_present(self):
        """
        Attempts to parse the instance's value as an integer, if present.

        This method checks if the `value` attribute is not None. If `value` is not None,
        it attempts to convert it to an integer and stores the result in the `int_value`
        attribute. If the conversion fails due to an invalid format or type, it logs a
        debug message indicating that the parsing attempt failed.

        Raises:
            ValueError: If the attribute `value` cannot be converted to an integer.
            TypeError: If the attribute `value` is of an incompatible type.
        """
        if self.value is not None:
            try:
                self.int_value = int(self.value)
            except (ValueError, TypeError):
                logging.debug(f"Invalid integer format in line: {self.line}")

    def parse_date_if_present(self):
        """
        Parses and assigns a date value to the attribute `date_value` if the attribute
        `value` is present and is of a recognizable date or datetime format.

        Raises:
            None: The function does not raise exceptions directly but will log a debug
            message if the `value` does not match the expected date format or is of an
            unrecognized type.

        Args:
            None: This method does not take any arguments directly. It operates on the
            instance's attributes.

        Returns:
            None: The method modifies the instance attribute `date_value` directly and
            does not return any value.
        """
        if self.value is not None:
            if isinstance(self.value, datetime):
                self.date_value = self.value.date()
                return
            elif isinstance(self.value, date):
                self.date_value = self.value
                return
            else:
                try:
                    self.date_value = datetime.strptime(self.value, DATE_FMT).date()
                except (ValueError, TypeError):
                    logging.debug(f"Invalid date format in line: {self.line}")

    def update_value(self, value: str):
        """
        Updates the current value and its associated attributes if the new value is valid.

        The method checks if the provided value is not None, not an empty string, and
        differs from the current stored value. If these conditions are met, it updates
        the value, reformats the line with the key-value pair, marks that the variable
        has been updated, and triggers specific parsing functions to check for date
        or integer values within the updated input.

        Args:
            value (str): The new value to be assigned. Must be a non-empty string and
                different from the current value to trigger updates.
        """
        if value is None or value == "" or str(value).strip() == self.value:
            self.existing_variable_updated = False
        else:
            self.value = str(value).strip()
            self.line = f"{self.key}: {self.value}"
            self.existing_variable_updated = True
            self.parse_date_if_present()
            self.parse_int_if_present()

    def get(self, key: str = None):
        """
        Gets the relevant parsed value associated with the given key, if the key matches this object's key.
        Returns the most significant parsed value available (date_value, int_value, or value) in a prioritized order.

        Args:
            key (str): The key to be matched against this object's key.

        Returns:
            Any: Returns the most significant parsed value of the object in the following
            order of priority: date_value, int_value, value. If no significant value is
            available or the keys do not match, returns None.
        """
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
        Converts the object into its string representation.

        This method is used to provide a readable or useful string representation
        of the object. It is particularly useful for debugging and logging or when
        objects need to be displayed as strings.

        Returns:
            str: The string representation of the object.
        """
        return self.line

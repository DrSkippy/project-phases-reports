import fileinput
import logging
import uuid
from datetime import datetime

from reports.configurations import *
from reports.parser import create_charter_link, extract_params
from resources.lines import StringLine, AggregateLines

def set_date_obj(_today_date_obj):
    """
    Sets the global date object for today's date.

    This function assigns the provided date object to the global variable
    `today_date_obj`. It is intended to manage the application's
    representation of the current date.

    Args:
        _today_date_obj: The date object to set as the current date.
    """
    global today_date_obj
    today_date_obj = _today_date_obj

class ProjectFileObject:
    def __init__(self, root, files, project_info_filename: str):
        """
        Initializes an instance of the class and sets up the initial state, including
        mapping phase identifiers to their respective functions, parsing project-related
        files, and invoking the corresponding phase function based on the current phase.

        Args:
            root: The root directory path for the project.
            files: A collection of files related to the project.
            project_info_filename: The filename of the project information file.

        """
        self.uuid = None
        self.phase = None
        self.previous_phase = None
        self.project = None
        # setup phase functions mapping
        self.phase_functions = {
            "0-Ideas": self.phase0,
            "1-Chartering": self.phase1,
            "2-Committed": self.phase2,
            "3-In Progress": self.phase3,
            "4-On Hold": self.phase4,
            "5-Rollout": self.phase5,
            "6-Completed": self.phase6}
        self.project_info_filepath = project_info_filename
        self.project_root = root
        self.files = files
        # initialize params_dict with default parameters
        self.params_dict = project_params_dict.copy()
        # 1. Parse the project info file and populate params_dict
        self.parse_file()
        # 2. Setup special fields like UUID, timestamps, phase changes, and links
        self.setup_special_fields()
        # 3. Call the appropriate phase function based on the current phase
        self.phase_functions[self.phase]()

    ######################## Phase Processing ################################
    def phase0(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_0_IDEAS", age_key="COMPUTED_DAYS_IN_STAGE_0_IDEAS")

    def phase1(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_1_CHARTERING", age_key="COMPUTED_DAYS_IN_STAGE_1_CHARTERING")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE", age_key="COMPUTED_AGE_DAYS")

    def phase2(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_2_COMMITTED", age_key="COMPUTED_DAYS_IN_STAGE_2_COMMITTED")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE",
                                                    age_key="COMPUTED_AGE_DAYS")

    def phase3(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS", age_key="COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE",
                                                    age_key="COMPUTED_AGE_DAYS")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_IN_PROGRESS_DATE",
                                                    age_key="COMPUTED_IN_PROGRESS_AGE_DAYS")

    def phase4(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_4_ON_HOLD", age_key="COMPUTED_DAYS_IN_STAGE_4_ON_HOLD")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE",
                                                    age_key="COMPUTED_AGE_DAYS")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_IN_PROGRESS_DATE",
                                                    age_key="COMPUTED_IN_PROGRESS_AGE_DAYS")

    def phase5(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_5_ROLLOUT", age_key="COMPUTED_DAYS_IN_STAGE_5_ROLLOUT")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_IN_PROGRESS_DATE",
                                                    age_key="COMPUTED_IN_PROGRESS_AGE_DAYS")
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE",
                                                    age_key="COMPUTED_AGE_DAYS")

    def phase6(self):
        self._date_in_phase(key="COMPUTED_DATE_IN_STAGE_6_COMPLETED", age_key="COMPUTED_DAYS_IN_STAGE_6_COMPLETED")
        if self.params_dict["COMPUTED_PROJECT_END_DATE"] is None:
            # First time we processed file since project phase changed to completed
            self.params_dict["COMPUTED_PROJECT_END_DATE"] = StringLine(key="COMPUTED_PROJECT_END_DATE",
                                                                       value=today_date_obj,
                                                                       new=True)
        self._project_activity_class_start_date_age(date_key="COMPUTED_PROJECT_START_DATE",
                                                    age_key="COMPUTED_AGE_DAYS")
        self._days_between_phases(start_key="COMPUTED_PROJECT_START_DATE",
                                  end_key="COMPUTED_PROJECT_END_DATE",
                                  age_key="COMPUTED_COMPLETION_TIME_DAYS")
        self._days_between_phases(start_key="COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS",
                                  end_key="COMPUTED_PROJECT_END_DATE",
                                  age_key="COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS")
        self._days_between_phases(start_key="COMPUTED_DATE_IN_STAGE_2_COMMITTED",
                                  end_key="COMPUTED_PROJECT_END_DATE",
                                  age_key="COMPUTED_COMMIT_TO_COMPLETION_DAYS")
        self._days_between_phases(start_key="COMPUTED_DATE_IN_STAGE_1_CHARTERING",
                                  end_key="COMPUTED_PROJECT_END_DATE",
                                  age_key="COMPUTED_CHARTER_TO_COMPLETION_DAYS")
        if (self.params_dict["COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"] is not None and
                self.params_dict["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is not None):
            days = (self.params_dict["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"].int_value -
                    self.params_dict["COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"].int_value)
            if (self.params_dict["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] is None or
                    self.params_dict["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] == 0):
                # First time we processed file since project phase changed to completed
                self.params_dict["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] = StringLine(
                    key="COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS",
                    value=days,
                    new=True)

    ###################### Phase Functions Helpers ##########################
    def _days_between_phases(self, start_key=None, end_key=None, age_key=None):
        if self.params_dict[start_key] is not None and self.params_dict[end_key] is not None:
            start_date = self.params_dict[start_key].date_value
            end_date = self.params_dict[end_key].date_value
            try:
                dt_delta = end_date - start_date
            except TypeError as e:
                logging.error(
                    f"TypeError in computing days between {start_key}={self.params_dict[start_key].value} and "
                    f"{end_key}={self.params_dict[end_key].value} for project {self.project}")
                raise TypeError(e)
            else:
                if self.params_dict[age_key] is None or self.params_dict[age_key] == 0:
                    # First time we processed file since project phase changed to active
                    self.params_dict[age_key] = StringLine(key=age_key,
                                                           value=int(dt_delta.days),
                                                           new=True)

    def _date_in_phase(self, key=None, age_key=None):
        if self.params_dict[key] and self.params_dict[key].date_value is not None:
            self._new_or_update_days(key, age_key)
        else:
            # First time we processed file since project phase changed
            self.params_dict[key] = StringLine(key=key, value=today_date_obj, new=True)
        if self.params_dict["COMPUTED_PREVIOUS_PHASE"].existing_variable_updated:
            # Phase has changed since last time we processed file
            # determine the date_key and age_key for previous phase
            prev_date_key = ("COMPUTED_DATE_IN_STAGE_" + self.previous_phase.split("-")[0]
                             + "_" + self.previous_phase.split("-")[1].replace(" ", "_").upper())
            prev_age_key = ("COMPUTED_DAYS_IN_STAGE_" + self.previous_phase.split("-")[0]
                            + "_" + self.previous_phase.split("-")[1].replace(" ", "_").upper())
            logging.debug(f"Current phase keys: {key}, {age_key}")
            logging.debug(f"Previous phase keys: {prev_date_key}, {prev_age_key}")
            logging.debug(f"Previous phase: {self.previous_phase}")
            logging.debug(f"Current date: {today_date_obj}")
            self._new_or_update_days(prev_date_key, prev_age_key)


    def _new_or_update_days(self, key, age_key):
        phase_start_date = self.params_dict[key].date_value
        dt_delta = today_date_obj - phase_start_date
        logging.debug(f"Phase start date: {phase_start_date}, Today: {today_date_obj}, Delta days: {dt_delta.days}")
        logging.debug(f"Age key: {age_key}, Current age days: {self.params_dict[age_key]}")
        if age_key is not None:
            if self.params_dict[age_key] is None:
                # First time we processed file since project phase changed date added
                self.params_dict[age_key] = StringLine(key=age_key,
                                                       value=int(dt_delta.days),
                                                       new=True)
            else:
                # Update the age days if the phase start date has changed
                if dt_delta.days != self.params_dict[age_key].int_value:
                    self.params_dict[age_key].update_value(int(dt_delta.days))
                    logging.info(f"Updated {key} age days for project {self.project} to {dt_delta.days} days.")
        else:
            raise ValueError(f"Age_key is None for key: {key}, no metrics added or updated")

    def _project_activity_class_start_date_age(self, date_key=None, age_key=None):
        # Active projects can start in any of phase 1, 2, 3, 4, or 5
        # In Progress - Active projects can start in any of phase 3, 4, or 5
        if self.params_dict[date_key] is None:
            # First time we processed file since project phase changed to active
            self.params_dict[date_key] = StringLine(key=date_key,
                                                    value=today_date_obj,
                                                    new=True)
        else:
            project_start_date = self.params_dict[date_key].date_value
            dt_delta = today_date_obj - project_start_date
            if self.params_dict[age_key] is None:
                # First time we processed file since project phase changed to active
                self.params_dict[age_key] = StringLine(key=age_key,
                                                       value=int(dt_delta.days),
                                                       new=True)
            else:
                # Update the age days if the project start date has changed
                if dt_delta.days != self.params_dict[age_key].int_value:
                    self.params_dict[age_key].update_value(int(dt_delta.days))
                    logging.info(f"Updated {date_key} age days for project {self.project} to {dt_delta.days} days.")

    ##########################################################################
    def setup_special_fields(self):
        """
        Executes the setup process for initializing and updating specific fields in the object.

        This method performs a sequence of operations to configure particular fields within the
        object by calling helper methods. Every helper method invoked is responsible for setting
        or updating a specific property or association relevant to the object.

        """
        self.set_uuid()
        self.record_timestamp()
        self.determine_phase_change()
        self.set_charter_and_project_info_link()

    def set_charter_and_project_info_link(self):
        """
        Sets or updates the charter link and project information link in the parameter dictionary.

        This method creates and sets the appropriate charter and project information links for the current project
        by using specific base paths and filenames. If no charter link is found, it logs a warning. If the generated
        links differ from the existing values in the parameter dictionary, the method updates them and logs the changes.

        Args:
            None

        Raises:
            None

        Returns:
            None
        """
        charter_links, link_base = create_charter_link(self.project_root, "refactor me away", self.files)
        if charter_links is None or len(charter_links) == 0:
            logging.warning(f"No charter link found for project {self.project} in {self.project_root}")
        else:
            charter_link = charter_links[0]
            logging.debug(f"{len(charter_links)} found, selected charter link: {charter_link}")
            if "COMPUTED_CHARTER_LINK" not in self.params_dict or self.params_dict["COMPUTED_CHARTER_LINK"] is None:
                self.params_dict["COMPUTED_CHARTER_LINK"] = StringLine(key="COMPUTED_CHARTER_LINK",
                                                               value=charter_link, new=True)
            else:
                if self.params_dict["COMPUTED_CHARTER_LINK"].value != charter_link:
                    self.params_dict["COMPUTED_CHARTER_LINK"].update_value(charter_link)
                    logging.info(f"Updated charter link for project {self.project} to {charter_link}.")

        project_info_link = f"{link_base}{self.project_info_filepath}?web=1"
        if 'COMPUTED_PROJECT_INFO_LINK' not in self.params_dict or self.params_dict['COMPUTED_PROJECT_INFO_LINK'] is None:
            self.params_dict['COMPUTED_PROJECT_INFO_LINK'] = StringLine(key='COMPUTED_PROJECT_INFO_LINK',
                                                                       value=project_info_link, new=True)
        else:
            if self.params_dict['COMPUTED_PROJECT_INFO_LINK'].value != project_info_link:
                self.params_dict['COMPUTED_PROJECT_INFO_LINK'].update_value(project_info_link)
                logging.info(f"Updated project info link for project {self.project} to {project_info_link}.")


    def set_uuid(self):
        """
        Sets the UUID for the instance based on the presence of "Project_ID" in the params_dict.

        If "Project_ID" is not found in the `params_dict` dictionary or its value is `None`, it will be created with a
        randomly generated UUID. The generated or existing UUID will then be set as the instance's `uuid`.

        Args:
            None

        Raises:
            None
        """
        if "Project_ID" not in self.params_dict or self.params_dict["Project_ID"] is None:
            self.params_dict["Project_ID"] = StringLine(key="Project_ID", value=str(uuid.uuid4()), new=True)
        self.uuid = self.params_dict["Project_ID"].value

    def record_timestamp(self):
        """
        Updates or records the current timestamp in the `params_dict` under the "Report_Date" key.

        This method ensures that the "Report_Date" key in the `params_dict` dictionary has the current
        datetime value. If the key does not exist or if its value is `None`, a new `StringLine` object
        is created with the current timestamp as its value. If the key exists, its value is updated
        with the current timestamp.

        Args:
            None

        Returns:
            None
        """
        if "Report_Date" not in self.params_dict or self.params_dict["Report_Date"] is None:
            self.params_dict["Report_Date"] = StringLine(key="Report_Date", value=datetime.now().strftime(DATE_FMT),
                                                         new=True)
        else:
            self.params_dict["Report_Date"].update_value(datetime.now().strftime(DATE_FMT))

    def determine_phase_change(self):
        """
        Analyzes and determines phase changes for a project by comparing the current phase
        with the previously recorded phase. Logs relevant information about phase transitions
        and updates internal tracking structures accordingly.

        Args:
            None

        Raises:
            None
        """
        if "COMPUTED_PREVIOUS_PHASE" not in self.params_dict or self.params_dict["COMPUTED_PREVIOUS_PHASE"] is None:
            self.params_dict["COMPUTED_PREVIOUS_PHASE"] = StringLine(key="COMPUTED_PREVIOUS_PHASE",
                                                                     value=self.phase,
                                                                     new=True)
            logging.info(f"Setting initial phase: {self.phase} for project: {self.project}")
        elif self.phase != self.params_dict["COMPUTED_PREVIOUS_PHASE"].value:
            self.previous_phase = self.params_dict["COMPUTED_PREVIOUS_PHASE"].value
            logging.info(f'Phase has changed: "{self.phase}" -> "{self.previous_phase}" for "{self.project}"')
            self.params_dict["COMPUTED_PREVIOUS_PHASE"].update_value(self.phase)
            new_line = f'{self.previous_phase} -> {self.phase} DATE: {datetime.now().strftime(DATE_FMT)}\n'
            self.params_dict["PHASE_CHANGE"] = StringLine(key="PHASE_CHANGE",
                                                          value=new_line,
                                                          new=True,
                                                          in_reports=False)

    ##########################################################################

    def parse_file(self):
        """
        Parses a project information file line by line and processes its content.

        The method processes a file located in `self.project_root` alongside additional
        metadata inferred from the file path. It updates `self.params_dict` with parsed
        key-value pairs and aggregates lines as needed. Empty lines are skipped, and
        comments are logged, while missing keys are logged as errors. Parsed data is
        based on both specific keys in the file and additional metadata not contained
        within the file.

        Raises:
            FileNotFoundError: If the project information file is not found.
            KeyError: If a required key is missing during parsing.

        Args:
            None

        Returns:
            None
        """
        # Process Project Info file
        projects_processed_counter = 0
        with open(os.path.join(self.project_root, project_info_filename), "r") as project_info_file:
            logging.info(f"Processing file {projects_processed_counter} ({self.project_root})")
            projects_processed_counter += 1
            self.phase, self.project = extract_params(self.project_root)  # harvest parameters from path
            ################################################
            ## Meta parameters not parsed from file
            self.params_dict["Phases"] = StringLine(key="Phases", value=self.phase)
            self.params_dict["Project"] = StringLine(key="Project", value=self.project)

            ################################################
            ## Parse the file line by line
            agg_lines = AggregateLines()
            for line in project_info_file:
                if line.strip() == "":
                    # skip empty lines
                    continue
                obj = StringLine(line)
                if obj.key is not None and obj.key in self.params_dict:
                    self.params_dict[obj.key] = obj
                elif obj.aggregate_key is not None and obj.aggregate_key in self.params_dict:
                    agg_lines.add_line(obj)
                    self.params_dict[obj.aggregate_key] = agg_lines
                elif obj.is_comment:
                    logging.info(f"Comment line found: {obj.line}")
                else:
                    logging.error(f"Key {obj.key} not found in params_dict, line: {line.strip()}")

    def get_legacy_params(self):
        """
        Generates a dictionary of legacy parameters from the current parameters dictionary.

        This method processes each entry in the `params_dict` dictionary, checks the type
        of each line object, and determines if it should be included in the legacy parameters.
        Objects of type `StringLine` or `AggregateLines` are included only if they are marked
        as being in reports. If a line object does not satisfy these conditions, it will
        either be skipped with logging or added directly to the legacy parameters.

        Returns:
            dict: A dictionary containing the legacy parameters based on the criteria above.
        """
        legacy_params = {}
        for key, line_obj in self.params_dict.items():
            if isinstance(line_obj, StringLine) or isinstance(line_obj, AggregateLines):
                if not line_obj.is_in_reports:
                    logging.info(f'In "{self.project_root}": at key={key} line_obj={line_obj} is not in reports')
                    continue
                legacy_params[key] = line_obj.get(key)
            else:
                logging.info(
                    f'In "{self.project_root}": at key={key} line_obj={line_obj} is not a StringLine or AggregateLines')
                legacy_params[key] = line_obj
        return legacy_params

    def finalize_file(self):
        """
        Processes and finalizes the content of a specified project file by performing in-place modifications
        for existing variables and appending new variables at the end of the file if necessary.

        This method checks for updates in a dictionary of parameters and modifies the corresponding lines
        in the project information file. It replaces lines in-place for already existing variables that were
        updated and appends new lines for variables marked as new. The function returns a tuple indicating
        whether any replacements or appends were performed during the process.

        Args:
            None

        Returns:
            Tuple[bool, bool]: A tuple indicating two boolean values:
                - replaced_in_file (bool): True if any existing lines were replaced in the file, False otherwise.
                - appended_in_file (bool): True if any new lines were appended to the file, False otherwise.
        """
        # In place changes
        replaced_in_file = False
        appended_in_file = False
        for line in fileinput.input(os.path.join(self.project_root, project_info_filename), inplace=True):
            for key, obj in self.params_dict.items():
                if isinstance(obj, StringLine) and obj.existing_variable_updated and line.startswith(key):
                    print(f"{obj.line}")
                    replaced_in_file = True
                    break
            else:
                print(line, end='')
        # Append new lines to the file
        with open(os.path.join(self.project_root, project_info_filename), "a") as project_info_file:
            for key, obj in self.params_dict.items():
                if isinstance(obj, StringLine) and obj.add_new_variable:
                    append_in_file = True
                    project_info_file.write(str(obj) + "\n")

        return replaced_in_file, appended_in_file

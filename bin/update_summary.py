import sys
import os
import uuid
import dateutil.utils
from resources import date_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fileinput
import logging
from logging.config import dictConfig
from resources.date_utils import parse_date

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'level': 'DEBUG',
            'filename': 'update_summary.log',
            'mode': 'a',
            'encoding': 'utf-8',
            'maxBytes': 900000,
            'backupCount': 3
        }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['file']
    }
})

from reports.parser import *
from reports.summary import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.environ['PYTHONPATH']
datetime_today = dateutil.utils.today()

# TODO: Document current outputs and compare against MetricsDefinition.csv to identify needs
if __name__ == "__main__":
    logging.info("Starting update_summary.py")

    os.chdir(projects_tree_root)
    logging.info(f"Current directory: {os.getcwd()}")

    project_records_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue
        new_project_start_date = None
        new_project_end_date = None
        new_project_in_progress_date = None
        new_days_progress_to_close = None
        new_completion_time_days = None
        new_completion_time_minus_hold = None
        new_commit_to_completion_days = None
        new_charter_to_completion_days = None

        # Process Project Info file
        with open(os.path.join(root, project_info_filename), "r") as project_info_file:
            logging.info(f"Processing file {projects_processed_counter} ({root})")
            projects_processed_counter += 1
            phase, project = extract_params(root)  # harvest parameters from path
            print(phase)
            print(project)
            logging.info(f"Phase: {phase}, Project: {project}")
            params = parse_project_info(project_info_file)
            params["Phases"] = phase
            params["Project"] = project

            print(f"Processing file {projects_processed_counter} ({phase}: {project})")

            params["Project Folder"] = synthesize_sharepoint_url(phase, project)
            params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"]) + "\n\n"
            if isinstance(params["COMMIT_JUSTIFICATIONS"], list) and len(params["COMMIT_JUSTIFICATIONS"]) > 0:
                # Concatenated in order they appear
                params["COMMIT_JUSTIFICATIONS"] = " ".join(params["COMMIT_JUSTIFICATIONS"]) + "\n\n"
            else:
                params["COMMIT_JUSTIFICATIONS"] = "Commit justification required!\n\n"

            # #############################################################################################
            # Compute derived values for timing of phases
            # Phase changed?
            # params["COMPUTED_PREVIOUS_PHASE"] can be [None, stage = stage, stage /= stage
            # TODO: Evaluate stage dates as a dict and return key of chronologically previous value
            # TODO: Add current stage start date?
            if params["COMPUTED_PREVIOUS_PHASE"] is None:
                params["COMPUTED_PREVIOUS_PHASE"] = phase

            record_timestamp(root, project_info_filename)

            if project_phases[phase] >= 6:
                # Completed projects
                if params["COMPUTED_PROJECT_END_DATE"] is None:
                    # First time we processed file since project phase changed to completed
                    params["COMPUTED_PROJECT_END_DATE"] = datetime_today
                    new_project_end_date = params["COMPUTED_PROJECT_END_DATE"]
                else:
                    date_today = datetime.strptime(
                        params["COMPUTED_PROJECT_END_DATE"][:10],
                        DATE_FMT)

            if project_phases[phase] >= 3:
                # In Progress projects
                if params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] is None:
                    # First time we processed file since project phase changed to In Progress
                    project_in_progress_date = datetime.now()
                    print(f'121 in_progress: {repr(project_in_progress_date)}')
                    print(f'121 in_progress type: {type(project_in_progress_date)}')
                    print(f'121 date_today: {repr(date_today)}')
                    print(f'121 date_today type: {type(date_today)}')
                    params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] = project_in_progress_date.strftime(DATE_FMT)
                    new_project_in_progress_date = project_in_progress_date
                else:
                    # project_in_progress_date = params["COMPUTED_PROJECT_IN_PROGRESS_DATE"]
                    project_in_progress_date = datetime.strptime(
                        params["COMPUTED_PROJECT_IN_PROGRESS_DATE"], '%Y-%m-%d'
                    )
                    print(f'121 in_progress: {repr(project_in_progress_date)}')
                    print(f'121 in_progress type: {type(project_in_progress_date)}')
                    print(f'121 date_today: {repr(date_today)}')
                    print(f'121 date_today type: {type(date_today)}')

                    dt_delta = datetime.now() - project_in_progress_date
                    print(f'131 dt_delta: {repr(dt_delta)}')
                    print(f'131 dt_delta type: {type(dt_delta)}')
                    if dt_delta.days < 0:
                        dt_delta = timedelta(days=0)
                    params["COMPUTED_IN_PROGRESS_AGE_DAYS"] = dt_delta.days

            if project_phases[phase] >= 1:
                # Chartering - Active projects
                if params["COMPUTED_PROJECT_START_DATE"] is None:
                    # First time we processed file since project phase changed to active
                    project_start_date = datetime.now()
                    params["COMPUTED_PROJECT_START_DATE"] = project_start_date.strftime(DATE_FMT)
                    new_project_start_date = project_start_date
                else:
                    project_start_date = datetime.strptime(
                        params["COMPUTED_PROJECT_START_DATE"][:10],
                        DATE_FMT)
                    dt_delta = date_today - project_start_date
                    params["COMPUTED_AGE_DAYS"] = dt_delta.days

            # COMPUTED_COMPLETION_TIME_DAYS
            if (params["COMPUTED_PROJECT_END_DATE"] is not None and
                    params["COMPUTED_PROJECT_START_DATE"] is not None):
                end_date = datetime.strptime(params["COMPUTED_PROJECT_END_DATE"][:10], DATE_FMT)
                start_date = datetime.strptime(params["COMPUTED_PROJECT_START_DATE"][:10], DATE_FMT)
                if params["COMPUTED_COMPLETION_TIME_DAYS"] is None:
                    completion_time_days = (end_date - start_date).days
                    params["COMPUTED_COMPLETION_TIME_DAYS"] = completion_time_days
                    new_completion_time_days = completion_time_days
                else:
                    completion_time_days = params["COMPUTED_COMPLETION_TIME_DAYS"]
                    params["COMPUTED_COMPLETION_TIME_DAYS"] = completion_time_days
            else:
                logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_DAYS")

            # COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS
            if (params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is None and
                    params["COMPUTED_PROJECT_END_DATE"] is not None and
                    params["COMPUTED_PROJECT_START_DATE"] is not None):
                end_date = datetime.strptime(params["COMPUTED_PROJECT_END_DATE"][:10], DATE_FMT)
                in_progress_date = datetime.strptime(params["COMPUTED_PROJECT_IN_PROGRESS_DATE"][:10], DATE_FMT)
                days_progress_to_complete = (end_date - in_progress_date).days
                params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] = days_progress_to_complete
                new_days_progress_to_close = params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"]
            elif params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is not None:
                days_progress_to_complete = params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"]
                params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] = days_progress_to_complete
            else:
                logging.info('Project does not have both a start date and end date')

            # COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS
            if (params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is not None and
                    params["COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"] is not None):
                if params["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] is None:
                    completion_time_minus_hold = (
                            params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] - params[
                        "COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"]).days
                    params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] = completion_time_minus_hold.strftime(DATE_FMT)
                    new_completion_time_minus_hold = completion_time_minus_hold
                else:
                    completion_time_minus_hold = datetime.strptime(
                        params["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"][:10], DATE_FMT)
                    params["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] = completion_time_minus_hold
            else:
                logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS")

            # COMPUTED_COMMIT_TO_COMPLETION_DAYS
            if (params["COMPUTED_PROJECT_END_DATE"] is not None and
                    params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"] is not None):
                if params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"] is None:
                    commit_to_completion_days = (
                            params["COMPUTED_PROJECT_END_DATE"] - params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"]).days
                    params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"] = commit_to_completion_days.strftime(DATE_FMT)
                    new_commit_to_completion_days = commit_to_completion_days
                else:
                    commit_to_completion_days = datetime.strptime(
                        params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"][:10], DATE_FMT)
                    params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"] = commit_to_completion_days
            else:
                logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS")

            # COMPUTED_CHARTER_TO_COMPLETION_DAYS
            if (params["COMPUTED_PROJECT_END_DATE"] is not None and
                    params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"] is not None):
                if params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"] is None:
                    charter_to_completion_days = (
                            params["COMPUTED_PROJECT_END_DATE"] - params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"]).days
                    params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"] = charter_to_completion_days.strftime(DATE_FMT)
                    new_charter_to_completion_days = charter_to_completion_days
                else:
                    charter_to_completion_days = datetime.strptime(
                        params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"][:10], DATE_FMT)
                    params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"] = charter_to_completion_days
            else:
                logging.info("Missing values needed to Compute COMPUTED_CHARTER_TO_COMPLETION_DAYS")

            if params["Project_ID"] is None:
                project_id = uuid.uuid1()
                params["Project_ID"] = project_id
            else:
                project_id = params["Project_ID"]


            def write_to_project_info(root, project_info_filename, key, value):
                """
                Write a key and value pair to the file.

                Args:
                    root (str): The root directory for the file.
                    project_info_filename (str): The name of the file where data will be written.
                    key (str): The key being written.
                    value (str): The value being written.
                """
                with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                    project_info_file.write(f"{key}: {value}\n")
                logging.info(f"project_info_file.write: key == {repr(key)}, value == {repr(value)}")
                logging.info(f"Wrote {key}: {value} to {project_info_filename}")


            def compute_stage_date(params, root, project_info_filename, stage_key):
                """
                Compute the date for a given stage key in the params dictionary.

                Args:
                    params (dict): The dictionary holding stage data.
                    root (str): The root directory for the file.
                    project_info_filename (str): The name of the file where data will be written.
                    stage_key (str): The key for the current stage date (e.g., "COMPUTED_DATE_IN_STAGE_X").

                Returns:
                    datetime.datetime: The computed or existing stage date.
                """
                if params[stage_key] is None:
                    # Set the current date for the stage
                    stage_date = datetime.now()
                    params[stage_key] = stage_date.strftime(DATE_FMT)

                    # Write the new computed date to the file
                    write_to_project_info(root, project_info_filename, stage_key, stage_date.strftime(DATE_FMT))

                    return stage_date
                else:
                    # Parse the existing date from the params
                    stage_date = datetime.strptime(params[stage_key][:10], DATE_FMT)
                    logging.info(f"Existing date for {stage_key}: {stage_date}")

                    return stage_date

            # TODO: Modify to overwrite values if new value is greater
            # def compute_stage_age(params, root, project_info_filename, stage_key_date, stage_key_age):
            #     """
            #     Compute the age in days for a given stage key in the params dictionary.
            #
            #     Args:
            #         params (dict): The dictionary holding stage data.
            #         root (str): The root directory for the file.
            #         project_info_filename (str): The name of the file where data will be written.
            #         stage_key_date (str): The key for the stage date (e.g., "COMPUTED_DATE_IN_STAGE_X").
            #         stage_key_age (str): The key for the stage age in days (e.g., "COMPUTED_DAYS_IN_STAGE_X").
            #
            #     Returns:
            #         int: The computed or existing stage age in days.
            #     """
            #     # logging.info(f'fn param stage_key_date == {repr(stage_key_date)}')
            #     # logging.info(f'fn param stage_key_age == {repr(stage_key_age)}')
            #     stage_date_str = params.get(stage_key_date)
            #     # logging.info(f'stage_date_str == {repr(stage_date_str)}')
            #     current_date = date.today()
            #
            #     if stage_date_str:
            #         stage_date = datetime.datetime.strptime(stage_date_str, DATE_FMT).date()
            #         logging.info(f'stage_date == {repr(stage_date)}')
            #
            #         if params[stage_key_age] is None:
            #             if stage_date <= current_date:
            #                 stage_age = (current_date - stage_date).days
            #                 logging.info(f'stage_age == {repr(stage_age)}')
            #                 params[stage_key_age] = stage_age
            #
            #                 # Write the computed age to the file
            #                 # logging.info(
            #                 #     f'root == {repr(root)},'
            #                 #     f' project_info_filename == {repr(project_info_filename)},'
            #                 #     f' stage_key_age == {repr(stage_key_age)},'
            #                 #     f' stage_age == {repr(stage_key_age)}'
            #                 # )
            #                 write_to_project_info(root, project_info_filename, stage_key_age, stage_age)
            #
            #                 return stage_age
            #             elif stage_date > current_date:
            #                 logging.info(f"Date associated with stage is in the future: {stage_date}")
            #         else:
            #             # Return the existing age value
            #             # logging.info(f'params[stage_key_age] == {repr(params[stage_key_age])}')
            #             stage_age = params[stage_key_age]
            #             # logging.info(f'stage_age == {repr(stage_age)}')
            #             # logging.info(f"Existing age for {stage_key_age}: {stage_age}")
            #             # logging.info(
            #             #     f'root == {repr(root)},'
            #             #     f' project_info_filename == {repr(project_info_filename)},'
            #             #     f' stage_key_age == {repr(stage_key_age)},'
            #             #     f' stage_age == {repr(stage_key_age)}'
            #             # )
            #             return stage_age
            #     else:
            #         logging.warning(f"Unable to compute age: Missing date for {stage_key_date}")
            #         return None

        # TODO: Write statement to capture first stage. Fist stage should reflect start date
        #           This can be done my taking minimum value in stage date dict

        # TODO: IF previous stage is hold, and if var`off_hold_date` is null then datetime.datetime.now()
        #   Wont work for multiple holds

        # TODO: replace `else: stage_#_date` with existing computed date where possible
        #   e.g.: stage_3_date = datetime.datetime.strptime(
        #                         params["COMPUTED_PROJECT_IN_PROGRESS_DATE"][:10],
        #                         DATE_FMT)

        # Update the project info file with the previous phase
        if project_phases[phase] == 0:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_0_IDEAS"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_0_IDEAS"
            stage_0_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():

                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 1:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_1_CHARTERING"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_1_CHARTERING"
            stage_1_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    print(f'376 initial_phase_date: {repr(date_today)}')
                    print(f'376 initial_phase_date: {type(date_today)}')
                    print(f'376 date_today: {repr(date_today)}')
                    print(f'376 date_today: {type(date_today)}')
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 2:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_2_COMMITTED"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_2_COMMITTED"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 2:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_2_COMMITTED"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_2_COMMITTED"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 3:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 4:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_4_ON_HOLD"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 5:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_5_ROLLOUT"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_5_ROLLOUT"]
            parameter_date_key_date = parse_date(parameter_date_key_verbose, 'date')
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')
            # print(f'428 parameter_date_key_date: {repr(parameter_date_key_date)}')
            # print(f'428 parameter_date_key_date type: {type(parameter_date_key_date)}')
            # print(f'428 parameter_date_key_datetime: {repr(parameter_date_key_datetime)}')
            # print(f'428 parameter_date_key_datetime type: {type(parameter_date_key_datetime)}')
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_5_ROLLOUT"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            # if params[f'{parameter_date_key}'] is not None:
            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

                # if initial_phase_date <= datetime_today:
                #     compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                # else:
                #     logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 6:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_6_COMPLETED"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_6_COMPLETED"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = datetime.strptime(params[f'{parameter_date_key}'], '%Y-%m-%d').date()
                datetime_today = datetime.now()
                if initial_phase_date <= datetime_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 7:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_7_MAINTENANCE"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                print(f'line 451: {repr(initial_phase_date)}')
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        if project_phases[phase] == 9:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_9_AD_HOC"
            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_9_AD_HOC"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if params[f'{parameter_date_key}'] is not None:
                initial_phase_date = params[f'{parameter_date_key}']
                if initial_phase_date <= date_today.date():
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date, date_today)
                else:
                    logging.warning(f"Negative Delta: {initial_phase_date} is in the future")

        # Old Method of calling funciton that calculates time in stage
        # if project_phases[phase] == 3:
        #     parameter_key = 'COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS'
        #     stage_3_date = compute_stage_date(
        #         params, root, project_info_filename, "COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"
        #     )
        #
        #     stage_3_age = compute_stage_age(
        #         params, root, project_info_filename, "COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS", "COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS"
        #     )

        previous_phase_updated = False
        for line in fileinput.input(os.path.join(root, project_info_filename), inplace=True):
            if line.startswith("COMPUTED_PREVIOUS_PHASE:"):
                print(f'COMPUTED_PREVIOUS_PHASE: {phase}')
                previous_phase_updated = True
            else:
                print(line, end='')

        # If the previous phase was not updated, it didn't exist. So, append it to the end of the file
        if not previous_phase_updated:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PREVIOUS_PHASE: {phase}\n')

        # Update the project info file with time values for phase transitions
        if new_project_start_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_START_DATE: {new_project_start_date.strftime(DATE_FMT)}\n')

        if new_project_in_progress_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_PROJECT_IN_PROGRESS_DATE: {new_project_in_progress_date.strftime(DATE_FMT)}\n')

        if new_project_end_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f'COMPUTED_PROJECT_END_DATE: {new_project_end_date.strftime(DATE_FMT)}\n')

        # if the phase changed, append a generic phase change record to end of the file
        if params["COMPUTED_PREVIOUS_PHASE"] != phase:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'PHASE_CHANGE: {params["COMPUTED_PREVIOUS_PHASE"]} -> {phase} DATE: {datetime.now().strftime(DATE_FMT)}\n')

        if new_days_progress_to_close is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS: {new_days_progress_to_close}\n')

        if new_completion_time_days is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_COMPLETION_TIME_DAYS: {new_completion_time_days}\n')

        if new_completion_time_minus_hold is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS: {new_completion_time_minus_hold}\n')

        if new_commit_to_completion_days is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_COMMIT_TO_COMPLETION_DAYS: {new_commit_to_completion_days}\n')

        if new_charter_to_completion_days is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f'COMPUTED_CHARTER_TO_COMPLETION_DAYS: {new_charter_to_completion_days}\n')

        project_records_list.append(params)
    create_reports(project_records_list)

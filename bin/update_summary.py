import uuid
import fileinput
from datetime import datetime
from logging.config import dictConfig
# Can't remember why I included the sys.path.append(...) line below. Leaving as comment in case it's important
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Project Module(s) Below
from resources.date_utils import parse_date
from reports.parser import *
from reports.summary import *


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

datetime_today = dateutil.utils.today()


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
        new_stage_0_date = None
        new_stage_1_date = None
        new_stage_2_date = None
        new_stage_3_date = None
        new_stage_4_date = None
        new_stage_5_date = None
        new_stage_6_date = None
        new_stage_7_date = None
        new_stage_9_date = None


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

"""
TODO: Scott has this set up as two blocks. The inner block, (e.g. `if project_phases[phase] >= 6:`),
    reads/evaluates PROJECT_INFO.txt and the outer block, (e.g. `if new_project_end_date is not None:`) writes values
    back to the PROJECT_INFO.txt file. The two are separated to avoid reading and writing at the same time. My statements
    are written as part of the inner -- ensure that they are not writing to an open file slash move writes to outer block.
    
"""
            # Scott
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

            # Scott
            if project_phases[phase] >= 3:
                # In Progress projects
                if params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] is None:
                    # First time we processed file since project phase changed to In Progress
                    project_in_progress_date = datetime.now()
                    params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] = project_in_progress_date.strftime(DATE_FMT)
                    new_project_in_progress_date = project_in_progress_date
                else:
                    # project_in_progress_date = params["COMPUTED_PROJECT_IN_PROGRESS_DATE"]
                    project_in_progress_date = datetime.strptime(
                        params["COMPUTED_PROJECT_IN_PROGRESS_DATE"], '%Y-%m-%d'
                    )

                    dt_delta = datetime.now() - project_in_progress_date
                    if dt_delta.days < 0:
                        dt_delta = timedelta(days=0)
                    params["COMPUTED_IN_PROGRESS_AGE_DAYS"] = dt_delta.days

            # Scott
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

            # COMPUTED_COMPLETION_TIME_DAYS KW
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

            # COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS KW
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


            if project_phases[phase] == 0:
                if params["COMPUTED_DATE_IN_STAGE_0_IDEAS"] is None:
                    stage_0_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_0_IDEAS"] = stage_0_date.strftime(DATE_FMT)
                    new_stage_0_date = stage_0_date
                else:
                    stage_0_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_0_IDEAS"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_0_date
                    params["COMPUTED_DAYS_IN_STAGE_0_IDEAS"] = dt_delta.days

            if project_phases[phase] == 1:
                if params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"] is None:
                    stage_1_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"] = stage_1_date.strftime(DATE_FMT)
                    new_stage_1_date = stage_1_date
                else:
                    stage_1_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_1_date
                    params["COMPUTED_DAYS_IN_STAGE_1_CHARTERING"] = dt_delta.days

            if project_phases[phase] == 2:
                if params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"] is None:
                    stage_2_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"] = stage_2_date.strftime(DATE_FMT)
                    new_stage_2_date = stage_2_date
                else:
                    stage_2_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_2_date
                    params["COMPUTED_DAYS_IN_STAGE_2_COMMITTED"] = dt_delta.days

            if project_phases[phase] == 3:
                if params["COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"] is None:
                    stage_3_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"] = stage_3_date.strftime(DATE_FMT)
                    new_stage_3_date = stage_3_date
                else:
                    stage_3_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_3_date
                    params["COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS"] = dt_delta.days

            if project_phases[phase] == 4:
                if params["COMPUTED_DATE_IN_STAGE_4_ON_HOLD"] is None:
                    stage_4_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_4_ON_HOLD"] = stage_4_date.strftime(DATE_FMT)
                    new_stage_4_date = stage_4_date
                else:
                    stage_4_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_4_ON_HOLD"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_4_date
                    params["COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"] = dt_delta.days

            if project_phases[phase] == 5:
                if params["COMPUTED_DATE_IN_STAGE_5_ROLLOUT"] is None:
                    stage_5_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_5_ROLLOUT"] = stage_5_date.strftime(DATE_FMT)
                    new_stage_5_date = stage_5_date
                else:
                    stage_5_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_5_ROLLOUT"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_5_date
                    params["COMPUTED_DAYS_IN_STAGE_5_ROLLOUT"] = dt_delta.days

            if project_phases[phase] == 6:
                if params["COMPUTED_DATE_IN_STAGE_6_COMPLETED"] is None:
                    stage_6_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_6_COMPLETED"] = stage_6_date.strftime(DATE_FMT)
                    new_stage_6_date = stage_6_date
                else:
                    stage_6_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_6_COMPLETED"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_6_date
                    params["COMPUTED_DAYS_IN_STAGE_6_COMPLETED"] = dt_delta.days

            if project_phases[phase] == 7:
                if params["COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"] is None:
                    stage_7_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"] = stage_7_date.strftime(DATE_FMT)
                    new_stage_7_date = stage_7_date
                else:
                    stage_7_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_7_date
                    params["COMPUTED_DAYS_IN_STAGE_7_MAINTENANCE"] = dt_delta.days

            if project_phases[phase] == 9:
                if params["COMPUTED_DATE_IN_STAGE_9_AD_HOC"] is None:
                    stage_9_date = datetime.now()
                    params["COMPUTED_DATE_IN_STAGE_9_AD_HOC"] = stage_9_date.strftime(DATE_FMT)
                    new_stage_9_date = stage_9_date
                else:
                    stage_9_date = datetime.strptime(
                        params["COMPUTED_DATE_IN_STAGE_9_AD_HOC"][:10],
                        DATE_FMT)
                    dt_delta = date_today - stage_9_date
                    params["COMPUTED_DAYS_IN_STAGE_9_AD_HOC"] = dt_delta.days



        # Update the project info file with the previous phase
        if project_phases[phase] == 0:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_0_IDEAS"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_0_IDEAS"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_0_IDEAS"
            stage_0_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 1:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_1_CHARTERING"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_1_CHARTERING"
            stage_1_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 2:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_2_COMMITTED"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_2_COMMITTED"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 3:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS"
            stage_3_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 4:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_4_ON_HOLD"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_4_ON_HOLD"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"
            stage_4_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 5:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_5_ROLLOUT"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_5_ROLLOUT"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_5_ROLLOUT"
            stage_2_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 6:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_6_COMPLETED"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_6_COMPLETED"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_6_COMPLETED"
            stage_6_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 7:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_7_MAINTENANCE"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_7_MAINTENANCE"
            stage_7_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

        if project_phases[phase] == 9:
            parameter_date_key = "COMPUTED_DATE_IN_STAGE_9_AD_HOC"
            parameter_date_key_verbose = params["COMPUTED_DATE_IN_STAGE_9_AD_HOC"]
            parameter_date_key_datetime = parse_date(parameter_date_key_verbose, 'datetime')

            parameter_age_key = "COMPUTED_DAYS_IN_STAGE_9_AD_HOC"
            stage_9_date = compute_stage_date(params, root, project_info_filename, parameter_date_key)

            if parameter_date_key_datetime is not None:
                initial_phase_date = parameter_date_key_datetime
                try:
                    compute_phase_dwell(root, project_info_filename, parameter_age_key, initial_phase_date)
                except ValueError as e:
                    print(f'compute_phase_dwell(initial_phase_date): {repr(initial_phase_date)}')
                    print(f'compute_phase_dwell(initial_phase_date) type: {type(initial_phase_date)}')
                    logging.error(f"Error parsing date")

# TODO: Combine `previous_phase_updated` & `previous_phase_updated`
        previous_phase_updated = False
        for line in fileinput.input(os.path.join(root, project_info_filename), inplace=True):
            if line.startswith("COMPUTED_PREVIOUS_PHASE:"):
                print(f'COMPUTED_PREVIOUS_PHASE: {phase}')
                previous_phase_updated = True
            else:
                print(line, end='')

        # If the previous phase was not updated, it didn't exist. So, append it to the end of the file
        previous_phase_updated:
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

        if new_stage_0_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_0_IDEAS: {new_stage_0_date.strftime(DATE_FMT)}\n")
        
        if new_stage_1_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_1_CHARTERING: {new_stage_1_date.strftime(DATE_FMT)}\n")

        if new_stage_2_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_2_COMMITTED: {new_stage_2_date.strftime(DATE_FMT)}\n")

        if new_stage_3_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS: {new_stage_3_date.strftime(DATE_FMT)}\n")

        if new_stage_4_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_4_ON_HOLD: {new_stage_4_date.strftime(DATE_FMT)}\n")

        if new_stage_5_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_5_ROLLOUT: {new_stage_5_date.strftime(DATE_FMT)}\n")

        if new_stage_6_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_6_COMPLETED: {new_stage_6_date.strftime(DATE_FMT)}\n")

        if new_stage_7_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_7_MAINTENANCE: {new_stage_7_date.strftime(DATE_FMT)}\n")

        if new_stage_9_date is not None:
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(
                    f"COMPUTED_DATE_IN_STAGE_9_AD_HOC: {new_stage_9_date.strftime(DATE_FMT)}\n")

        project_records_list.append(params)
        create_reports(project_records_list)

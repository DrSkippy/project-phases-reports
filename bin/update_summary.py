#!/usr/bin/env -S poetry run python
import sys
import os
import uuid
import fileinput
from datetime import datetime
from logging.config import dictConfig

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # enables import of modules from resources
# Import Project Module(s) Below
from resources.date_utils import parse_date, days_between_dates
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

def process_project_directory(root, dirs, files):

    date_today = datetime.now()
    new_project_start_date = None
    new_project_end_date = None
    new_project_in_progress_date = None
    new_days_progress_to_close = None
    new_completion_time_days = None
    new_completion_time_minus_hold = None
    new_commit_to_completion_days = None
    new_charter_to_completion_days = None

    # funtion to handle `if project_phases[phase] == n` logic
    def update_stage(params, phase_to_check, current_phase, date_key, age_key, date_today, special_case=None):
        new_date = None
        new_age = None

        if current_phase != phase_to_check:
            return new_date, new_age

        # Special case for stage 3
        if special_case == "stage_3":
            if params[date_key] is None:
                if params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] is None:
                    stage_date = datetime.now()
                    params[date_key] = stage_date.strftime(DATE_FMT)
                    new_date = stage_date
                else:
                    stage_date = datetime.strptime(params["COMPUTED_PROJECT_IN_PROGRESS_DATE"][:10], DATE_FMT)
                    params[date_key] = stage_date.strftime(DATE_FMT)
                    new_date = stage_date
            else:
                stage_date = datetime.strptime(params[date_key][:10], DATE_FMT)
                dt_delta = days_between_dates(stage_date, date_today)
                params[age_key] = dt_delta
                new_age = dt_delta
            return new_date, new_age

        # Generic logic for non-stage 3 stages
        if params[date_key] is None:
            stage_date = datetime.now()
            params[date_key] = stage_date.strftime(DATE_FMT)
            new_date = stage_date
        else:
            stage_date = datetime.strptime(params[date_key][:10], DATE_FMT)
            dt_delta = date_today - stage_date
            params[age_key] = dt_delta.days if hasattr(dt_delta, "days") else dt_delta
            new_age = params[age_key]
        return new_date, new_age


    with open(os.path.join(root, project_info_filename), "r") as project_info_file:
        phase, project = extract_params(root)
        params = parse_project_info(project_info_file)
        params["Phases"] = phase
        params["Project"] = project
        params["CharterLink"] = create_charter_link(root, dirs, files)
        print(f"Processing project ({phase}: {project}) in {root}")
        params["Project Folder"] = synthesize_sharepoint_url(phase, project)
        params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"]) + "\n\n"
        if isinstance(params["COMMIT_JUSTIFICATIONS"], list) and len(params["COMMIT_JUSTIFICATIONS"]) > 0:
            params["COMMIT_JUSTIFICATIONS"] = " ".join(params["COMMIT_JUSTIFICATIONS"]) + "\n\n"
        else:
            params["COMMIT_JUSTIFICATIONS"] = "Commit justification required!\n\n"


        # params["COMPUTED_PREVIOUS_PHASE"] can be [None, stage = stage, stage /= stage
        if params["COMPUTED_PREVIOUS_PHASE"] is None:
            params["COMPUTED_PREVIOUS_PHASE"] = phase

        record_timestamp(root, project_info_filename)

        # Scott
        if project_phases[phase] >= 6:
            # Completed projects
            if params["COMPUTED_PROJECT_END_DATE"] is None:
                # First time we processed file since project phase changed to completed
                params["COMPUTED_PROJECT_END_DATE"] = datetime_today
                new_project_end_date = params["COMPUTED_PROJECT_END_DATE"]
            else:
                date_today = datetime.strptime(
                    params["COMPUTED_PROJECT_END_DATE"][:10], DATE_FMT)  #

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
            end_date = parse_date(params["COMPUTED_PROJECT_END_DATE"], 'datetime')
            start_date = parse_date(params["COMPUTED_PROJECT_START_DATE"], 'datetime')
            if params["COMPUTED_COMPLETION_TIME_DAYS"] is None:
                completion_time_days = (end_date - start_date).days
                params["COMPUTED_COMPLETION_TIME_DAYS"] = completion_time_days
                new_completion_time_days = completion_time_days
        else:
            logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_DAYS")

        # COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS KW
        if (params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is None and
                params["COMPUTED_PROJECT_END_DATE"] is not None and
                params["COMPUTED_PROJECT_START_DATE"] is not None):
            end_date = parse_date(params["COMPUTED_PROJECT_END_DATE"], 'datetime')
            in_progress_date = parse_date(params["COMPUTED_PROJECT_IN_PROGRESS_DATE"], 'datetime')
            days_progress_to_complete = (end_date - in_progress_date).days
            params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] = days_progress_to_complete
            new_days_progress_to_close = params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"]
        else:
            logging.info('Project does not have both a start date and end date')

        # COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS
        if (params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] is not None and
                params["COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"] is not None):
            if params["COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS"] is None:
                completion_time_minus_hold = (
                        params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] - params[
                    "COMPUTED_DAYS_IN_STAGE_4_ON_HOLD"]).days
                params["COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS"] = completion_time_minus_hold.strftime(
                    DATE_FMT)
                new_completion_time_minus_hold = completion_time_minus_hold
        else:
            logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS")

        # COMPUTED_COMMIT_TO_COMPLETION_DAYS
        if (params["COMPUTED_PROJECT_END_DATE"] is not None and
                params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"] is not None):
            if params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"] is None:
                end_date = parse_date(params["COMPUTED_PROJECT_END_DATE"], 'datetime')
                start_date = parse_date(params["COMPUTED_DATE_IN_STAGE_2_COMMITTED"], 'datetime')
                commit_to_completion_days = (end_date - start_date).days
                params["COMPUTED_COMMIT_TO_COMPLETION_DAYS"] = commit_to_completion_days
                new_commit_to_completion_days = commit_to_completion_days
        else:
            logging.info("Missing values needed to Compute COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS")

        # COMPUTED_CHARTER_TO_COMPLETION_DAYS
        if (params["COMPUTED_PROJECT_END_DATE"] is not None and
                params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"] is not None):
            if params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"] is None:
                end_date = parse_date(params["COMPUTED_PROJECT_END_DATE"], 'datetime')
                start_date = parse_date(params["COMPUTED_DATE_IN_STAGE_1_CHARTERING"], 'datetime')
                charter_to_completion_days = (end_date - start_date).days
                params["COMPUTED_CHARTER_TO_COMPLETION_DAYS"] = charter_to_completion_days
                new_charter_to_completion_days = charter_to_completion_days
        else:
            logging.info("Missing values needed to Compute COMPUTED_CHARTER_TO_COMPLETION_DAYS")

        if params["Project_ID"] is None:
            project_id = uuid.uuid1()
            params["Project_ID"] = project_id
        else:
            project_id = params["Project_ID"]

        new_stage_0_date, new_stage_0_age = update_stage(
            params, 0, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_0_IDEAS", "COMPUTED_DAYS_IN_STAGE_0_IDEAS",
            date_today
        )
        new_stage_1_date, new_stage_1_age = update_stage(
            params, 1, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_1_CHARTERING", "COMPUTED_DAYS_IN_STAGE_1_CHARTERING",
            date_today
        )
        new_stage_2_date, new_stage_2_age = update_stage(
            params, 2, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_2_COMMITTED", "COMPUTED_DAYS_IN_STAGE_2_COMMITTED",
            date_today
        )
        new_stage_3_date, new_stage_3_age = update_stage(
            params, 3, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS", "COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS",
            date_today, special_case="stage_3"
        )
        new_stage_4_date, new_stage_4_age = update_stage(
            params, 4, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_4_ON_HOLD", "COMPUTED_DAYS_IN_STAGE_4_ON_HOLD",
            date_today
        )
        new_stage_5_date, new_stage_5_age = update_stage(
            params, 5, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_5_ROLLOUT", "COMPUTED_DAYS_IN_STAGE_5_ROLLOUT",
            date_today
        )
        new_stage_6_date, new_stage_6_age = update_stage(
            params, 6, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_6_COMPLETED", "COMPUTED_DAYS_IN_STAGE_6_COMPLETED",
            date_today
        )
        new_stage_7_date, new_stage_7_age = update_stage(
            params, 7, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_7_MAINTENANCE", "COMPUTED_DAYS_IN_STAGE_7_MAINTENANCE",
            date_today
        )
        new_stage_9_date, new_stage_9_age = update_stage(
            params, 9, project_phases[phase],
            "COMPUTED_DATE_IN_STAGE_9_AD_HOC", "COMPUTED_DAYS_IN_STAGE_9_AD_HOC",
            date_today
        )


    previous_phase_updated = False
    for line in fileinput.input(os.path.join(root, project_info_filename), inplace=True):
        if line.startswith("COMPUTED_PREVIOUS_PHASE:"):
            print(f'COMPUTED_PREVIOUS_PHASE: {phase}')
            previous_phase_updated = True
        else:
            print(line, end='')

    stage_3_age_updated = False
    if project_phases[phase] == 3 and new_stage_3_age is not None:
        for line in fileinput.input(os.path.join(root, project_info_filename), inplace=True):
            if line.startswith("COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS:"):
                print(f"COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS: {new_stage_3_age}")
                stage_3_age_updated = True
            else:
                print(line, end='')
        if not stage_3_age_updated:
            # Separate `with open()...` block inside if project_phases[phase] == 3 to prevent deleting line with <> 3
            with open(os.path.join(root, project_info_filename), "a") as project_info_file:
                project_info_file.write(f"COMPUTED_DAYS_IN_STAGE_3_IN_PROGRESS: {new_stage_3_age}\n")


    with open(os.path.join(root, project_info_filename), "a") as project_info_file:

        def write_stage_field(project_info_file, value, fieldname, fieldtype):
            if value is not None:
                if fieldtype == "date":
                    project_info_file.write(f"{fieldname}: {value.strftime(DATE_FMT)}\n")
                elif fieldtype == "str":
                     project_info_file.write(f"{fieldname}: {value}\n")
                else:  # age or numeric
                    project_info_file.write(f"{fieldname}: {value}\n")

        stage_fields = [
            (new_days_progress_to_close, 'COMPUTED_IN_PROGRESS_TO_COMPLETION_DAYS', 'int'),
            (new_completion_time_days, 'COMPUTED_COMPLETION_TIME_DAYS', 'int'),
            (new_completion_time_minus_hold, 'COMPUTED_COMPLETION_TIME_MINUS_HOLD_DAYS', 'int'),
            (new_commit_to_completion_days, 'COMPUTED_COMMIT_TO_COMPLETION_DAYS', 'int'),
            (new_charter_to_completion_days, 'COMPUTED_CHARTER_TO_COMPLETION_DAYS', 'int'),
            (new_stage_0_date, 'COMPUTED_DATE_IN_STAGE_0_IDEAS', 'date'),
            (new_stage_1_date, 'COMPUTED_DATE_IN_STAGE_1_CHARTERING', 'date'),
            (new_stage_2_date, 'COMPUTED_DATE_IN_STAGE_2_COMMITTED', 'date'),
            (new_stage_3_date, 'COMPUTED_DATE_IN_STAGE_3_IN_PROGRESS', 'date'),
            (new_stage_4_date, 'COMPUTED_DATE_IN_STAGE_4_ON_HOLD', 'date'),
            (new_stage_5_date, 'COMPUTED_DATE_IN_STAGE_5_ROLLOUT', 'date'),
            (new_stage_6_date, 'COMPUTED_DATE_IN_STAGE_6_COMPLETED', 'date'),
            (new_stage_7_date, 'COMPUTED_DATE_IN_STAGE_7_MAINTENANCE', 'date'),
            (new_stage_9_date, 'COMPUTED_DATE_IN_STAGE_9_AD_HOC', 'date'),
        ]

        for value, fieldname, fieldtype in stage_fields:
            write_stage_field(project_info_file, value, fieldname, fieldtype)

        # If the previous phase was not updated, it didn't exist. So, append it to the end of the file
        if not previous_phase_updated:
            project_info_file.write(f'COMPUTED_PREVIOUS_PHASE: {phase}\n')

        # Update the project info file with time values for phase transitions
        if new_project_start_date is not None:
            project_info_file.write(f'COMPUTED_PROJECT_START_DATE: {new_project_start_date.strftime(DATE_FMT)}\n')

        if new_project_in_progress_date is not None:
            project_info_file.write(
                f'COMPUTED_PROJECT_IN_PROGRESS_DATE: {new_project_in_progress_date.strftime(DATE_FMT)}\n')

        if new_project_end_date is not None:
            project_info_file.write(f'COMPUTED_PROJECT_END_DATE: {new_project_end_date.strftime(DATE_FMT)}\n')

        # if the phase changed, append a generic phase change record to end of the file
        # possible to compute everything from here
        if params["COMPUTED_PREVIOUS_PHASE"] != phase:
            project_info_file.write(
                f'PHASE_CHANGE: {params["COMPUTED_PREVIOUS_PHASE"]} -> {phase} DATE: {datetime.now().strftime(DATE_FMT)}\n'
            )

    return params


def main():
    logging.info("Starting update_summary.py")
    os.chdir(projects_tree_root)
    project_records_list = []
    projects_processed_counter = 0

    for root, dirs, files in os.walk(".", topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue

        params = process_project_directory(root, dirs, files)
        if params is not None:
            project_records_list.append(params)
            projects_processed_counter += 1

    create_reports(project_records_list)
    logging.info("Processing complete.")


if __name__ == "__main__":
    main()


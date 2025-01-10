# USAGE:
#
#   cd /Users/s.hendrickson/Documents/OneDrive - F5, Inc
#   python ~/Working/2023-08-23_project_visibility/bin/update_summary.py
#   cat "./Projects Folders/summary.csv"
#
import logging
from logging.config import dictConfig
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

        # Process Project Info file
        with open(os.path.join(root, project_info_filename), "r") as project_info_file:
            logging.info(f"Processing file {projects_processed_counter} ({root})")
            projects_processed_counter += 1
            phase, project = extract_params(root)  # harvest parameters from path
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
            if params["COMPUTED_PREVIOUS_PHASE"] is None:
                params["COMPUTED_PREVIOUS_PHASE"] = phase

            project_phase_end_date = datetime.datetime.now()  # current last day of unfinished projects

            if project_phases[phase] >= 6:
                # Completed projects
                if params["COMPUTED_PROJECT_END_DATE"] is None:
                    # First time we processed file since project phase changed to completed
                    project_phase_end_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_END_DATE"] = project_phase_end_date.strftime(DATE_FMT)
                    new_project_end_date = project_phase_end_date
                else:
                    project_phase_end_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_END_DATE"][:10],
                        DATE_FMT)

            if project_phases[phase] >= 3:
                # In Progress projects
                if params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] is None:
                    # First time we processed file since project phase changed to In Progress
                    project_in_progress_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_IN_PROGRESS_DATE"] = project_in_progress_date.strftime(DATE_FMT)
                    new_project_in_progress_date = project_in_progress_date
                else:
                    project_in_progress_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_IN_PROGRESS_DATE"][:10],
                        DATE_FMT)
                    dt_delta = project_phase_end_date - project_in_progress_date
                    if dt_delta.days < 0:
                        dt_delta = datetime.timedelta(days=0)
                    params["COMPUTED_IN_PROGRESS_AGE_DAYS"] = dt_delta.days

            if project_phases[phase] >= 1:
                # Chartering - Active projects
                if params["COMPUTED_PROJECT_START_DATE"] is None:
                    # First time we processed file since project phase changed to active
                    project_start_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_START_DATE"] = project_start_date.strftime(DATE_FMT)
                    new_project_start_date = project_start_date
                else:
                    project_start_date = datetime.datetime.strptime(
                        params["COMPUTED_PROJECT_START_DATE"][:10],
                        DATE_FMT)
                    dt_delta = project_phase_end_date - project_start_date
                    params["COMPUTED_AGE_DAYS"] = dt_delta.days

            project_records_list.append(params)

        # Update the project info file with the previous phase
        import fileinput

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
                project_info_file.write(f'PHASE_CHANGE: {params["COMPUTED_PREVIOUS_PHASE"]} -> {phase} DATE:{datetime.datetime.now().strftime(DATE_FMT)}\n')

    create_reports(project_records_list)

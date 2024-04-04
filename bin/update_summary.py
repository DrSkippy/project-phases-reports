# USAGE:
#
#   cd /Users/s.hendrickson/Documents/OneDrive - F5, Inc
#   python ~/Working/2023-08-23_project_visibility/bin/update_summary.py
#   cat "./Project Folders/summary.csv"
#
from reports.parser import *
from reports.summary import *

if __name__ == "__main__":
    os.chdir(projects_tree_root)
    project_records_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
        if project_info_filename not in files or "1-Chartering" not in dirs:
            continue
        new_project_start_date = None
        new_project_end_date = None
        new_project_in_progress_date = None
        # Process Project Info file
        with open(os.path.join(root, project_info_filename), "r") as project_info_file:
            projects_processed_counter += 1
            phase, project = extract_params(root)  # harvest parameters from path
            params = parse_project_info(project_info_file)
            params["Phases"] = phase
            params["Project"] = project

            print(f"Processing file {projects_processed_counter} ({phase}: {project})")

            params["Project Folder"] = synthesize_sharepoint_url(phase, project)
            params["NOTES"] = NOTES_DELIMITER.join(params["NOTES"]) + "\n\n"
            if isinstance(params["COMMIT_JUSTIFICATION"], list) and len(params["COMMIT_JUSTIFICATION"]) > 0:
                # Concatenated in order they appear
                params["COMMIT_JUSTIFICATION"] = " ".join(params["COMMIT_JUSTIFICATION"]) + "\n\n"
            else:
                params["COMMIT_JUSTIFICATION"] = "Commit justification required!\n\n"

            # Compute derived values for timing of phases
            project_end_date = datetime.datetime.now()  # current last day of unfinished projects
            if project_phases[phase] >= 6:
                # Completed projects
                if params["COMPUTED_PROJECT_END_DATE"] is None:
                    # First time we processed file since project phase changed to completed
                    project_end_date = datetime.datetime.now()
                    params["COMPUTED_PROJECT_END_DATE"] = project_end_date.strftime(DATE_FMT)
                    new_project_end_date = project_end_date
                else:
                    project_end_date = datetime.datetime.strptime(
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
                    dt_delta = project_end_date - project_in_progress_date
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
                    dt_delta = project_end_date - project_start_date
                    params["COMPUTED_AGE_DAYS"] = dt_delta.days

            project_records_list.append(params)

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

    create_reports(project_records_list)

#!/usr/bin/env -S poetry run python
__version__ = "2.0.0"

import argparse
import logging
import os
from datetime import datetime
from logging.config import dictConfig

from reports.summary import configure_report_path_globals, create_reports
from resources.project_file import project_info_filename, project_folders_root, ProjectFileObject, set_date_obj

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
            'filename': 'update_summary_v2.log',
            'mode': 'a',
            'encoding': 'utf-8',
            'maxBytes': 1600000,
            'backupCount': 3
        }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['file']
    }
})

if __name__ == "__main__":
    logging.info(f"Starting update_summary Version {__version__}")

    parser = argparse.ArgumentParser(description="Update projects summary script")
    parser.add_argument('--env', choices=['prod', 'test'], default='test',
                        help='Set environment path from environment variables')
    parser.add_argument('--inject-date', type=str, default=None,
                        help='Inject a specific date (YYYY-MM-DD) instead of today\'s date')
    args = parser.parse_args()

    global today_date_obj
    today_date_obj = datetime.today().date()

    if args.env == 'prod':
        projects_tree_root = os.getenv('PROJECT_PHASES_PROD_PROJECTS_FOLDERS_DIRECTORY')
    elif args.env == 'test':
        projects_tree_root = os.getenv('PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY')
        # inject a specific date for testing purposes
        if args.inject_date:
            today_date_obj = datetime.strptime(args.inject_date, '%Y-%m-%d').date()
            logging.info(f"Injected date for testing: {today_date_obj}")
    else:
        raise ValueError("Invalid environment specified. Use 'prod' or 'test'.")
    logging.info(f"Project folders root: {projects_tree_root}")
    set_date_obj(today_date_obj)
    configure_report_path_globals(projects_tree_root, today_date_obj)

    project_objects_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(projects_tree_root, topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue

        proj = ProjectFileObject(root, files, project_info_filename)
        print(f"Processing file {projects_processed_counter: 3} ({proj.phase}: {proj.project})")
        logging.debug(f'Processing root={root}: {str(proj)}')
        project_objects_list.append(proj)
        projects_processed_counter += 1

    logging.info(f"Processed {len(project_objects_list)} projects.")
    create_reports([p.get_legacy_params() for p in project_objects_list])
    res = {obj.uuid: obj.finalize_file() for obj in project_objects_list}
    logging.debug(f"Finalized files: {res}")

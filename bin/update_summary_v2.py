#!/usr/bin/env -S poetry run python
__version__ = "2.0.0"

import argparse
import logging
import os
from logging.config import dictConfig

from reports.summary import configure_report_path_globals, create_reports
from resources.project_file import project_info_filename, project_folders_root, ProjectFileObject

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
    args = parser.parse_args()

    if args.env == 'prod':
        projects_tree_root = os.getenv('PROJECT_PHASES_PROD_PROJECTS_FOLDERS_DIRECTORY')
    elif args.env == 'test':
        projects_tree_root = os.getenv('PROJECT_PHASES_TEST_SNAPSHOT_DIRECTORY')
    else:
        raise ValueError("Invalid environment specified. Use 'prod' or 'test'.")
    logging.info(f"Project folders root: {projects_tree_root}")
    configure_report_path_globals(projects_tree_root)

    project_objects_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(projects_tree_root, topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue

        proj = ProjectFileObject(root, files, project_info_filename)
        logging.debug(f'Processing root={root}: {str(proj)}')
        project_objects_list.append(proj)

    logging.info(f"Processed {len(project_objects_list)} projects.")
    create_reports([p.get_legacy_params() for p in project_objects_list])
    res = {obj.uuid: obj.finalize_file() for obj in project_objects_list}
    logging.debug(f"Finalized files: {res}")

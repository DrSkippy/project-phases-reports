#!/usr/bin/env -S poetry run python
import sys
import os
import uuid
import fileinput
from datetime import datetime
from logging.config import dictConfig

#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # enables import of modules from resources
# Import Project Module(s) Below
from resources.date_utils import parse_date, days_between_dates
from reports.parser import *
from reports.summary import *
from resources.file_object import *


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
    logging.info("Starting update_summary Version 2")

    ### TESTING
    projects_tree_root = "/home/scott/Working/project-phases-reports/tests/projects_snapshot/"
    os.chdir(projects_tree_root)
    logging.info(f"Current directory: {os.getcwd()}")

    project_records_list = []
    project_objects_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue

        proj = ProjectFileObject(root, project_info_filename)
        logging.debug(str(proj))
        project_objects_list.append(proj)

    create_reports([p.get_legacy_params() for p in project_objects_list])

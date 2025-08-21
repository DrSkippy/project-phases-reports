#!/usr/bin/env -S poetry run python
from logging.config import dictConfig

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # enables import of modules from resources
# Import Project Module(s) Below
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
            'filename': 'update_summary_v2.log',
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

    os.chdir(projects_tree_root)
    logging.info(f"Current directory: {os.getcwd()}")

    project_objects_list = []
    projects_processed_counter = 0

    # Walk the file system from the root directory
    for root, dirs, files in os.walk(".", topdown=False):
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

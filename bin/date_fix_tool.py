#!/usr/bin/env -S poetry run python
__version__ = 0.0.1
import logging
import tqdm
import argparse
import os
from datetime import datetime
from reports.configurations import project_info_filename, project_folders_root
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
            'filename': 'date_fix_tool.log',
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

date_re = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
date_seq_re = re.compile(r"\d{4}-\d{1,2}-\d{1,2}-\d{1,2}")  # date with sequence number

def clean_line(line, project_file_name):
    line = line.strip()
    if line.lower().startswith("note"):
        # Fix notes fields
        conforming_head_date = None
        sequence_number = None
        note_line = line.strip()
        try:
            head, tail = note_line.strip().split(":", 1)
        except ValueError:
            try:
                head, tail = note_line.strip().split(";", 1)
            except ValueError:
                try:
                    head, tail = note_line.strip().split(" ", 1)
                    if len(head) > 18:
                        raise ValueError(f"Note head is too long ({head})")
                except ValueError:
                    logging.warning(f"WARN: Note is poorly formed ({note_line}) [{project_file_name}]")
        head = head.replace("_", "-")  # in case someone transposed in typing
        try:
            head_date = date_seq_re.search(head).group(0)
            y, m, d, sequence_number = head_date.split("-")
            conforming_head_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            logging.info(f"Sequence number {sequence_number} found")
        except (ValueError, AttributeError):
            # try again without sequence number
            try:
                head_date = date_re.search(head).group(0)
                y, m, d = head_date.split("-")
                conforming_head_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
            except ValueError:
                logging.error(f"ERROR: Note date is not in yyyy-mm-dd format: {head} [{project_file_name}]")
        try:
            d = datetime.strptime(conforming_head_date, "%Y-%m-%d")
        except ValueError:
            logging.error(f"ERROR: Invalid date ({conforming_head_date}) [{project_file_name}]")

        if sequence_number:
            return f"NOTES_{conforming_head_date}_{sequence_number}: {tail.strip()}"
        else:
            return f"NOTES_{conforming_head_date}: {tail.strip()}"
    return line

if __name__ == "__main__":
    logging.info(f"Starting update_summary Version {__version__}")
    print(f"Starting date fix Version {__version__}")

    parser = argparse.ArgumentParser(description="Update projects summary script")
    parser.add_argument('--env', choices=['prod', 'test'], default='test',
                        help='Set environment path from environment variables')
    parser.add_argument('--inject-date', type=str, default=None,
                        help='Inject a specific date (YYYY-MM-DD) instead of today\'s date')
    args = parser.parse_args()

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

    projects_processed_counter = 0

    for root, dirs, files in os.walk(projects_tree_root, topdown=False):
        if project_info_filename not in files or project_folders_root not in root:
            logging.warning(f"Skipping {root}")
            continue

        with open(os.path.join(root, project_info_filename), "r",
                                encoding="utf-8-sig") as project_info_file:
            logging.debug(f'Processing root={root}')
            project_file_lines = []
            for line in tqdm(project_info_file):
                new_line = clean_line(line, os.path.join(root, project_info_filename))
                project_file_lines.append(new_line)
        # create backup and new file
        print("### New file")
        print("\n".join(project_file_lines))
        projects_processed_counter += 1
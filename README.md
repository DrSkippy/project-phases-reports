# Folder Based Project Reporting Tool

This tool is designed to generate reports based on the structure and contents of a folder-based project. It scans through the directories and files, extracting relevant information to create a comprehensive report.
## Features

Eech project folder must contain a copy of the sample file:

[clean_sample_PROJECT_INFO.txt](tests/clean_sample_PROJECT_INFO.txt)

Structure of phases and reports after running the script with one project in teh Completed Phase will look like:
```
projects_snapshot
└── Projects Folders
    ├── 0-Ideas
    ├── 1-Chartering
    ├── 2-Committed
    ├── 3-In Progress
    ├── 4-On Hold
    ├── 5-Rollout
    ├── 6-Completed
    │   └── Sample Project for Testing
    │       └── PROJECT_INFO.txt
    ├── analytics_summary.csv
    ├── data_product_links.md
    ├── owner_views_active.md
    ├── owner_views_commit.md
    ├── owner_views_completed.md
    ├── phase_views.md
    ├── stakeholder_list.txt
    ├── stakeholders_views_active.md
    ├── summary.csv
    └── weekly_owner_views_active.html
```

test_clean_projects.sh in the testing directory will create a `projects_snapshot` from your gzipped `projects_snapshot.tar.gz` file.

test_clean_full_cycle_single_project.sh in the testing directory will create a `projects_snapshot` from your gzipped `projects_snapshot.tar.gz` file, then move the sample project through all phases, generating reports at each phase.

./bin/update_summary_v2.py has flags --env prod for running in production mode, --env test for running in test mode with synthetic date injection for reproducibility.

./bin/update_summary.py has flags --env prod for running in production mode, --env test for running in test mode but no synthetic date injection.
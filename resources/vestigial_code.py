# def compute_stage_age(...)
# function definition that was commented out in bin/update_summary.py. Archived for reference.
#
#
#     # [OG Comment]: Modify to overwrite values if new value is greater
#     def compute_stage_age(params, root, project_info_filename, stage_key_date, stage_key_age):
#         """
#         Compute the age in days for a given stage key in the params dictionary.
#
#         Args:
#             params (dict): The dictionary holding stage data.
#             root (str): The root directory for the file.
#             project_info_filename (str): The name of the file where data will be written.
#             stage_key_date (str): The key for the stage date (e.g., "COMPUTED_DATE_IN_STAGE_X").
#             stage_key_age (str): The key for the stage age in days (e.g., "COMPUTED_DAYS_IN_STAGE_X").
#
#         Returns:
#             int: The computed or existing stage age in days.
#         """
#         # logging.info(f'fn param stage_key_date == {repr(stage_key_date)}')
#         # logging.info(f'fn param stage_key_age == {repr(stage_key_age)}')
#         stage_date_str = params.get(stage_key_date)
#         # logging.info(f'stage_date_str == {repr(stage_date_str)}')
#         current_date = date.today()
#
#         if stage_date_str:
#             stage_date = datetime.datetime.strptime(stage_date_str, DATE_FMT).date()
#             logging.info(f'stage_date == {repr(stage_date)}')
#
#             if params[stage_key_age] is None:
#                 if stage_date <= current_date:
#                     stage_age = (current_date - stage_date).days
#                     logging.info(f'stage_age == {repr(stage_age)}')
#                     params[stage_key_age] = stage_age
#
#                     # Write the computed age to the file
#                     # logging.info(
#                     #     f'root == {repr(root)},'
#                     #     f' project_info_filename == {repr(project_info_filename)},'
#                     #     f' stage_key_age == {repr(stage_key_age)},'
#                     #     f' stage_age == {repr(stage_key_age)}'
#                     # )
#                     write_to_project_info(root, project_info_filename, stage_key_age, stage_age)
#
#                     return stage_age
#                 elif stage_date > current_date:
#                     logging.info(f"Date associated with stage is in the future: {stage_date}")
#             else:
#                 # Return the existing age value
#                 # logging.info(f'params[stage_key_age] == {repr(params[stage_key_age])}')
#                 stage_age = params[stage_key_age]
#                 # logging.info(f'stage_age == {repr(stage_age)}')
#                 # logging.info(f"Existing age for {stage_key_age}: {stage_age}")
#                 # logging.info(
#                 #     f'root == {repr(root)},'
#                 #     f' project_info_filename == {repr(project_info_filename)},'
#                 #     f' stage_key_age == {repr(stage_key_age)},'
#                 #     f' stage_age == {repr(stage_key_age)}'
#                 # )
#                 return stage_age
#         else:
#             logging.warning(f"Unable to compute age: Missing date for {stage_key_date}")
#             return None
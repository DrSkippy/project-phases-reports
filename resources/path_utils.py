import logging
import os
import sys
from pathlib import Path


class SystemInfo:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.env_user = os.environ['USER']
        self.path_user = self._get_path_user()
        self.projects_path = self._get_projects_path()

    def _get_path_user(self):
        path_object = Path(self.current_dir)
        path_parts = path_object.parts
        if len(path_parts) > 2 and path_parts[1] == 'Users':
            return path_parts[2]
        logging.warning("Path does not follow the expected format: '/Users/[user]/...' _get_path_user() returns None")
        return None

    def _get_projects_path(self):
        if self.env_user == self.path_user:
            if self.path_user == 's.hendrickson':
                return "/Users/s.hendrickson/Documents/OneDrive - F5, Inc"
            elif self.path_user == 'ke.wilson':
                print("Enter 'test' to set target path to '/Users/ke.wilson/Desktop/test_data_accel'. \n"
                      "Enter 'OneDrive' to set target path to '/Users/ke.wilson/Library/CloudStorage/OneDrive-F5,Inc/Documents - Data Accelerator - Enterprise Analytics'. \n"
                      "Enter 'other' to specify a target path. \n"
                      "Enter 'cancel' to end the program.")
                kw_path_input = input("Enter one of the following [test/OneDrive/other]: ")
                if kw_path_input == 'test':
                    print("Path to projects directory set as: '/Users/ke.wilson/Desktop/test_data_accel'")
                    return "/Users/ke.wilson/Desktop/test_data_accel"
                elif kw_path_input == 'OneDrive':
                    verify_prod_path = input("Are you sure you want to alter files in OneDrive? y/n: ")
                    if verify_prod_path == 'y':
                        print("Path to projects directory set as: /Users/ke.wilson/Library/CloudStorage/OneDrive-F5,Inc/Documents - Data Accelerator - Enterprise Analytics'")
                        return "/Users/ke.wilson/Library/CloudStorage/OneDrive-F5,Inc/Documents - Data Accelerator - Enterprise Analytics"
                    else:
                        print(f"You responded with '{verify_prod_path}'. The program will now end.")
                        sys.exit("\n\nProgram terminated due to user input.")
                elif kw_path_input == 'other':
                    kw_custom_path = input("Enter target path without quotations: ")
                    print(f"Path to projects directory set as: '{kw_custom_path}'")
                    return kw_custom_path
                elif kw_path_input == 'cancel':
                    print(f"You responded with '{kw_path_input}. The program will now end.")
                    sys.exit("\n\nProgram terminated due to user input.")
                else:
                    print(f"Invalid user input: '{kw_path_input}'.\nThe program will now end.")
                    sys.exit("\n\nProgram terminated due to user input.")
        else:
            newuser_custom_path = input("Enter target path without quotations: ")
            newuser_verify_input = input(f"Path to projects directory is about to be set as: '{newuser_custom_path}'\nWould you like to proceed? y/n: ")
            if newuser_verify_input == 'y':
                print(f"Path to projects directory set as: \n\t'{newuser_custom_path}'")
                return newuser_custom_path
            else:
                print(f"You responded with '{newuser_verify_input}'. The program will now end.")
                sys.exit("\n\nProgram terminated due to user input.")

    def return_system_info(self):
        return self.projects_path


if __name__ == "__main__":
    system_info = SystemInfo()
    class_path = system_info.return_system_info()
    print(class_path)


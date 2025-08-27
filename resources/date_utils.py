import logging
from datetime import datetime, date, time, timedelta, timezone

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"


def parse_date(date_input, type_out, date_format=DATE_FMT):
    if type(date_input) == str:
        """
        Parse a date string into a `datetime` object.
        """
        if type_out == 'date':
            try:
                return datetime.strptime(date_input, date_format).date()
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        elif type_out == 'datetime':
            try:
                return datetime.strptime(date_input, date_format)
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        else:
            logging.error("parse_date() type_out argument needs to be str type 'date' or str type 'datetime'")
            return None
    elif type(date_input) == datetime.date:
        if type_out == 'date':
            try:
                return date_input
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        elif type_out == 'datetime':
            try:
                return datetime.combine(date_input, time.min)
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        else:
            logging.error("parse_date() type_out argument needs to be str type 'date' or str type 'datetime'")
            return None
    elif type(date_input) == datetime:
        if type_out == 'date':
            try:
                return date_input.date()
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        elif type_out == 'datetime':
            try:
                return date_input
            except ValueError as e:
                logging.error(f"Error parsing date: {date_input} - {str(e)}")
                return None
        else:
            logging.error("parse_date() type_out argument needs to be str type 'date' or str type 'datetime'")
            return None
    else:
        logging.error(f"date_str is {type(date_input)}")


def days_between_dates(start_date, end_date):
    """
    Calculate the number of days between two dates. Returns -999 if invalid.
    """
    if start_date and end_date:
        delta = end_date - start_date
        return max(delta.days, 0)
    # avoid special values that are valid math values: return -999
    return None

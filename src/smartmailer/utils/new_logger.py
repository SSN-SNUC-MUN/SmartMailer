import os
from datetime import datetime
from typing import Optional, TextIO

from smartmailer.utils.shell import get_style

from inspect import getframeinfo, stack


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs) -> "Logger":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
            self,
            log_to_file: bool = False,
            log_level: str = "INFO"
        ) -> None:

        self.log_to_file = log_to_file
        self.log_level = log_level
        self.log_dir = "smartmailer_logs"
        self.log_file_handle: Optional[TextIO] = None
        self.log_line_format = '%Y-%m-%d %H:%M:%S'
        self.cwd = os.getcwd()

        if log_level not in LOG_LEVELS:
            old_level = log_level
            self.log_level = "INFO"
            self._log_helper(f"Log Level {old_level} not found in {LOG_LEVELS}. Defaulting to INFO.", "WARNING", datetime.now())
            
        if self.log_to_file:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            log_filename = datetime.now().strftime("smartmailer-%Y-%m-%d_%H-%M-%S.log")
            log_path = os.path.join(self.log_dir, log_filename)
            self.log_file_handle = open(log_path, "w")


    def debug(self, message: str) -> None:
        log_level = "DEBUG"
        self._log_helper(message, log_level, datetime.now())

    def info(self, message: str) -> None:
        log_level = "INFO"
        self._log_helper(message, log_level, datetime.now())

    def warning(self, message: str) -> None:
        log_level = "WARNING"
        self._log_helper(message, log_level, datetime.now())

    def error(self, message: str) -> None:
        log_level = "ERROR"
        self._log_helper(message, log_level, datetime.now())

    def critical(self, message: str) -> None:
        log_level = "CRITICAL"
        self._log_helper(message, log_level, datetime.now())


    def _log_helper(self, message: str, log_level: str, timestamp: datetime) -> None:
        caller = getframeinfo(stack()[2][0])
        # entry 0 is this function
        # entry 1 is what called _log_helper - which is the debug(), info() and family
        # entry 2 is what called the debug(), info() and such - this is the file which logged the entry
        # hence the stack()[2]
        filename = os.path.relpath(caller.filename, self.cwd)
        # we get the relative path of the filename to the current working directory,
        # from the absolute path given to us.

        if LOG_LEVELS.index(self.log_level) <= LOG_LEVELS.index(log_level):
            self._dispatch_message(message, f"{filename} L{caller.lineno}", log_level, timestamp)

    def _dispatch_message(self, message: str, file_or_context: str, log_level: str, datetime: datetime) -> None:
        string = f"{datetime.strftime(self.log_line_format)} | {log_level} | {file_or_context} | {message}"
        if self.log_to_file:
            self.log_file_handle.write(string)

        color_map = {
            "INFO": ["bold"],
            "WARNING": ["yellow"],
            "ERROR": ["red"],
            "CRITICAL": ["red", "bold"]
        }
        if log_level in color_map:
            string = "".join([get_style(style) for style in color_map[log_level]]) + string + get_style("end")
        print(string)
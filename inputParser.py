import argparse as ap
import logging
import os.path

import pandas as pd


# Assumptions
# SSV file format = .log
# It is quite difficult to have 2 positional arguments while when one (or more) of them are extensible

class InputParse:
    def __init__(self):
        self.parser = ap.ArgumentParser(prog='LogParse',
                                        description='Parse SquidProxy logs, currently handles CSV files')
        # flag args format (flag, help) : True / False
        self.flag_args = [('--mfip', 'Most frequent IP'),
                          ('--lfip', 'Least frequent IP'),
                          ('--eps', 'Events per Second'),
                          ('--bytes', 'Total amount of bytes exchanged')]
        self.files = []

        self.add_args()

    def add_args(self):
        """Add required arguments to the argparse"""
        self.parser.add_argument('-i', "--inputFilePath", nargs="+",
                                 help="One or more files to parse", action="store")
        self.parser.add_argument('-o', '--outputFilePath', type=str,
                                 help=" Path to a file to save output in plain text JSON format")

        # Add Required flags (at least one of)
        required_flag = self.parser.add_argument_group("Output Information")
        for arg in self.flag_args:
            required_flag.add_argument(arg[0], help=arg[1], action="store_true", required=False)

    def verify_file_locations(self, args) -> None:
        """Verify permissions for input and output files before attempting any file operations.
         There might be different options of handling this situation, for now it just raises a permissions error"""
        not_found = []
        not_readable = []
        for file in args.inputFilePath:
            if not os.path.exists(file):
                not_found.append(file)
            if not os.access(file, os.R_OK):
                not_readable.append(file)
        if not_found:
            raise FileNotFoundError("\n".join(not_found))
        if not_readable:
            raise PermissionError('Unable to read [Permission Denied]: \n' + "\n".join(not_readable))

        try:
            # Remove output file if it exists without promoting the user
            if os.path.exists(args.outputFilePath):
                os.remove(args.outputFilePath)
            # check if the file will be writable
            open(args.outputFilePath, "w")
        except PermissionError:
            raise PermissionError(f"Write permissions denied for {args.outputFilePath}")

    def load_files(self, files: list):
        """Load all files into memory in form of pandas dataframes for further processing.
        Very likely quite memory heavy, there are optimization paths like out of core or 1by1 / parallel processing"""
        for file_path in files:
            logging.info(f"Loading file: {file_path}")
            if file_path.endswith(".log"):
                try:
                    # Assuming that .log means SSV as is usual
                    file_content = self.parse_ssv(file_path)
                    self.files.append((file_path, file_content))
                except Exception as e:
                    logging.error(f"File not in expected format[SSV] skipping: {file_path} \n {e}")
            # Add more elif conditions as desired to expand file reading ability
            # (Could be made into standalone file if there is enough types as a class extension)
            else:
                logging.error(f"File format not recognised: {file_path}")

        logging.info("Files loaded")

    def parse_ssv(self, file: str) -> pd.DataFrame:
        """Uses pandas read_csv function with tweaks and python engine to load SSV files,
         logs any bad lines as warnings"""

        def handle_bad_line(line):
            # handling if required
            logging.warning(f"Bad Line {line}")

        data = pd.read_csv(file, sep='\\s+', on_bad_lines=handle_bad_line, engine='python', header=None)
        # cleaning here if required
        return data

    def run(self):
        args = self.parser.parse_args()
        # create a dict of flag name : flag value
        flag_values = {flag[0].strip('-'): getattr(args, flag[0].strip('-')) for flag in self.flag_args}
        # check if at least 1 flag is set
        if sum(flag_values.values()) == 0:
            self.parser.error("At least of the parameters in the Output Information flags is needed")

        self.verify_file_locations(args)
        self.load_files(args.inputFilePath)

        return self.files, flag_values, args.outputFilePath

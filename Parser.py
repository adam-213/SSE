import json
import logging

import pandas as pd

from inputParser import InputParse


class Parser:
    def __init__(self):
        self.method_mapping = {}
        # map the class for processing methods
        self.map_processing_methods()
        # initiate Input Handler
        input_handler = InputParse()
        # Check if flags match with implemented functions
        if set([arg[0].removeprefix("--") for arg in input_handler.flag_args]) != set(self.method_mapping.keys()):
            missing = set([arg[0].removeprefix("--") for arg in input_handler.flag_args]) - set(
                self.method_mapping.keys())
            # python 3.11 does not allow for f-string expression part cannot include a backslash (fixed in 3.12)
            missing_string = '\n'.join(missing)
            logging.warning(f"Flag exists without parser function implemented: {missing_string}")
        # Run input handling
        self.files, self.flags, self.output = input_handler.run()

    def map_processing_methods(self):
        """ This method maps out the Parser class for all methods that start with p_ and maps them to their
        respective flags this is specifically to not use eval/exec while maintaining centralization of the flags"""

        # possible to switch this around to create flags based on what is implemented (+ pull help from docstrings of
        # functions)
        for method_name in dir(self):
            if method_name.startswith("p_"):
                method = getattr(self, method_name)
                self.method_mapping[method_name.removeprefix("p_")] = method

    def run(self) -> None:
        """Execute the analysis on per-file basis"""
        filestats = []
        for file in self.files:
            # print(f"Statistics for file {file[0]}")
            logging.info(f"Analysing {file[0]}")
            stats = {}
            for flag_name, flag_value in self.flags.items():
                if flag_value:
                    result = self.method_mapping[flag_name](file[1])
                    stats[flag_name] = result
            filestats.append((file[0], stats))

        self.to_json(filestats)

    def to_json(self, filestats: list) -> None:
        logging.info("Writing json")
        dict_data = {fn: stats for fn, stats in filestats}
        with open(self.output, 'w') as jsonFile:
            # assuming that the analysis functions are written well and handled their outputs to be Json compatible
            json.dump(dict_data, jsonFile, indent=4)

    def p_mfip(self, file: pd.DataFrame):
        """Get most frequent IP"""
        client_ip = file.iloc[:, 2]
        mfip = client_ip.value_counts().head(1)
        # print("Most Frequent IP", mfip)
        return mfip.keys()[0]

    def p_lfip(self, file: pd.DataFrame):
        """Get least frequent IP"""
        client_ip = file.iloc[:, 2]
        lfip = client_ip.value_counts().tail(1)
        # print("Least Frequent IP", lfip)
        return lfip.keys()[0]

    def p_eps(self, file: pd.DataFrame):
        """Average events per second in the file"""
        timestamps = pd.to_datetime(file.iloc[:, 0], unit='s')
        rounded_timestamps = timestamps.dt.round('1s')
        counts = rounded_timestamps.value_counts()
        avg_counts = counts.mean()
        # print("Average events per second", avg_counts)
        return float(avg_counts)

    def p_bytes(self, file: pd.DataFrame):
        """Total data transferred in bytes"""
        bytes_var = file.iloc[:, 4]
        sum_bytes = bytes_var.sum()
        # print("Total amount of data transferred [B]", sumBytes)
        return int(sum_bytes)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = Parser()
    parser.run()

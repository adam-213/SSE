import logging

import pandas as pd

from inputParser import InputParse

import json


class Parser:
    def __init__(self):
        self.methodMapping = {}
        # map the class for processing methods
        self.mapProcessingMethods()
        # initiate Input Handler
        inputHandler = InputParse()
        # Check if flags match with implemented functions
        if set([arg[0].removeprefix("--") for arg in inputHandler.flagArgs]) != set(self.methodMapping.keys()):
            missing = set([arg[0].removeprefix("--") for arg in inputHandler.flagArgs]) - set(self.methodMapping.keys())
            logging.warning(f"Flag exists without parser function implemented: {'\n'.join(missing)}")
        # Run input handling
        self.files, self.flags, self.output = inputHandler.run()

    def mapProcessingMethods(self):
        """ This method maps out the Parser class for all methods that start with p_ and maps them to their respective flags
            this is specifically to not use eval/exec while maintaining centralization of the flags """

        #  possible to switch this around to create flags based on what is implemented (+ pull help from docstrings of functions)
        for methodName in dir(self):
            if methodName.startswith("p_"):
                method = getattr(self, methodName)
                self.methodMapping[methodName.removeprefix("p_")] = method

    def run(self):
        filestats = []
        for file in self.files:
            # print(f"Statistics for file {file[0]}")
            logging.info(f"Analysing {file[0]}")
            stats = {}
            for flagName, flagValue in self.flags.items():
                if flagValue:
                    result = self.methodMapping[flagName](file[1])
                    stats[flagName] = result
            filestats.append((file[0], stats))

        self.toJson(filestats)

    def toJson(self, filestats):
        logging.info("Writing json")
        dictData = {fn: stats for fn, stats in filestats}
        with open(self.output, 'w') as jsonFile:
            # assuming that the analysis functions are written well and handled their outputs to be Json compatible
            json.dump(dictData, jsonFile, indent=4)

    def p_mfip(self, file: pd.DataFrame):
        """Get most frequent IP"""
        clientIP = file.iloc[:, 2]
        mfip = clientIP.value_counts().head(1)
        # print("Most Frequent IP", mfip)
        return mfip.keys()[0]

    def p_lfip(self, file: pd.DataFrame):
        """Get least frequent IP"""
        clientIP = file.iloc[:, 2]
        lfip = clientIP.value_counts().tail(1)
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
        bytes = file.iloc[:, 4]
        sumBytes = bytes.sum()
        # print("Total ammount of data transfered [B]", sumBytes)
        return int(sumBytes)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = Parser()
    parser.run()

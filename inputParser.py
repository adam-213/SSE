import argparse as ap
import os.path
import pandas as pd
import logging


# Assumptions
# SSV file format
# It is quite difficult to have 2 positional arguments while having the input be extensible whle the other are not -> -parameters were used
# there might be concerns with memory with this kind of loading,
#   there are options, you could use vaex [out of core] or process the files as they are being loaded 1by1


class InputParse:
    def __init__(self):
        self.parser = ap.ArgumentParser(prog='LogParse', description='Parse SquidProxy logs, currently handles CSV files')
        # flag args format (flag, help) : True / False
        self.flagArgs = [('--mfip', 'Most frequent IP'),
                         ('--lfip', 'Least frequent IP'),
                         ('--eps', 'Events per Second'),
                         ('--bytes', 'Total amount of bytes exchanged')]
        self.files = []

        self.addArgs()

    def addArgs(self):
        # Required files arg (extensible)
        self.parser.add_argument('-i', "--inputFilePath", nargs="+",
                                 help="One or more files to parse", action="store")
        self.parser.add_argument('-o', '--outputFilePath', nargs=1,
                                 help=" Path to a file to save output in plain text JSON format")

        # Add Required flags (at least one of)
        requiredFlag = self.parser.add_argument_group("Output Information")
        for arg in self.flagArgs:
            requiredFlag.add_argument(arg[0], help=arg[1], action="store_true", required=False)

    def verifyFileLocations(self, args):
        notFound = []
        notReadable = []
        for file in args.inputFilePath:
            if not os.path.exists(file):
                notFound.append(file)
            if not os.access(file, os.R_OK):
                notReadable.append(file)
        if notFound:
            raise FileNotFoundError("\n".join(notFound))
        if notReadable:
            raise PermissionError('Unable to read [Permission Denied]: \n' + "\n".join(notFound))
        if not os.access(args.outputFilePath[0], os.W_OK):
            raise PermissionError(f"Write permissions denied for {args.outputFilePath}")

    def loadFiles(self, files: list):
        for filePath in files:
            logging.info(f"Loading file: {filePath}")
            if filePath.endswith(".log"):
                try:
                    # Assuming that .log means SSV as is usual
                    fileContent = self.parseSSV(filePath)
                    # appending dataframes to a list for them to be returned by the class.
                    self.files.append((filePath, fileContent))
                except Exception as e:
                    logging.error(f"File not in expected format[SSV] skipping: {filePath} \n {e}")
            # Add more elif conditions as desired to expand file reading ability
            # (Could be made into standalone file if there is enough types as a class extension)
            else:
                logging.error(f"File format not recognised: {filePath}")

        logging.info("Files loaded")

    def parseSSV(self, file):

        def handleBadLine(line):
            # handling if required
            logging.warning(f"Bad Line {line}")

        data = pd.read_csv(file, sep='\\s+', on_bad_lines=handleBadLine, engine='python')
        # cleaning here if required
        return data

    def run(self):
        args = self.parser.parse_args()
        # create a dict of flagname : flagvalue
        flagValues = {flag[0].strip('-'): getattr(args, flag[0].strip('-')) for flag in self.flagArgs}
        # check if at least 1 flag is set
        if sum(flagValues.values()) == 0:
            self.parser.error("At least of the parameters in the Output Information flags is needed")

        self.verifyFileLocations(args)
        self.loadFiles(args.inputFilePath)

        if __name__ == '__main__':
            # for self testing purposes
            self.test(args, flagValues)

        return self.files, flagValues, args.outputFilePath[0]

    def test(self, args, flagValues):
        logging.debug(args)
        logging.debug(self.files)
        logging.debug(flagValues)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    InputParse().run()

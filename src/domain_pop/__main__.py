"""
Blueprint Domain Population

"""
# System
import logging
import logging.config
import sys
import argparse
from pathlib import Path
import atexit

# Domain Population
from domain_pop.domaindb import DomainDB
from domain_pop import version

_logpath = Path("domain_pop.log")
_progname = 'Blueprint Domain Population'

def clean_up():
    """Normal and exception exit activities"""
    _logpath.unlink(missing_ok=True)

def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description=_progname)
    parser.add_argument('-dom', '--domain', action='store',
                        help='Name of a directory containing a domain in a populated metamodel TclRAL file and one '
                             'db type file per domain')
    parser.add_argument('-c', '--context', action='store',
                        help='Name of the context directory specifying initial populations and states per domain')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='Debug mode'),
    parser.add_argument('-L', '--log', action='store_true',
                        help='Generate a diagnostic log file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose messages')
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version')
    return parser.parse_args(cl_input)


def main():
    # Start logging
    logger = get_logger()
    logger.info(f'{_progname} version: {version}')

    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'{_progname} version: {version}')
        sys.exit(0)

    if not args.log:
        # If no log file is requested, remove the log file before termination
        atexit.register(clean_up)

    # Domain specified
    if args.system:
        DomainDB.populate(system_dir=Path(args.system), context_dir=Path(args.context),
                      scenario_file=Path(args.scenario), debug=args.debug)

    logger.info("No problemo")  # We didn't die on an exception, basically
    if args.verbose:
        print("\nNo problemo")


if __name__ == "__main__":
    main()

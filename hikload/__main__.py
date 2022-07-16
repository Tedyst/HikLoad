from .download import parse_args, run
import logging
import signal
import sys


def main_ui(args=None):
    try:
        from .ui import main as ui_main
        if args == None:
            args = parse_args()
        ui_main(args)
    except ImportError as e:
        logging.error(e)
        logging.error("Could not import the UI. Please install PyQt5 and Qt5")
    except Exception as e:
        logging.error(e)
        raise e


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    args = parse_args()
    try:
        if args.ui:
            main_ui(args)
        else:
            logging.info("If you want to use the UI, use the --ui flag")
            run(args)
    except KeyboardInterrupt:
        logging.info("Exited by user")
        sys.exit(0)


if __name__ == '__main__':
    main()

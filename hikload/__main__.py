from .download import parse_args, run
from .ui import main as ui_main
import logging
import signal

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    args = parse_args()
    try:
        if args.ui:
            ui_main(args)
        else:
            logging.info("If you want to use the UI, use the --ui flag")
            run(args)
    except KeyboardInterrupt:
        logging.info("Exited by user")
        exit(0)

if __name__ == '__main__':
    main()
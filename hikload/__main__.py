from .download import parse_args, run
import logging

def main():
    args = parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        logging.info("Exited by user")
        exit(0)

if __name__ == '__main__':
    main()
import argparse
import logging
import os

from isas.service import Service

LOGGER_NAMES = [
    'isas_base.data.data_manager',
    'isas_base.subpackage.base',
    'isas_base.subpackage.base_analysis',
    'isas_base.subpackage.base_measurement',
    'isas_base.subpackage.base_visualization',
    'isas.interface',
    'isas.dashboard.dashboard',
    'isas.dashboard.qt.dashboard_app',
    'isas.service.service',
    'isas.service.socket',
]


def main() -> None:
    # set arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('cfg_path')
    args = vars(parser.parse_args())

    # set logger
    for logger_name in LOGGER_NAMES:
        logger = logging.getLogger(logger_name)
        logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
        formatter = logging.Formatter('%(asctime)s %(levelname)7s %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # run service
    service = Service(cfg=args['cfg_path'])
    service()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

from valutatrade_hub.cli.interface import CLI
from valutatrade_hub.core.utils import ensure_data_files


def main():
    '''
    Функция точки входа
    '''
    ensure_data_files()
    
    app = CLI()
    app.run()

if __name__ == "__main__":
    main()
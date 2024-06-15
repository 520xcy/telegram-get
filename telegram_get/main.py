#!/usr/bin/python3

import os
if os.getenv('ISBOT'):
    from tg_bot import tg_client
else:
    from tg_client import tg_client


PROJECT_PATH = os.path.dirname(__file__)



if __name__ == '__main__':

    

    t = tg_client(PROJECT_PATH)
    t.start()
    

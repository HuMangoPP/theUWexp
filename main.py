#!/usr/bin/env python
from src.client import Client
import sys

if __name__ == '__main__':
    client = Client()
    client.run()
    sys.exit()
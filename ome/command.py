# ome - Object Message Expressions
# Copyright (c) 2015-2016 Luke McCarthy <luke@iogopro.co.uk>

from argparse import ArgumentParser

argparser = ArgumentParser('ome', add_help=False)
argparser.add_argument('filename', nargs='+')
argparser.add_argument('--verbose', '-v', action='store_true')
argparser.add_argument('--verbose-backend', action='store_true')
argparser.add_argument('--target', action='store', default='c')
argparser.add_argument('--backend', action='store', default=None)
argparser.add_argument('--backend-command', action='store', default=None)
argparser.add_argument('--print-code', action='store_true')

command_args = argparser.parse_args()

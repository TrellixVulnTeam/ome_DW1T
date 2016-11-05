# ome - Object Message Expressions
# Copyright (c) 2015-2016 Luke McCarthy <luke@iogopro.co.uk>

import os
from ...error import OmeError
from .backend_cc import CCArgsBuilder, CCBuilder

class GCCArgsBuilder(CCArgsBuilder):
    all = [
        '-x', 'c',
        '-std=c99',
        '-Wall',
        '-Wextra',
        '-Wno-unused',
    ]
    release = [
        '-O3',
    ]
    debug = [
        '-ggdb',
    ]
    release_link = [
        '-Wl,--strip-all',
        '-Wl,--gc-sections',
    ]

    def get_musl_args(self, built_options, musl_path):
        specs_file = os.path.join(musl_path, 'lib', 'musl-gcc.specs')
        if not os.path.isfile(specs_file):
            raise OmeError('could not find GCC specs file for musl: ' + specs_file)
        return [], ['-specs', specs_file]

class GCCBuilder(CCBuilder):
    name = 'GCC'
    default_command = 'gcc'
    supported_platforms = frozenset(['linux'])
    version_args = ['--version']
    version_re = 'gcc \(GCC\) (\d+\.\d+\.\d+)'
    get_build_args = GCCArgsBuilder()

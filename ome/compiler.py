# ome - Object Message Expressions
# Copyright (c) 2015 Luke McCarthy <luke@iogopro.co.uk>. All rights reserved.

import io
import os
import re
import struct
import subprocess
import sys

from . import constants
from .ast import Block, BuiltInBlock, Method, Send, Sequence
from .constants import *
from .dispatcher import generate_dispatcher
from .labels import *
from .parser import Parser
from .target import target_platform_map, default_target_platform

class TraceBackInfo(object):
    def __init__(self, id, file_info, source_line, column, underline):
        self.id = id
        self.file_info = file_info
        self.source_line = source_line
        self.column = column
        self.underline = underline

def encode_string_data(string):
    """Add 32-bit length header and nul termination/alignment padding."""
    string = string.encode('utf8')
    string = struct.pack('I', len(string)) + string
    padding = b'\0' * (8 - (len(string) & 7))
    return string + padding

class DataTable(object):
    def __init__(self):
        self.size = 0
        self.data = []
        self.string_offsets = {}

    def append_data(self, data):
        offset = self.size
        self.data.append(data)
        self.size += len(data)
        return offset

    def allocate_string_offset(self, string):
        if string not in self.string_offsets:
            data = encode_string_data(string)
            self.string_offsets[string] = self.append_data(data)
        return self.string_offsets[string]

    def allocate_string(self, string):
        return '(OME_data+%s)' % self.allocate_string_offset(string)

    def generate_assembly(self, out):
        out.write('\nalign 8\nOME_data:\n')
        for data in self.data:
             out.write('\tdb ' + ','.join('%d' % byte for byte in data) + '\n')
        out.write('.end:\n')

def collect_nodes_of_type(ast, node_type):
    nodes = []
    def append_block(node):
        if isinstance(node, node_type):
            nodes.append(node)
    ast.walk(append_block)
    return nodes

class Program(object):
    def __init__(self, filename, ast, builtin, target_type):
        self.filename = filename
        self.builtin = builtin
        self.toplevel_method = ast
        self.toplevel_block = ast.expr

        if isinstance(self.toplevel_block, Sequence):
            self.toplevel_block = self.toplevel_block.statements[-1]

        if 'main' not in self.toplevel_block.symbols:
            self.error('no main method defined')

        self.target_type = target_type
        self.code_table = []  # list of (symbol, [list of (tag, method)])
        self.data_table = DataTable()

        self.block_list = collect_nodes_of_type(ast, Block)
        self.allocate_tag_ids()
        self.allocate_constant_tag_ids()

        self.send_list = collect_nodes_of_type(ast, Send)
        self.find_used_methods()
        self.compile_traceback_info()

        self.build_code_table()

    def error(self, message):
        raise OmeFileError(self.filename, message)

    def warning(self, message):
        sys.stderr.write('\x1b[1m{0}: \x1b[35mwarning:\x1b[0m {1}\n'.format(self.filename, message))

    def allocate_tag_ids(self):
        tag = Tag_User
        for block in self.block_list:
            if not block.is_constant:
                block.tag = tag
                tag += 1
        if tag > MAX_TAG:
            self.error('exhausted all tag IDs')

    def allocate_constant_tag_ids(self):
        constant_tag = Constant_User
        for block in self.block_list:
            if block.is_constant:
                block.tag = constant_to_tag(constant_tag)
                block.tag_constant = constant_tag
                constant_tag += 1
        if constant_tag > MAX_CONSTANT_TAG:
            self.error('exhausted all constant tag IDs')

    def find_used_methods(self):
        self.sent_messages = set(['string'])
        self.sent_messages.update(
            send.symbol for send in self.send_list if not send.receiver_block)

        self.called_methods = set([
            (self.toplevel_block.tag, 'main'),
        ])
        self.called_methods.update(
            (send.receiver_block.tag, send.symbol) for send in self.send_list
            if send.receiver_block and send.symbol not in self.sent_messages)

        for method in self.target_type.builtin_methods:
            if method.sent_messages and self.should_include_method(method, self.builtin.tag):
                self.sent_messages.update(method.sent_messages)

    def compile_traceback_info(self):
        for send in self.send_list:
            if send.parse_state:
                ps = send.parse_state
                file_info = '\n  File "%s", line %s, in |%s|\n    ' % (
                    ps.stream_name, ps.line_number, send.method.symbol)

                line_unstripped = ps.current_line.rstrip()
                line = line_unstripped.lstrip()
                column = 4 + (ps.column - (len(line_unstripped) - len(line)))

                underline = send.symbol.find(':') + 1
                if underline < 1:
                    underline = len(send.symbol)

                send.traceback_info = TraceBackInfo(
                    id = (ps.stream_name, ps.line_number, ps.column),
                    file_info = self.data_table.allocate_string(file_info),
                    source_line = self.data_table.allocate_string(line),
                    column = column,
                    underline = underline)

    def compile_method_with_label(self, method, label):
        code = method.generate_code(self.data_table)
        code.optimise(self.target_type)
        return code.generate_assembly(label, self.target_type)

    def compile_method(self, method, tag):
        return self.compile_method_with_label(method, make_call_label(tag, method.symbol))

    def should_include_method(self, method, tag):
        return method.symbol in self.sent_messages or (tag, method.symbol) in self.called_methods

    def build_code_table(self):
        methods = {}

        for method in self.target_type.builtin_methods:
            if self.should_include_method(method, self.builtin.tag):
                if method.symbol not in methods:
                    methods[method.symbol] = []
                label = make_call_label(method.tag, method.symbol)
                code = '%s:\n%s' % (label, method.code)
                methods[method.symbol].append((method.tag, code))

        for block in self.block_list:
            for method in block.methods:
                if self.should_include_method(method, block.tag):
                    if method.symbol not in methods:
                        methods[method.symbol] = []
                    code = self.compile_method(method, block.tag)
                    methods[method.symbol].append((block.tag, code))

        for symbol in sorted(methods.keys()):
            self.code_table.append((symbol, methods[symbol]))

        methods.clear()

    def generate_assembly(self, out):
        define_format = self.target_type.define_constant_format
        for name, value in sorted(constants.__dict__.items()):
            if isinstance(value, int):
                out.write(define_format.format(name, value))

        out.write(define_format.format('OME_main', make_call_label(self.toplevel_block.tag, 'main')))
        out.write(self.target_type.builtin_macros)
        out.write(self.target_type.builtin_code)
        out.write('\n')
        out.write(self.compile_method_with_label(self.toplevel_method, 'OME_toplevel'))
        out.write('\n')

        dispatchers = set()
        for symbol, methods in self.code_table:
            if symbol in self.sent_messages:
                tags = [tag for tag, code in methods]
                out.write(generate_dispatcher(symbol, tags, self.target_type))
                out.write('\n')
                dispatchers.add(symbol)
            for tag, code in methods:
                out.write(code)
                out.write('\n')

        for symbol in self.sent_messages:
            if symbol not in dispatchers:
                self.warning("no methods defined for message '%s'" % symbol)
                out.write(generate_dispatcher(symbol, [], self.target_type))
                out.write('\n')

        out.write(self.target_type.builtin_data)
        self.data_table.generate_assembly(out)

def parse_file(filename, builtin):
    try:
        with open(filename) as f:
            source = f.read()
    except FileNotFoundError:
        raise OmeFileError('ome', 'file does not exist: ' + filename)
    except UnicodeDecodeError as e:
        raise OmeFileError(filename, 'utf-8 decoding failed at position {0.start}: {0.reason}'.format(e))
    except Exception as e:
        raise OmeFileError(filename, str(e))
    return Parser(source, filename, builtin).toplevel()

def compile_file_to_assembly(filename, target_type):
    builtin = BuiltInBlock(target_type)
    ast = parse_file(filename, builtin)
    ast = Method('', [], ast)
    ast = ast.resolve_free_vars(builtin)
    ast = ast.resolve_block_refs(builtin)
    program = Program(filename, ast, builtin, target_type)
    out = io.StringIO()
    program.generate_assembly(out)
    asm = out.getvalue()
    #print(asm)
    return asm.encode('utf8')

def run_assembler(target_type, input, outfile):
    p = subprocess.Popen(target_type.get_assembler_args(outfile), stdin=subprocess.PIPE)
    p.communicate(input)
    if p.returncode != 0:
        sys.exit(p.returncode)

def run_linker(target_type, infile, outfile):
    p = subprocess.Popen(target_type.get_linker_args(infile, outfile))
    p.communicate()
    if p.returncode != 0:
        sys.exit(p.returncode)

def compile_file(filename, target_platform=default_target_platform):
    if target_platform not in target_platform_map:
        raise OmeFileError('ome', 'unsupported target platform: {0}-{1}'.format(*target_platform))
    target_type = target_platform_map[target_platform]
    asm = compile_file_to_assembly(filename, target_type)
    exe_file = os.path.splitext(filename)[0]
    obj_file = exe_file + '.o'
    run_assembler(target_type, asm, obj_file)
    run_linker(target_type, obj_file, exe_file)

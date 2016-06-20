#!/usr/bin/env python3

import json
import sys

import clap

model = {}
with open('./ui.json', 'r') as ifstream: model = json.loads(ifstream.read())


args = list(clap.formatter.Formatter(sys.argv[1:]).format())

command = clap.builder.Builder(model).build().get()
parser = clap.parser.Parser(command).feed(args)
checker = clap.checker.RedChecker(parser)

try:
    fail = True
    checker.check()
    fail = False
except clap.errors.UnrecognizedOptionError as e:
    print('unrecognized option found: {0}'.format(e))
except clap.errors.UIDesignError as e:
    print('misdesigned interface: {0}'.format(e))
except clap.errors.MissingArgumentError as e:
    # This exception is raised when an option requests an argument but is
    # not present on the command line.
    # In the example program, the `--repeat` option may raise this exception.
    print('missing argument to an option: {}'.format(e))
except clap.errors.ConflictingOptionsError as e:
    # This exception is raised when two or more conflicting options are passed on
    # the command line.
    # A typical example of such situation is passing both `--verbose` and `--silent`
    # to a program.
    # In the example program, the `--uppercase` and `--lowercase` options conflict
    # with each other.
    print('conflicting options given: {}'.format(e))
except clap.errors.InvalidOperandRangeError as e:
    # This exception is raised when a program is called with invalid number of
    # operands, e.g. too few or too many.
    # An operand is a command line argument that is not an option, not an option
    # argument, and not a subcommand name.
    # Exapmle using Git:
    #
    #   git checkout -b foo/bar
    #                   ^^^^^^^
    #                   This is an operand.
    #
    # In the example program this is triggered by passing no operands.
    print('invalid number of operands: {}'.format(e))
except Exception as e:
    print('unhandled exception: {0}: {1}'.format(type(e), e))
finally:
    if fail: exit(1)
    ui = parser.parse().ui().finalise()

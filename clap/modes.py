#!/usr/bin/env python3


"""This is interface which enables use of modes.
It is basically a set of parsers from which one is chosen according
to the *mode-keyword* found in input list.

*mode-keyword* is first item in the list that does not look like option.
Example:

    foo bar --hello-world

Here, `bar` is mode of program `foo` called with option `--hello-world`.
A more sphisticated example could be:

    foo --verbose --log './foo.log' bar --hello-world

In this example a couple of options is passed before *mode-keyword* is found.
These are global options which are common to all modes.

When using `modes.Parser()` remember to add global options after all modes has been set.
Otherwise, you'll get an `UnknownOptionError` when trying to pass global option.
"""

import warnings

from clap import base, errors, option, shared

class Parser():
    """Object implementing modes functionality.
    """
    def __init__(self, argv=[], default='', empty=True):
        self._argv = argv
        if empty: self._modes = {'': base.Base()}
        else: self._modes = {'': base.Base()}
        self._mode = ''
        self.default = default
        self.parser = None
        self._operands = []

    def __contains__(self, option):
        """If you check whether Parser() contains an option or not, general one and every mode-parser
        is checked.
        """
        return option in self.parser

    def __str__(self):
        return self.mode

    def feed(self, argv):
        """Feeds input arguments list to parser.
        """
        self._argv = argv
        self.parser = None
        self.mode = ''

    def _append(self, option, local=False):
        """Appends option to sub-parsers.
        """
        if local:
            self._modes['']._append(option)
        else:
            for name in self._modes: self._modes[name]._append(option)

    def addOption(self, short='', long='', help='', arguments=[],
                  requires=[], wants=[],
                  required=False, not_with=[],
                  conflicts=[], local=False):
        """Adds an option to the list of options recognized by parser.
        Available types are: int, float and str.

        If you `addOption` it is added to the general parser and all mode-parsers unless
        `local` is passed.
        """
        new = option.Option(short=short, long=long, help='', arguments=arguments,
                            requires=requires, wants=wants,
                            required=required, not_with=not_with,
                            conflicts=conflicts)
        self._append(new, local)
        return new

    def addMode(self, name, parser):
        """Adds mode to Modes() or overwrites old definition.
        """
        self._modes[name] = parser

    def has(self, mode):
        """Returns True if Modes() has given mode.
        """
        return mode in self.modes

    def _modeindex(self):
        """Returns index of first non-option-like item in input list.
        Returns -1 if no mode was found but all input was scanned.

        Quits searching as soon as `--` breaker is found.
        """
        index, i = -1, 0
        while i < len(self._argv):
            item = self._argv[i]
            if item == '--': break
            if shared.lookslikeopt(item):
                # if item is an option get list of all its arguments and
                # increase the counter accordingly;
                # needed for support for options with multiple arguments because
                # otherwise _modeindex() would treat second argument as a mode
                args = self.type(item)
                if args is not None: n = len(self.type(item))
                else: n = 0
                i += n
            if not shared.lookslikeopt(item):
                if i == 0 or not self.type(self._argv[i-1]): index = i
                if index > -1: break
            i += 1
        return index

    def define(self):
        """Defines mode to use and sets correct parser.
        """
        index = self._modeindex()
        if index > -1:
            mode = self._argv[index]
            n = 1
        else:
            mode = self.default
            index = 0
            n = 0
        if mode not in self._modes: raise errors.UnrecognizedModeError(mode)
        self.parser = self._modes[mode]
        input = self._argv[:index] + self._argv[index+n:]
        self.parser.feed(input)
        self.mode = mode
        return mode

    def check(self):
        """Checks input list for errors.
        """
        self.define()
        self.parser.check()

    def parse(self):
        """Parses input list.
        """
        warnings.warn('clap.modes.Parser will be remove in version 0.9.1: use clap.parser.Parser instead', DeprecationWarning)
        self.parser.parse()

    def finalize(self):
        """Commits all actions required to get a usable parser.
        """
        self.define()
        self.parse()
        return self

    def get(self, s):
        """Returns option's argument.
        """
        return self.parser.get(s)

    def getoperands(self):
        """Returns operands passed to the program.
        """
        return self.parser.getoperands()

    def type(self, s):
        """Returns information about type(s) given option takes as its arguments.
        """
        t = None
        if self.parser: t = self.parser.type(s)
        else:
            for m in self._modes:
                for o in self._modes[m]._options:
                    t = self._modes[m].type(s)
                    if t is not None: break
                if t is not None: break
        return t

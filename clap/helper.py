"""This module holds logic responsible for turning JSON representations into usable UI descriptions, i.e.
Python objects representing modes and options.
"""

import json
import warnings

from . import option
from . import mode
from . import shared
from . import errors


def makelines(s, maxlen):
    """Split string into words (space separated, no fancy tokenising here) and
    join them into lines of at most `maxlen` width.
    """
    lines = []
    words = s.split(' ')
    line = ''
    i = 0
    while i < len(words):
        word = words[i]
        if len(line + word) <= maxlen-1:
            line += (word + ' ')
            i += 1
        else:
            lines.append(line)
            line = ''
    if line: lines.append(line)
    return lines


def renderOptionHelp(option, help=True):
    """Renders a single help line for passed option.
    if `help` is passed as false, it will not render help message but only
    short and long variants.
    """
    message = (option['short'] if option['short'] else '    ')
    if option['short'] and option['long']: message += ', '
    message += (option['long'] if option['long'] else '')
    if option.params():
        message += ('=' if option['long'] else ' ')
        message += ' '.join(['<{0}>'.format(i) for i in option.params()])
    if help: message += (' - {0}'.format(option['help']) if option['help'] else '')
    return message

def _getoptionlines(mode, indent='    ', level=1):
    """Renders lines with options' help messages.
    The lines with actual option help strings, have only put short and long
    variants into their strings to make nice padding available, so all options'
    descriptions begin on the same column.
    Renderer handles the help messages (if they are present).
    """
    lines = []
    for scope in ['global', 'local']:
        if mode.options(group=scope): lines.append( ('str', indent*(level) + '{0} options:'.format(scope)) )
        for o in mode.options(group=scope): lines.append( ('option', indent*(level+1) + renderOptionHelp(o, False), o) )
        if mode.options(group=scope): lines.append( ('str', '') )
    return lines


def _cleanback(lines):
    """Removes whitespace-only lines from the end of lines list.
    """
    while True:
        type, content = lines[-1]
        if type != 'str': break
        if content.strip() == '': lines.pop(-1)
        else: break
    return lines


class Helper:
    """Class used to build help screens for CLAP UIs.

    It can build abbreviated and full screens, display usage information,
    example program invocations, nested commands and their options, etc.

    The output is modelled after the 'git --help' output and 'gem' output,
    in the ways of how usage and examples are shown and how options are aligned; and
    after man pages in how option parameters are shown.
    """
    def __init__(self, progname, mode):
        self._mode = mode
        self._indent = {'string': '   ', 'level': 0}
        self._progname = progname
        self._maxlen = 140
        self._opt_desc_start = 0
        self._lines = []

    def addUsage(self, line):
        """Add usage line.
        """
        warnings.warn('this method is deprecated: usage exampels are taken from JSON representations')
        self._usage.append(line)
        return self

    def setmaxlen(self, n):
        """Set the maximum lenght of a single line on help screen.
        Descriptions will be adjusted to match it.
        """
        self._maxlen = n
        return self

    def _genexamples(self):
        """Generate `examples` part of help screen.
        It will list example invocations of the program and
        their descriptions.
        """
        lines = []
        examples = (self._mode._doc['examples'] if 'examples' in self._mode._doc else [])
        if examples: lines.append( ('str', 'Examples:') )
        for i, example in enumerate(examples):
            if 'line' not in example: continue
            lines.append( ('str', '{0}{1} {2}'.format(self._indent['string'], self._progname, example['line'])) )
            if 'desc' in example and example['desc']:
                lines.append( ('str', '{0}{0}{1}'.format(self._indent['string'], example['desc'])) )
                if i < len(examples)-1: lines.append( ('str', '') )
        if lines: self._lines.extend(lines)
        if self._lines and lines: self._lines.append( ('str', '') )

    def _genusage(self):
        """Generate `usage` part of help screen.
        Modelled after `git --help` invocation usage message.
        """
        for key in ['usage']:
            head = '{0}: {1} '.format(key, self._progname)
            indent = len(head) * ' '
            lines = []
            what = (self._mode._doc[key] if key in self._mode._doc else [])
            if what: lines.append( ('str', head + what[0]) )
            for line in what[1:]: lines.append( ('str', indent + line) )
            self._lines.extend(lines)
            if self._lines: self._lines.append( ('str', '') )

    def _gencommandhelp(self, mode, name, level=0, longest=0):
        """Generate lines with command help message.
        """
        if not longest: longest = len(name)
        SPACING = (2 if longest else 0)  # CONF?
        lines = []
        text = '{0}{1}'.format(name.ljust(longest+SPACING), mode._doc['help'].strip())
        first = makelines(text, self._maxlen)[0]
        lines.append( ('str', ((self._indent['string']*level) + first)) )
        for l in makelines(text[len(first):], (self._maxlen-len(name)-3)):
            indent = self._indent['string']*level
            padding = ' ' * (len(name) + SPACING)
            l = '{0}{1}{2}'.format(indent, padding, l)
            lines.append( ('str', l) )
        lines = _cleanback(lines)
        if text: lines.append( ('str', '') )
        return lines

    def _gencommandslines(self, mode, name, level, deep):
        lines = []
        modes = sorted(mode.modes())
        longest = 0
        for m in modes:
            if len(m) > longest: longest = len(m)
        for m in modes:
            submode = mode.getmode(m)
            if deep:
                lines.extend(self._genmodelines(submode, name=m, level=level+2))
                lines.append( ('str', '') )
            else:
                lines.extend(self._gencommandhelp(submode, name=m, level=level+2, longest=longest))
        return lines

    def _genmodelines(self, mode, level=0, name='', deep=True):
        lines = []
        self._lines.extend(self._gencommandhelp(mode, name, level=level))
        self._lines.extend(_getoptionlines(mode, indent=self._indent['string'], level=level+1))
        if mode.modes(): self._lines.append( ('str', ((self._indent['string']*(level+1)) + 'commands:')) )
        self._lines.extend(self._gencommandslines(mode, name, level, deep))
        return lines

    def gen(self, deep=True):
        """Generate help screen.
        """
        warnings.warn('deprecated: use .full() method instead')
        return self.full(deep)

    def usage(self):
        """Generate usage help screen.
        """
        self._genusage()
        return self

    def examples(self):
        """Generate examples help screen.
        """
        self._genexamples()
        return self

    def full(self, deep=True):
        """Generate full help screen.
        """
        self._genusage()
        self._genexamples()
        self._lines.extend(self._genmodelines(mode=self._mode, deep=deep))
        return self

    def render(self):
        """Performs final rendering of token-lines into single string
        that can be printed out as a help message.
        """
        for i in self._lines:
            if i[0] == 'option':
                if len(i[1]) > self._opt_desc_start: self._opt_desc_start = len(i[1])
        self._opt_desc_start += 2

        lines = []
        for no, i in enumerate(self._lines):
            if i[0] == 'str':
                type, string = i
            elif i[0] == 'option':
                type, string, opt = i
                while len(string) < self._opt_desc_start: string += ' '
                string += ('- {0}'.format(opt['help']) if opt['help'] else '')
            else:
                raise Exception('line {0}: unknown type: {1}: {2}'.format(no, i[0], i))
            lines.append(string)
        while lines:
            if lines[-1] == '': lines.pop(-1)
            else: break
        return '\n'.join(lines)


class HelpRunner:
    """Class used to run help screen logic, basing on the contents of parsed UI passed to it.
    """
    def __init__(self, ui, program):
        """Parameters:

        - ui:       parsed UI,
        - program:  program name (as string),
        """
        self._ui = ui
        self._program_name = program
        self._displayed = False
        self._options, self._commands = ['-h', '--help'], ['help']
        self._ignorecmds = ['']

    def _byoptions(self):
        """Display help if options tell you to do so.
        """
        cui, ui = self._ui, self._ui
        present = False
        while True and str(ui.down()) != 'help':
            for i in self._options:
                if i in cui:
                    present = True
                    break
            if cui.islast(): break
            cui = cui.down()
        if present:
            helper = Helper(self._program_name, cui._mode).setmaxlen(n=70)
            print(helper.gen(deep=('--verbose' in cui)).render())
            self._displayed = True

    def _byhelpcommand(self):
        """Display help message when 'help' command is encountered.
        """
        ui = (self._ui if str(self._ui) else self._ui.down())
        if str(ui) != 'help': return
        items = ui.operands()
        if not items:
            helper = Helper(self._program_name, ui.up()._mode).setmaxlen(n=70)
            print(helper.gen(deep=('--verbose' in ui or '--help' in ui)).render())
            self._displayed = True
        if self._displayed: return
        mode, done = ui.top()._mode, False
        for i, item in enumerate(items):
            if shared.lookslikeopt(item):
                message = (renderOptionHelp(mode.getopt(item)).strip() if mode.accepts(item) else 'unrecognised option: no help available')
                print('(option) {0}'.format(message))
                self._displayed = True
                break
            elif not mode.hasmode(item):
                message = 'unrecognised mode: no help available'
                print('{0}'.format(message))
                self._displayed = True
                break
            elif i < len(items):
                mode = mode.getmode(item)
        if not self._displayed:
            helper = Helper(self._program_name, mode).setmaxlen(n=70)
            print(helper.gen(deep=('--verbose' in ui or '--help' in ui)).render())
            self._displayed = True

    def adjust(self, options=None, commands=None, ignorecmds=None):
        """Adjusting help runner to match current program specifics.
        'options' is a list of options (as full names, e.g. '-h' and '--help') that shall trigger help screen display,
        'commands' is a list of commands (their names) that shall trigger help screen display,
        'ignorecmds' is a list of commands that can be trimmed from the to of given UI (in order in which they appear in this list),
        """
        if options is not None: self._options = options
        if commands is not None: self._commands = commands
        if ignorecmds is not None: self._ignorecmds = ignorecmds
        return self

    def _ignore(self):
        """Check if given UI can or should be adjusted for Help Runner.
        By default, help runner ignores the empty - '' - command which is
        the first and default command for any program whose UI is built by CLAP.
        """
        for i in self._ignorecmds:
            if str(self._ui) == i: self._ui = self._ui.down()
            else: break

    def run(self):
        """Runs whole logic.
        """
        self._ignore()
        if '--usage' in self._ui:
            print(Helper(self._program_name, self._ui.top()._mode).usage().render())
            self._displayed = True
        if '--examples' in self._ui:
            print(Helper(self._program_name, self._ui.top()._mode).examples().render())
            self._displayed = True
        if not self._displayed: self._byoptions()
        if not self._displayed: self._byhelpcommand()
        return self

    def displayed(self):
        """Returns true if any help was displayed.
        Usually, this means that no further work shall be done by the program so
        this is convinience method.
        """
        return self._displayed

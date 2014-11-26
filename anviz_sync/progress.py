# -*- coding: utf-8 -*- 

"""
    anviz_progress.progress
    ~~~~~~~~~~~~~~~~~~~~~~~

    Module that contains a ProgressBar object definition.

    :copyright: (c) 2014 by Augusto Roccasalva.
    :license: BSD, see LICENSE for more details.
"""

import sys

# Fancy progress ala (pacman-color) ArchLinux
_colors = {
    'BOLD': u'\x1b[01;1m',
    'RED':    u'\x1b[01;31m',
    'GREEN':  u'\x1b[01;32m',
    'YELLOW': u'\x1b[01;33m',
    'BLUE':   u'\x1b[01;34m',
    'PINK':   u'\x1b[01;35m',
    'CYAN':   u'\x1b[01;36m',
    'NORMAL': u'\x1b[0m',
    'red':    u'\x1b[0;31m',
    'green':  u'\x1b[0;32m',
    'yellow': u'\x1b[0;33m',
    'blue':   u'\x1b[0;34m',
    'pink':   u'\x1b[0;35m',
    'cyan':   u'\x1b[0;36m',
    'normal': u'\x1b[0m',
    'cursor_on':  u'\x1b[?25h',
    'cursor_off': u'\x1b[?25l',
}

_unset = object()


class ProgressBar(object):
    MAX_MARKERS = 27
    indicator = '\x1b[K%s%s%s\r'
    end_color = _colors['NORMAL']

    def __init__(self, name, max_steps, stream=sys.stdout,
                 color='BOLD', sec_color='BLUE'):
        self.name = name
        self.start_color = _colors.get(color, _colors['NORMAL'])
        self.sec_start_color = _colors.get(sec_color, _colors['NORMAL'])
        self.act_color = _colors['NORMAL']
        self._stream = stream
        self._color_n = 2*len(self.start_color) + len(self.sec_start_color) +\
                        3*len(self.end_color)
        self.max_steps, self.current_steps = max_steps, 0
        self.steps_per_marker = float(max_steps) / self.MAX_MARKERS
        self.current_markers, self.current_percentage = 0, 0
        self.set_activity(None)

    def set_activity(self, activity, color=None, flush=True):
        self.current_activity = activity
        self.act_color_name = color
        if flush:
            self._stream.write(self.indicator % self._build_cols(
                self.current_percentage, self.current_markers
            ))
            self._stream.flush()

    def step(self, step_increment = 1):
        self.current_steps += step_increment
        if self.max_steps != 0:
            new_markers = int(self.current_steps / self.steps_per_marker)
            new_percentage = int(self.current_steps * 100 / self.max_steps)
        else:
            new_markers = self.max_steps
            new_percentage = 100

        if (step_increment == 0) or\
           (new_percentage != self.current_percentage) or\
           (self.current_markers < new_markers):
            self.current_percentage = new_percentage
            self.current_markers = new_markers
            self._stream.write(
                self.indicator % self._build_cols(new_percentage, new_markers)
            )
            self._stream.flush()

    def finish(self, msg=_unset, msg_color='normal'):
        if msg is not _unset:
            self.set_activity(msg, msg_color)
        self._stream.write(
            self.indicator % self._build_cols(100, self.MAX_MARKERS)
        )
        self._stream.write(u'\n')
        self._stream.flush()

    def _build_cols(self, percentage, markers):
        if self.current_activity is None:
            name = "%-42s" % self.name[:42]
            activity = ""
        else:
            if self.act_color_name is not None and\
                    self.act_color_name in _colors:
                self.act_color = _colors[self.act_color_name]
            else:
                if self.act_color is None:
                    self.act_color = _colors['NORMAL']

            alen = len(self.current_activity)
            nlen = 42 - alen
            name = ("%%-%ds" % nlen) % self.name[:nlen]
            activity = self.act_color + ("%%%ds" % alen) %\
                       self.current_activity + _colors['NORMAL']

        sc, ssc, ec = self.start_color, self.sec_start_color, self.end_color
        left = u"%s*%s %s%s%s %s [" % (ssc, ec, sc, name, ec, activity)
        right = u"] %s%3d%%%s" % (sc, percentage, ec)
        bar = (u'#'*markers+'-'*self.MAX_MARKERS)[:self.MAX_MARKERS]
        return left, bar, right


class ProgressDummy(object):

    def set_activity(self, *args):
        pass

    def step(self):
        pass

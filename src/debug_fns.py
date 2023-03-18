################################################################
# CSCI 336/636 Information Retrieval
# Spring 2023
#
# debug_fns.py
#   - Debugging routines and timers
#
# New in v0.4: DEBUG flag
#  * Allow messages to be skipped using a flag
#
# New in v0.3: DebugTimer
#  * Class to create objects to record labeled time stamps
#  * Use constructor to record/'start' timer
#  * Use 'check' and 'qcheck' to record duration from last
#    recorded time along with a label
#  * DebugTimer.check - prints msg at terminal
#  * DebugTimer.qcheck - ('quiet' check) record time without printing
#
# New in v0.2: 8 message types:
# * check, ncheck, dcheck, dncheck
# * pcheck, npcheck, dpcheck, dnpcheck
#
# Prefix 'n': newline after message
# Prefix 'd': puts prefix '[DEBUG] ' before message
#
# Author: R. Zanibbi, Oct 2022, Mar 2023
################################################################

import time
import sys

# Added global flag to allow messages to be skipped when set to False
# rather than having to manually remove messages
DEBUG = False


##################################
# Print to standard error
##################################
# Source: https://stackoverflow.com/questions/5574702/how-do-i-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


##################################
# Basic debug messages
# * check - check expression
# * pcheck - pause and check
##################################
# Allow strings at start + end of messages
def check(message, expression, msg_start="", msg_end="", pause=False):
    if not DEBUG:
        return

    if msg_start != "":
        print(msg_start, message, ":" + msg_end, expression)
    elif msg_end != "" and msg_end[-1] == "\n":
        # DEBUG -- separate to avoid extra space for expressions on new lines.
        print(message, ":")
        print(expression)
    else:
        print(message, ":" + msg_end, expression)

    # Add newline or pause message
    if pause:
        input("Press any key to continue...\n")


def pcheck(message, expression, msg_start="", msg_end=""):
    check(message, expression, msg_start, msg_end, pause=True)


##################################
# Print newline after ':'
# ** Useful for matrices
##################################
def ncheck(message, expression):
    check(message, expression, msg_end="\n")


def npcheck(message, expression):
    pcheck(message, expression, msg_end="\n")


##################################
# Insert debug tag at start
##################################
def dcheck(message, expression):
    check(message, expression, msg_start="[DEBUG]", msg_end="")


def dncheck(message, expression):
    check(message, expression, msg_start="[DEBUG]", msg_end="\n")


def dpcheck(message, expression):
    pcheck(message, expression, msg_start="[DEBUG]", msg_end="")


def dnpcheck(message, expression):
    pcheck(message, expression, msg_start="[DEBUG]", msg_end="\n")


################################################################
# Object to record timing information with messages
# Please Note: Records wall-clock time, and not time running
#              on the processor.
################################################################
class DebugTimer:
    # Date and time string
    @staticmethod
    def date_str(time_secs):
        return time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time_secs))

    @staticmethod
    def entry_str(entry):
        (label, clock_time, duration) = entry
        return "{:>10.4f}s  {}".format(duration, label) + "\n"

    # Main data is a list of triples with a label, current clock time, and difference from
    # the previous entry in seconds
    def __init__(self, init_label="Timer"):
        self.entries = [(init_label, time.time(), 0)]

    # String summary of timing information + labels
    def __str__(self):
        head = self.entries[0]
        tail = self.entries[-1]

        # Report first label and start time
        out_string = "[ Timer: " + head[0] + " ]\n"
        out_string += "Started: " + DebugTimer.date_str(head[1]) + "\n"

        # Report start time and checkpoints
        out_string += "Total Duration: {:.4f} seconds".format(tail[1] - head[1]) + "\n"
        for i in range(1, len(self.entries)):
            out_string += DebugTimer.entry_str(self.entries[i])

        return out_string

    # Start again.
    def reset(self, start_label="Reset Timer"):
        self.entries = [(start_label, time.time(), 0)]

    # Add next time step with a label.
    # Optionally print last duration with timer name and message (single line)
    def check(self, label="Check", show=True):
        last_time = self.entries[-1][1]
        current_time = time.time()
        self.entries.append((label, current_time, current_time - last_time))

        if show:
            head = self.entries[0]
            print(
                "[ Timer: " + head[0] + " ] " + DebugTimer.entry_str(self.entries[-1])
            )

    # ('quiet') Add next time step with a label, do *not* print a message
    def qcheck(self, qlabel="Check"):
        self.check(qlabel, False)

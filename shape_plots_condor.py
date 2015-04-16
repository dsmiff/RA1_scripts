#!/usr/bin/env python
"""
Interface for running on HTCondor

Usage: call in HTcondor script with arguments:

$(process) <myrootfiles> <myoutdir> --other_args_here

where the pther_args_here can be any args that would be used when running
shape_plots.py locally, e.g. --qcd --exclusive_HT

This script essentially just maps a number into a variable, and sets the correct ROOTdir
and out_dir in shape_plots.
"""

import argparse
import shape_plots as plotr

parser = argparse.ArgumentParser()
parser.add_argument("varID", type=int, help="ID number to specify variable")
parser.add_argument("input", help="dir for intput root files")
parser.add_argument("output", help="output dir")
parser.add_argument("other", help="all other options to pass to shape_plots", default="", nargs=argparse.REMAINDER)
args = parser.parse_args()
print args

plotr.ROOTdir = args.input
plotr.out_dir = args.output
var = plotr.plot_vars[args.varID:args.varID + 1]  # add the varaible to the args passes to shape_plots
args.other.append("-v")
args.other.append(var[0])
print args.other
plotr.main(args.other)
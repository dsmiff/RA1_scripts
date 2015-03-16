#!/usr/bin/env python
"""
Interface for running on HTCondor

Usage: call in HTcondor script with arguments:

$(process) ./myrootfiles ./myoutdir --excl
"""

import shape_plots as plotr
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("ID", type=int, help="ID number to specify variable")
parser.add_argument("ROOTdir", help="dir for root files")
parser.add_argument("OUTdir", help="output dir")
parser.add_argument("--excl", action="store_true",
                    help="run exclusive HT bins (default is inclusive HT)")
args = parser.parse_args()


var = plotr.plot_vars[ID:ID + 1]
plotr.run_over(root_dir=args.ROOTdir, out_dir=args.OUTdir, plot_vars=var,
               njet=plotr.n_j, btag=plotr.n_b, htbins=plotr.HTbins,
               exclusive_HT=args.excl, check=False, custom_title=plotr.title)

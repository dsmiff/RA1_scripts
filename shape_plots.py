#!/usr/bin/env python
"""
This script makes data VS background plots, but gets the backgrounds from
DATA control region shape, not MC. To do this, we define several control regions
(for each BG source), use MC to calculate transfer factors, then scale the
data control region plot by that factor. Oh yeah and whack in stat + syst
uncertainties, latter from closure tests. (NB syst invalid for fine jet multiplicity)

We can do this for bins of Njets, Nbtag, HT. And we look at lots of variables.

And we make it look b-e-a-utiful.

Robin Aggleton

"""

import argparse
import plot_grabber as grabr
import ROOT as r
from itertools import product, izip
import math
import numpy as np
import os
import array
from Ratio_Plot import Ratio_Plot
import sys
import make_component_pres as pres

r.PyConfig.IgnoreCommandLineOptions = True
r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

# Define region bins
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][:]
n_j = ["le3j", "ge4j", "ge2j"][:]
n_j_fine = ["eq2j", "eq3j", "eq4j", "ge5j"][:] # fine jet binning
# n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b", "ge2b", "ge3b", "ge4b"][:]
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b", "ge2b", "ge4b"][:]


# input files, output directories, which HTbins to run over
ROOTdir, out_dir, HTbins = [
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/", "11Dec_aT_0p53_forRobin_v0_new", allHTbins[:]],  #re-run
    ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1", "./01Dec_aT_0p53_globalAlphaT_v1_new/", allHTbins[3:]],  # alphaT in control regions as well
    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0", "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0_new/", allHTbins[:]],  # dPhi* >0.3 in SR, fine jet multiplicity, fixed cross-cleaner
    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0", "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0_new/", allHTbins[:]]  # dPhi* <0.3 in SR, fine jet multiplicity, fixed cross-cleaner
    # ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0_MuonInJet/", "11Dec_aT_0p53_forRobin_v0_MuonInJet", allHTbins[3:]],  # muon in jet
    # ["/Users/robina/Dropbox/AlphaT/Root_Files_04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0", "./04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0_new/", allHTbins[:]],  # dPhi* <0.3 in SR - old
][-1]

# Variable(s) you want to plot
plot_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "EffectiveMass", "Number_Good_verticies",
             "JetMultiplicity", "ComMinBiasDPhi_acceptedJets"]
plot_vars = ["ComMinBiasDPhi_acceptedJets", "MET_Corrected", "MHT", "LeadJetEta", "Number_Good_verticies"][:] # for the website plots?

# Custom bins for AlphaT per Rob's suggestion
alphaT_bins = np.concatenate((np.arange(0.5, 1.0, 0.05), np.arange(1.0, 5.5, 0.5)))

dphi_bins = np.arange(0.0, 4.1, 0.1)

rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
            "ComMinBiasDPhi_acceptedJets": dphi_bins, "AlphaT": alphaT_bins,
            "MET_Corrected": 8, "HT": 10, "LeadJetPt": 5, "SecondJetPt": 5,
            "EffectiveMass": 10, "MHT": 4}

log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]


def do_a_plot_HT_incl(var="ComMinBiasDPhi_acceptedJets", njet="eq3j", btag="eq0b"):
    # Inclusive HT
    rebin = rebin_d[var] if var in rebin_d else 2
    log = True if var in log_these else False
    plot = Ratio_Plot(ROOTdir, out_dir, var, njet, btag, HTbins, rebin, log)
    plot.make_plots()
    plot.save()


def do_a_plot_HT_excl(var="AlphaT", njet="le3j", btag="eq0b"):
    # exclusive HT bins - do one by one
    for ht in HTbins:
        rebin = rebin_d[var] if var in rebin_d else 2
        log = True if var in log_these else False
        plot = Ratio_Plot(ROOTdir, out_dir, var, njet, btag, [ht], rebin, log)
        plot.plot_components = True
        plot.make_plots()
        plot.save()
    # optionally can do component plots as well for this var
    # lo = HTbins[0].split("_")[0]
    # hi = HTbins[-1].split("_")[1] if "_" in HTbins[-1] else "Inf"
    # print "Make component pres"
    # pres.make_pres(plot_dir=out_dir, var=var, njet=njet, btag=btag, lo_ht=lo, hi_ht=hi)


if __name__ == "__main__":
    """
    Mainly parse user args.

    Note that by default, this script runs over all vars, all njet, all btag bins,
    for INCLUSIVE HT. There are flags if you want to vary any of these.
    """

    print "Making lots of data VS bg plots..."

    parser = argparse.ArgumentParser()
    parser.add_argument("--do_exclusive_HT", help="if you want plots done in HT bins rather than for inclusive HT", action='store_true', default=False)
    parser.add_argument("-v", "--var", help=("variable to plot (if undefined, runs over all)"), nargs="+")
    parser.add_argument("-j", "--njet", help=("number of jets (if undefined, runs over all)"), nargs="+")
    parser.add_argument("-b", "--btag", help=("number of btags (if undefined, runs over all)"), nargs="+")
    args = parser.parse_args()

    # Figure out which vars/njet/btags options to run over
    # Do the set intersection to validate input (silently tho, tut tut)
    # If user specified, then run over those only, if not then all possible
    run_vars = plot_vars[:]
    run_njet = n_j_fine[:] if "fineJetMulti" in ROOTdir else n_j[:]
    run_btag = n_b[:]
    if args.var:
        run_vars = list(set(plot_vars) & set(args.var))
    if args.njet:
        run_njet = list(set(run_njet) & set(args.njet))
    if args.btag:
        run_btag = list(set(n_b) & set(args.btag))

    print run_vars, run_njet, run_btag

    for v, j, b in product(run_vars, run_njet, run_btag):
        if args.do_exclusive_HT:
            do_a_plot_HT_excl(var=v, njet=j, btag=b)
        else:
            do_a_plot_HT_incl(var=v, njet=j, btag=b)

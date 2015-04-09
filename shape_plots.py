#!/usr/bin/env python
"""
This script makes data VS background plots, but gets the backgrounds from
DATA control region shape, not MC.

Usage, see: python shape_plots.py --help

By default, it runs over all variables, btag bins, njet bins, for inclusive HT

To setup for a new set of plots:

1) make sure n_j/n_j_fine, n_b include the bins you want
2) setup ROOTdir, out_dir, HTbins, title, plot_vars, rebin values.
For each set of plots, we add another list (with those vars) to the Big List.
Make sure you select the correct entry.

3) run

Note that you can optionally run over inclusive or exclusive HT bins,
over specfic vars and specfic bins, using the command-line options.

TODO: better structure for holding vars, rebin factors, log status etc,
stop with the global vars,

Robin Aggleton

"""

import argparse
import ROOT as r
import plot_grabber as grabr
from itertools import product, izip
import math
import numpy as np
import os
import array
from Prediction_Plot import PredictionPlot
import sys
import make_component_pres as pres

r.PyConfig.IgnoreCommandLineOptions = True
r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

###############################################
# Define region bins - inclusive and exclusive
###############################################
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"]# "200_upwards", "375_upwards"][:]

n_j = ["le3j", "ge4j", "ge2j"][:]
n_j_fine = ["eq2j", "eq3j", "eq4j", "ge5j"][:] # fine jet binning
# n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b", "ge2b", "ge3b", "ge4b"][:]
# n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b", "ge2b", "ge4b"][:]
n_b = ["eq0b", "eq1b", "eq2b", "ge1b", "ge2b", "ge0b"][:]


###############################################
# Common set of variables - use these, or override below
###############################################
# all_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
#              "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
#              "MHTovMET", "EffectiveMass", "Number_Good_verticies",
#              "JetMultiplicity", "ComMinBiasDPhi_acceptedJets"]
all_vars = ["ComMinBiasDPhi_acceptedJets", "AlphaT", "ComMinBiasDPhi",
             "JetMultiplicity", "HT", "Number_Btags", "CommonJetPt",
             "CommonJetEta", "MET", "MET_Corrected", "MHT", "Number_Good_verticies"]
all_vars = ["ComMinBiasDPhi_acceptedJets", "AlphaT", "ComMinBiasDPhi",
             "HT", "MET", "MET_Corrected", "MHT"]


###############################################
# Custom bins & log axis - can override below
###############################################
alphaT_binning = np.concatenate((np.arange(0.5, 1.0, 0.05), np.arange(1.0, 5.5, 0.5)))

dphi_binning = np.arange(0.0, 3.6, 0.1)
# make sure it's anumpy array NOT a py list - cos ROOT is stooopid
# ht_binning = np.arange(775,1175,100)
# np.array([200, 275, 325, 375, 475, 575, 675, 775, 875, 975, 1075, 1500][-5:])
ht_binning = 25

# rebinning values can either be a number (number of bins to combine) or
# a numpy array of bin edges
rebin_default = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                 "ComMinBiasDPhi_acceptedJets": dphi_binning, "ComMinBiasDPhi": dphi_binning,
                 "AlphaT": alphaT_binning, "MET_Corrected": 5, "MET": 5,
                 "HT": 10, "LeadJetPt": 5, "SecondJetPt": 5,
                 "EffectiveMass": 10, "MHT": 10}

log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "ComMinBiasDPhi","HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]


###############################################
# input files, output directories, which HTbins to run over,
# custom title on plot (in addition to binning info), variables to plot,
# rebinning options. Note that for rebin values,
# specifying anything other than rebin_defaults will cause those vars
# to use those values to be used, all other vars will use values in rebin_defaults
#
# ONLY SELECT ONE ENTRY
###############################################
ROOTdir, out_dir, HTbins, title, plot_vars, rebin_d = [
    # ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/",
    #     "11Dec_aT_0p53_forRobin_v0_new",
    #     allHTbins[:],
    #     "#alpha_{T} > 0.53 in signal region",
    #     all_vars,
    #     rebin_default],  #re-run

    # ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1",
    #     "./01Dec_aT_0p53_globalAlphaT_v1_new/",
    #     allHTbins[3:],
    #     "#alpha_{T} > 0.53 in all regions",
    #     all_vars,
    #     rebin_default],  # alphaT in control regions as well

    # ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0_MuonInJet/",
    #     "11Dec_aT_0p53_forRobin_v0_MuonInJet",
    #     allHTbins[3:],
    #     "#alpha_{T} > 0.53 in signal region",
    #     all_vars,
    #     rebin_default],  # muon in jet

    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0",
        "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0_new/",
        allHTbins[:],
        "#alpha_{T} > 0.53 in signal region, #Delta #phi > 0.3",
        all_vars,
        rebin_default],  # dPhi* >0.3 in SR, fine jet multiplicity, fixed cross-cleaner

    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0",
        "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0_new/",
        allHTbins[:],
        "#alpha_{T} > 0.53 in signal region, #Delta #phi < 0.3",
        all_vars,
        rebin_default],  # dPhi* <0.3 in SR, fine jet multiplicity, fixed cross-cleaner

    ["/Users/robina/AlphaT/Root_Files_14Mar_approved0p55_dPhi_gt0p3_inHadOny_newCC_CSCBeamHalo_v0",
        "./14Mar_approved0p55_dPhi_gt0p3_inHadOny_newCC_CSCBeamHalo_v0_PhotonToDiMuon/",
        allHTbins[:],
        "#gamma #rightarrow #mu#mu, #alpha_{T} > 0.55 in signal region, #Delta#phi^{*}_{min} > 0.3",
        all_vars,
        rebin_default],

   ["/Users/robina/AlphaT/Root_Files_03April_0p507_fullLatest_htTrigs_v0", # qcd excess sideband
        "./03April_0p507_fullLatest_htTrigs_v0/",
        allHTbins[-4:], # only need for 775 onwards
        "#alpha_{T} > 0.507",
        ["ComMinBiasDPhi_acceptedJets", "AlphaT", "HT", "MHT"],
        {"HT": 10, "MHT": 10}],

   ["/Users/robina/AlphaT/Root_Files_07April_0p55_fullLatest_hadOnly_noPhi_v0", # pre-approved analysis
        "./07April_0p55_fullLatest_hadOnly_noPhi_v0/",
        allHTbins[3:], # only need for 375 onwards
        "#alpha_{T} > 0.55",
        ["ComMinBiasDPhi_acceptedJets", "AlphaT", "HT", "MHT"],
        {"HT": 10, "MHT": 10}]
][-2] # SELECT YOUR SAMPLE


def do_a_plot_HT_incl(root_dir, out_dir, var="ComMinBiasDPhi_acceptedJets", njet="eq3j", btag="eq0b", check=False, custom_title="#alpha_{T} > 0.55", qcd=False):
    """Inclusive HT plot"""

    rebin = rebin_d[var] if var in rebin_d else (rebin_default[var] if var in rebin_default else 2)
    log = True if var in log_these else False
    htbins_incl = ["200_upwards", "375_upwards", "775_upwards"][:]
    for ht in htbins_incl:
        # hack - assume we don't have 200_upwards or similar
        # in that case we just pass a list of ht bins that are equivalent
        lower = ht.split("_")[0]
        # Only do this inclusive bin if the user had the range in their HTbins list
        if sum([x.startswith(lower) for x in HTbins]):
            print ht
            htbins = [h for h in HTbins if int(h.split("_")[0]) >= int(lower)]
            plot = PredictionPlot(root_dir, out_dir, var, njet, btag, htbins, rebin, log, custom_title, qcd)
            if check:
                if not os.path.isfile(plot.outname+".png"):
                    print "python shape_plots.py -v %s -j %s -b %s" % (var, njet, btag)
            else:
                plot.make_plots()
                plot.save()


def do_a_plot_HT_excl(root_dir, out_dir, var="AlphaT", njet="le3j", btag="eq0b", htbins=HTbins, check=False, custom_title="#alpha_{T} > 0.55", qcd=False):
    """exclusive HT bins - do one by one"""

    htbins = [h for h in htbins if "upwards" not in h] # filter out inclusive ones
    for ht in htbins:
        rebin = rebin_d[var] if var in rebin_d else (rebin_default[var] if var in rebin_default else 2)
        log = True if var in log_these else False
        plot = PredictionPlot(root_dir, out_dir, var, njet, btag, [ht], rebin, log, custom_title, qcd)
        if check:
            if not os.path.isfile(plot.outname+".png"):
                print "python shape_plots.py -v %s -j %s -b %s --ht %s" % (var, njet, btag, ht)
        else:
            plot.plot_components = True
            plot.make_plots()
            plot.save()
    # optionally can do component presentation as well for this var
    # lo = HTbins[0].split("_")[0]
    # hi = HTbins[-1].split("_")[1] if "_" in HTbins[-1] else "Inf"
    # print "Make component pres"
    # pres.make_pres(plot_dir=out_dir, var=var, njet=njet, btag=btag, lo_ht=lo, hi_ht=hi)


def main():
    """
    Mainly parse user args.

    Note that by default, this script runs over all vars, all njet, all btag bins,
    for INCLUSIVE HT. There are flags if you want to vary any of these.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--exclusive_HT", help="if you want plots done in for all HT bins indivudally rather than for inclusive HT", action='store_true', default=False)
    parser.add_argument("-v", "--var", help="variable to plot (if undefined, runs over all)", nargs="+")
    parser.add_argument("-j", "--njet", help="number of jets (if undefined, runs over all)", nargs="+")
    parser.add_argument("-b", "--btag", help="number of btags (if undefined, runs over all)", nargs="+")
    parser.add_argument("-ht", help="specify HT bin(s) (if undefined, runs over all inclusive)", nargs="+")
    parser.add_argument("-c", "--check", help="don't make plots, just check they exist. prints list of those that don't so you can run them again.", action='store_true', default=False)
    parser.add_argument("--qcd", help="Add in QCD to main plot, but ignore in ratio plot.", action='store_true', default=False)
    args = parser.parse_args()

    # Figure out which vars/njet/btags options to run over
    # Do the set intersection to validate input (silently tho, tut tut)
    # If user specified, then run over those only, if not then all possible
    run_vars = plot_vars[:]
    run_njet = n_j_fine[:] if "fineJetMulti" in ROOTdir else n_j[:]
    run_btag = n_b[:]
    run_ht = HTbins[:]
    if args.var:
        run_vars = list(set(plot_vars) & set(args.var))
    if args.njet:
        run_njet = list(set(run_njet) & set(args.njet))
    if args.btag:
        run_btag = list(set(n_b) & set(args.btag))
    if args.ht:
        args.exclusive_HT = True
        run_ht = list(set(HTbins) & set(args.ht))


    # user feedback
    print "vars:", run_vars
    print "njet:", run_njet
    print "btag:", run_btag
    print "ht:", run_ht
    if args.exclusive_HT:
        print "Doing exclusive HT bins"
    else:
        print "Doing inclusive HT"

    # check that none are empty
    if not run_vars or not run_njet or not run_btag or not run_ht:
        raise RuntimeError("One of var/njet/btag/ht lists is empty - check your spelling!")

    if args.check:
        print "Not making plots, checking they exist..."
        print "Please re-run using the following commands:"
        print "(If there's no commands, you're good to go!)"
    else:
        print "Making lots of data VS bg plots from", ROOTdir

    # actually do something
    run_over(root_dir=ROOTdir, out_dir=out_dir, plot_vars=run_vars, njet=run_njet, btag=run_btag, htbins=run_ht, exclusive_HT=args.exclusive_HT, check=args.check, custom_title=title, qcd=args.qcd)


def run_over(root_dir, out_dir, plot_vars=plot_vars, njet=n_j, btag=n_b, htbins=allHTbins, exclusive_HT=False, check=False, custom_title="#alpha_{T} > 0.55", qcd=False):
    """
    Method to run over all vars/njet/btag/HT bins
    """
    for v, j, b in product(plot_vars, njet, btag):
        if exclusive_HT:
            do_a_plot_HT_excl(root_dir=root_dir, out_dir=out_dir, var=v, njet=j, btag=b, htbins=htbins, check=check, custom_title=title, qcd=qcd)
        else:
            do_a_plot_HT_incl(root_dir=root_dir, out_dir=out_dir, var=v, njet=j, btag=b, check=check, custom_title=title, qcd=qcd)


if __name__ == "__main__":
    main()
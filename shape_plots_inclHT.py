"""
This script makes data VS background plots, but gets the backgrounds from
DATA control region shape, not MC. To do this, we define several control regions
(for each BG source), use MC to calculate transfer factors, then scale the
data control region plot by that factor. Oh yeah and whack in stat + syst
uncertainties, latter from closure tests.

We do this for bins of Njets, Nbtag, HT. And we look at lots of variables.

And we make it look b-e-a-utiful.

Robin Aggleton

"""

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


r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

# Define region bins
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][:]
# n_j = ["le3j", "ge4j", "ge2j"][:2]
n_j = ["eq2j", "eq3j", "eq4j", "ge5j"] # fine jet binning
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]


# input files, output directories, which HTbins to run over
# if fineJetMulti need to use fine_jet branch, else master branch. Need better way.
ROOTdir, out_dir, HTbins = [
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/", "11Dec_aT_0p53_forRobin_v0_new", allHTbins[:]],  #re-run
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0_MuonInJet/", "11Dec_aT_0p53_forRobin_v0_MuonInJet", allHTbins[3:]],  # muon in jet
    ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1", "./01Dec_aT_0p53_globalAlphaT_v1/", allHTbins[3:]],  # alphaT in control regions as well
    ["/Users/robina/Dropbox/AlphaT/Root_Files_04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0", "./04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0/", allHTbins[:]],  # dPhi* <0.3 in SR - old
    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0", "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_gt0p3_v0_new/", allHTbins[:]],  # dPhi* >0.3 in SR, fine jet multiplicity, fixed cross-cleaner
    ["/Users/robina/Dropbox/AlphaT/Root_Files_21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0", "./21Dec_alphaT_0p53_fullHT_fixedCC_fineJetMulti_dPhi_lt0p3_v0_new/", allHTbins[:]]  # dPhi* <0.3 in SR, fine jet multiplicity, fixed cross-cleaner
][-2]

# Variable(s) you want to plot - NOT USED, just a reminder
plot_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "ComMinBiasDPhi_acceptedJets", "EffectiveMass",
             "Number_Good_verticies", "JetMultiplicity"]

# Custom bins for AlphaT per Rob's suggestion
alphaT_bins = np.concatenate((np.arange(0.5, 1.0, 0.05), np.arange(1.0, 5.5, 0.5)))

dphi_bins = np.arange(0.0, 4.1, 0.1) # or 10

rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
            "ComMinBiasDPhi_acceptedJets": dphi_bins, "AlphaT": alphaT_bins,
            "MET_Corrected": 8, "HT": 10, "LeadJetPt": 5, "SecondJetPt": 5,
            "EffectiveMass": 10, "MHT": 4}

log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]


def do_a_plot_HT_incl(var="ComMinBiasDPhi_acceptedJets", njet="eq3j", btag="eq0b"):
    rebin = rebin_d[var] if var in rebin_d else 2
    log = True if var in log_these else False
    plot = Ratio_Plot(ROOTdir, out_dir, var, njet, btag, HTbins, rebin, log)
    plot.make_plots()
    plot.save()


def do_all_plots_HT_incl():
    # inclusive HT
    for v, j, b in product(plot_vars, n_j, n_b):
        do_a_plot_HT_incl(var=v, njet=j, btag=b)


if __name__ == "__main__":
    print "Making lots of data VS bg plots for inclusive HT..."
    if len(sys.argv) == 4:
        do_a_plot_HT_incl(var=sys.argv[1], njet=sys.argv[2], btag=sys.argv[3])
    elif len(sys.argv) == 1:
        do_all_plots_HT_incl()
    else:
        print "Run using:"
        print "python shape_plots_inclHT.py # for all variable, njet, btag bins"
        print "python shape_plots_inclHT.py <variable> <njet> <btag> # for one specific case"
        exit(1)

"""
This script makes data VS background plots, but gets the backgrounds from
DATA control region shape, not MC. To do this, we define several control regions
(for each BG source), use MC to calculate transfer factors, then scale the
data control region plot by that factor. Oh yeah and whack in stat + syst
uncertainties, latter from closure tests.

We do this for bins of Njets, Nbtag, and inclusive HT. And we look at lots of variables.

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
from Prediction_Plot import Prediction_Plot
import sys
import make_component_pres as pres


r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

# Define region bins
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"]
# n_j = ["le3j", "ge4j", "ge2j"][:2]
n_j = ["eq2j", "eq3j", "eq4j", "ge5j"] # fine jet binning
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:3]


# input files, output directories, HTbins
ROOTdir, out_dir, HTbins = [
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/", "11Dec_aT_0p53_forRobin_v0", allHTbins[:]],  #re-run
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0_MuonInJet/", "11Dec_aT_0p53_forRobin_v0_MuonInJet", allHTbins[:]],  # include muon in Jet
    ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1", "./01Dec_aT_0p53_globalAlphaT_v1/", allHTbins[3:]],  # alphaT in control regions as well
    ["/Users/robina/Dropbox/AlphaT/Root_Files_04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0", "./04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0/", allHTbins[:]],  # dPhi* <0.3 in SR
    ["/Users/robina/Dropbox/AlphaT/Root_Files_03Dec_aT_0p53_lowBins_dPhi_gt0p3_v0", "./03Dec_aT_0p53_lowBins_dPhi_gt0p3_v0/", allHTbins[:]]  # dPhi* >0.3 in SR
][2]

# Variable(s) you want to plot - NOT USED, just a reminder
plot_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "ComMinBiasDPhi_acceptedJets", "EffectiveMass",
             "Number_Good_verticies", "JetMultiplicity"]

# Custom bins for AlphaT per Rob's suggestion
alphaT_bins = np.concatenate((np.arange(0.5, 1.0, 0.05), np.arange(1.0, 5.0, 0.5)))

dphi_bins = np.arange(0.0, 4.1, 0.1) # or 10

rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
            "ComMinBiasDPhi_acceptedJets": dphi_bins, "AlphaT": alphaT_bins,
            "MET_Corrected": 8, "HT": 10, "LeadJetPt": 5, "SecondJetPt": 5,
            "EffectiveMass": 10, "MHT": 4}

log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]


def do_a_plot_HT_excl(var="AlphaT", njet="le3j", btag="eq0b"):
    # exclusive HT bins - do one by one
    for ht in HTbins:
        rebin = rebin_d[var] if var in rebin_d else 2
        log = True if var in log_these else False
        plot = Prediction_Plot(ROOTdir, out_dir, var, njet, btag, [ht], rebin, log)
        plot.plot_components = True
        plot.make_plots()
        plot.save()
    # optionally can do component plots as well for this var
    # lo = HTbins[0].split("_")[0]
    # hi = HTbins[-1].split("_")[1] if "_" in HTbins[-1] else "Inf"
    # print "Make component pres"
    # pres.make_pres(plot_dir=out_dir, var=var, njet=njet, btag=btag, lo_ht=lo, hi_ht=hi)


def do_all_plots_HT_excl():
    for v, j, b in product(plot_vars, n_j, n_b):
        do_a_plot_HT_excl(var=v, njet=j, btag=b)


if __name__ == "__main__":
    print "Making lots of data VS bg plots for exclusive HT bins..."
    if len(sys.argv) == 4:
        do_a_plot_HT_excl(var=sys.argv[1], njet=sys.argv[2], btag=sys.argv[3])
    elif len(sys.argv) == 1:
        do_all_plots_HT_excl()
    else:
        print "Run using:"
        print "python shape_plots_exclHT.py # for all variables/njet/btag bins"
        print "python shape_plots_exclHT.py <variable> <njet> <btag>  # for one specific case"
        exit(1)

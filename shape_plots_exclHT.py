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

r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

# Define region bins
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"]
# n_j = ["le3j", "ge4j", "ge2j"][:2]
# n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]


# input files, output directories, HTbins
ROOTdir, out_dir, HTbins = [
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/", "11Dec_aT_0p53_forRobin_v0", allHTbins[:2]],  #re-run
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0_MuonInJet/", "11Dec_aT_0p53_forRobin_v0_MuonInJet", allHTbins[:]],  # include muon in Jet
    ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1", "./01Dec_aT_0p53_globalAlphaT_v1/", allHTbins[3:]],  # alphaT in control regions as well
    ["/Users/robina/Dropbox/AlphaT/Root_Files_04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0", "./04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0/", allHTbins[:]]  # dPhi* <0.3 in SR
][0]

# Variable(s) you want to plot - NOT USED
plot_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "ComMinBiasDPhi_acceptedJets", "EffectiveMass",
             "Number_Good_verticies", "JetMultiplicity"]

out_stem = "plot"

# Custom bins for AlphaT per Rob's suggestion
b1 = np.arange(0.5, 1.0, 0.05)
b2 = np.arange(1.0, 4.5, 0.5)
alphaT_bins = np.concatenate((b1, b2))

# exclusive HT bins
rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
            "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
            "MET_Corrected": 8, "HT": 1, "SecondJetPt": 1, "EffectiveMass": 5,
            "MHT": 4}
log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets"] #, "HT"]:


def do_all_plots_HT_excl(var="AlphaT", njet="le3j", btag="eq0b"):


    for ht in HTbins:
        rebin =rebin = rebin_d[var] if var in rebin_d else 2
        log = True if var in log_these else False
        plot = Ratio_Plot(ROOTdir, out_dir, var, njet, btag, [ht], rebin, log)
        plot.plot_components = True
        plot.make_plots()
        plot.save()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Run using:"
        print "python shape_plots_exclHT.py <variable> <njet> <btag>"
        exit(1)
    print "Making lots of data VS bg plots for exclusive HT bins..."
    do_all_plots_HT_excl(sys.argv[1], sys.argv[2], sys.argv[3])

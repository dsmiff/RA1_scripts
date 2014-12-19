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

r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
# r.TH1.AddDirectory(r.kFALSE)

# input files & output directories
ROOTdir, out_dir = [
    ["/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/", "11Dec_aT_0p53_forRobin_v0"],  #re-run
    ["/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1", "./01Dec_aT_0p53_globalAlphaT_v1/"],  # alphaT in control regions as well
    ["/Users/robina/Dropbox/AlphaT/Root_Files_04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0", "./04Dec_aT_0p53_fullHT_dPhi_lt0p3_v0/"]  # dPhi* <0.3 in SR
][0]

# Variable(s) you want to plot
plot_vars = ["Number_Btags", "AlphaT", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "ComMinBiasDPhi_acceptedJets", "EffectiveMass",
             "Number_Good_verticies", "JetMultiplicity"]

out_stem = "plot"

# Define region bins
HTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"]
ht_scheme = ["incl", "excl"][0]  # option for individual bin, or inclusive - not used ATM
n_j = ["le3j", "ge4j", "ge2j"][:2]
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]

sel=["OneMuon", "DiMuon", "Had"]
# # MC processes that go into transfer factors
# processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

# processes_mc_signal_le1b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
#                             "DiMuon": ['Zinv']}

# processes_mc_signal_ge2b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop', 'Zinv'],
#                             "DiMuon": []}  # for >= 2btags dimu region not used

# # Control regions to get data shapes (+ proper titles for legend etc)
# ctrl_regions = {"OneMuon": "Single #mu BG", "DiMuon": "#mu#mu BG"}

# # Sytematics on TF (as a %). Fn on njets & HT
# tf_systs = {
#     "le3j": {"200_275": 4, "275_325": 6, "325_375": 6, "375_475": 8, "475_575": 8, "575_675": 12, "675_775": 12, "775_875": 17, "875_975": 17, "975_1075": 19, "1075": 19},
#     "ge4j": {"200_275": 6, "275_325": 6, "325_375": 11, "375_475": 11, "475_575": 11, "575_675": 18, "675_775": 18, "775_875": 20, "875_975": 20, "975_1075": 26, "1075": 26}
# }


def make_plot_bins(var):#, njet, nbtag, ht):
    """
    For a given variable, makes data VS background plots for all the
    relevant HT, Njets, Nbtag bins
    """
    # Custom bins for AlphaT per Rob's suggestion
    b1 = np.arange(0.5, 1.0, 0.05)
    b2 = np.arange(1.0, 4.5, 0.5)
    alphaT_bins = np.concatenate((b1, b2))
    # alphaT_bins = 20 # an alternate sensible equal bin value


    # ONLY DO ONE OF THE FOLLOWING - IF YOU TRY AND DO ALL IT'LL SEGFAULT
    # for v, njet, btag, ht in product(var, n_j, n_b, HTbins):
    for v in var:
        print "Doing plots for", v
        rebin = 2
        rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                    "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
                    "MET_Corrected": 8, "HT": 1, "SecondJetPt": 1, "EffectiveMass": 5,
                    "MHT": 4}
        if v in rebin_d:
            rebin = rebin_d[v]
        log = False
        if v in ["AlphaT", "ComMinBiasDPhi_acceptedJets"]: #, "HT"]:
            log = True
        plot = Ratio_Plot(ROOTdir, "plot", v, "le3j", "eq0b", ["325_375"], rebin, log)
        # print plot.hist_data_signal
        print "YO"
        plot.make_plots()
        outd = "%s/%s_%s_%s" %(out_dir, "le3j", "eq0b", "325_375")
        plot.save(odir=outd)
        # dave = grabr.grab_plots("/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Muon_Data.root",sele="OneMuon", h_title=v, njet=njet, btag=btag, ht_bins=ht)
        # print dave.GetName()
        # plot = Ratio_Plot(ROOTdir, "plot", v, "le3j", "eq1b", ["675_775"], rebin, log)
        # plot.make_plots()
        # outd = "%s/%s_%s_%s" %(out_dir, "le3j", "eq1b", "675_775")
        # plot.save(odir=outd)


    # For ge4j cos the binning is diff in cases...
    for v in var:
        print "Doing plots for", v
        rebin = 2
        rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                    "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
                    "MET_Corrected": 8, "HT": 1, "SecondJetPt": 1, "EffectiveMass": 5,
                    "MHT": 8}
        if v in rebin_d:
            rebin = rebin_d[v]
        log = False
        if v in ["AlphaT", "ComMinBiasDPhi_acceptedJets"]: #, "HT"]:
            log = True
        # plot = Ratio_Plot(v, "ge4j", "eq0b", ["675_775"], rebin, log)
        # outd = "%s/%s_%s_%s" %(out_dir, "ge4j", "eq0b", "675_775")
        # plot.save(odir=outd)

        # plot = Ratio_Plot(v, "ge4j", "eq1b", ["675_775"], rebin, log)
        # outd = "%s/%s_%s_%s" %(out_dir, "ge4j", "eq1b", "675_775")
        # plot.save(odir=outd)


    # For inclusive HT
    counter = 0
    for v in var[:]:
        print "Doing plots for", v
        rebin = 2
        rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                    "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
                    "MET_Corrected": 8, "HT": 5, "SecondJetPt": 4, "EffectiveMass": 10,
                    "MHT": 8, "LeadJetPt": 4}
        if v in rebin_d:
            rebin = rebin_d[v]

        log = False
        if v in ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]:
            log = True

        njet = "ge4j"
        btag = "eq0b"
        counter += 1
        # plot = Ratio_Plot(ROOTdir, "plot", v, njet, btag, HTbins, rebin, log)
        # plot.make_plots()
        # outd = "%s/%s_%s_%s" %(out_dir, njet, btag, "200_Inf")
        # plot.save(odir=outd)
        # del plot
        # print counter

        # njet = "ge4j"
        # btag = "eq1b"
        # counter += 1
        # plot = Ratio_Plot(ROOTdir, "plot", v, njet, btag, HTbins, rebin, log)
        # plot.make_plots()
        # outd = "%s/%s_%s_%s" %(out_dir, njet, btag, "200_Inf")
        # plot.save(odir=outd)
        # del plot
        # print counter
    # Testing
    # plot = Ratio_Plot("AlphaT", "le3j", "eq0b", "375_475", 20, True)
    # plot.save()
    # plot = Ratio_Plot("JetMultiplicity", "le3j", "eq0b", "375_475", 1, False)
    # plot.save()
    # plot = Ratio_Plot("LeadJetPt", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("SecondJetPt", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("HT", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("SecondJetEta", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("LeadJetEta", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("MHT", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("MET_Corrected", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("MHTovMET", "ge4j", "eq0b", "375_475", 2, True)
    # plot.save()
    # plot = Ratio_Plot("ComMinBiasDPhi_acceptedJets", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("EffectiveMass", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("Number_Btags", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()
    # plot = Ratio_Plot("Number_Good_verticies", "le3j", "eq0b", "375_475", 2, False)
    # plot.save()


def do_all_plots_HT_excl():
    """
    The big enchilada
    """
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

    for ht in HTbins:
        v = plot_vars[6]
    # for njet, btag, ht in product(n_j, n_b, HTbins):
        if v in rebin_d:
            rebin = rebin_d[v]
        else:
            rebin = 2
        if v in log_these:
            log = True
        else:
            log = False

        # print  v, njet, btag, [ht]
        njet = "le3j"
        btag = "eq0b"
        plot = Ratio_Plot(ROOTdir, out_stem, v, njet, btag, [ht], rebin, log)
        plot.make_plots()
        outd = "%s/%s_%s_%s" %(out_dir, njet, btag, ht)
        plot.save(odir=outd)

        # plot = Ratio_Plot("Number_Btags", njet, btag, [ht], 1, False)
        # plot.save(odir=outd)
        # plot = Ratio_Plot("AlphaT", njet, btag, [ht], alphaT_bins, True)
        # plot.save(odir=outd)
        # # plot = Ratio_Plot("LeadJetPt", njet, btag, [ht], 2, False)
        # # plot.save(odir=outd)
        # plot = Ratio_Plot("LeadJetEta", njet, btag, [ht], 2, False)
        # plot.save(odir=outd)

        # plot = Ratio_Plot("SecondJetPt", njet, btag, [ht], 1, False)
        # plot.save(odir=outd)
        # # plot = Ratio_Plot("SecondJetEta", njet, btag, [ht], 2, False)
        # # plot.save(odir=outd)
        # plot = Ratio_Plot("HT", njet, btag, [ht], 1, False)
        # plot.save(odir=outd)
        # plot = Ratio_Plot("MHT", njet, btag, [ht], 4, False)
        # plot.save(odir=outd)
        # # plot = Ratio_Plot("MET_Corrected", njet, btag, [ht], 8, False)
        # # plot.save(odir=outd)

        # # plot = Ratio_Plot("ComMinBiasDPhi_acceptedJets", njet, btag, [ht], 10, True)
        # # plot.save(odir=outd)
        # plot = Ratio_Plot("MHTovMET", njet, btag, [ht], 1, False)
        # plot.save(odir=outd)
        # plot = Ratio_Plot("EffectiveMass", njet, btag, [ht], 5, False)
        # plot.save(odir=outd)

        # # plot = Ratio_Plot("Number_Good_verticies", njet, btag, [ht], 1, False)
        # # plot.save(odir=outd)
        # plot = Ratio_Plot("JetMultiplicity", njet, btag, [ht], 1, False)
        # plot.save(odir=outd)


def do_all_plots_HT_incl(njet="le3j", btag="eq0b"):

    # Custom bins for AlphaT per Rob's suggestion
    b1 = np.arange(0.5, 1.0, 0.05)
    b2 = np.arange(1.0, 4.5, 0.5)
    alphaT_bins = np.concatenate((b1, b2))

    # inclusive HT
    rebin = 2
    rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
                "MET_Corrected": 8, "HT": 5, "SecondJetPt": 4, "EffectiveMass": 10,
                "MHT": 8, "LeadJetPt": 4}

    log = False
    log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]
    for v in plot_vars:
        if v in rebin_d:
            rebin = rebin_d[v]
        else:
            rebin = 2
        if v in log_these:
            log = True
        else:
            log = False
        print v, njet, btag, HTbins
        plot = Ratio_Plot(v, njet, btag, HTbins, rebin, log)
        outd = "%s/%s_%s_%s" %(out_dir, njet, btag, "200_Inf")
        plot.save(odir=outd)


if __name__ == "__main__":
    print "Making lots of data VS bg plots..."
    make_plot_bins(plot_vars)
    # do_all_plots_HT_excl()
    # do_all_plots_HT_incl()

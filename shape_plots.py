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
import ROOT
from itertools import product

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetOptFit(1111)

# Define region bins
HTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][3:]
ht_scheme = ["incl", "excl"][0]  # option for individual bin, or inclusive
n_j = ["le3j", "ge4j", "ge2j"][:2]
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]

# Variable(s) you want to plot
# "MHT", "AlphaT", "Meff", "dPhi*", "jet variables", "MET (corrected)", "MHT/MET (corrected)", "Number_Good_vertices",
# plot_vars = ["LeadJetPt"]
plot_vars = ["Number_Btags"]

# Where you want to store plots
out_dir = ""
out_title = ""


def style_hist(hist, region):
    """
    Do some aesthetic stylings on hists.
    """
    if region == "OneMuon":
        hist.SetLineColor(ROOT.kViolet+2)
        hist.SetFillColor(ROOT.kViolet+2)
        hist.SetMarkerColor(ROOT.kViolet+2)
    elif region == "DiMuon":
        hist.SetLineColor(ROOT.kOrange)
        hist.SetFillColor(ROOT.kOrange)
        hist.SetMarkerColor(ROOT.kOrange)


def title_axes(hist, xtitle, ytitle="Events"):
    """
    Apply title to axes
    """
    hist.SetXTitle(xtitle)
    hist.SetYTitle(ytitle)
    hist.SetTitleOffset(hist.GetTitleOffset("Y")*1.2, "Y")


def make_plot(var, njet, btag, htbins):
    """
    For a given variable, for given HT, NJet, Nbtag bin,
    makes data VS background plot.
    Basically for each of single mu and di mu regions, it gets data in
    control regions, MC in signal & control regions (for all SM processes),
    and data in signal region. Then calculate transfer factor
    (MC_signal / MC_control), and scale data_control by that factor.
    Then stack single mu and di mu together.
    """

    # MC processes
    processes = ['DY', 'Data', 'DiBoson', 'TTbar', 'WJets', 'Zinv']

    # factor out common part - amount of MC in signal selection
    hist_mc_signal = None
    for p in processes:
        MC_signal_tmp = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/Had_%s.root" % p,
                                         sele="Had", h_title=var, njet=njet, btag=btag, ht_bins=htbins)
        if not hist_mc_signal:
            hist_mc_signal = MC_signal_tmp.Clone("MC_signal")
        else:
            hist_mc_signal.Add(MC_signal_tmp)

    # to hold single mu + dimu result
    shape_predict = ROOT.THStack("shape_predict","Awesome shape prediction")

    # control regions
    ctrl_regions = ["OneMuon", "DiMuon"]

    # Now do the single mu and di mu regions
    for ctrl in ctrl_regions:
        hist_data_control = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/Muon_Data.root",
                                             sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
        hist_mc_control = None
        for p in processes:
            MC_ctrl_tmp = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/Muon_%s.root" %p,
                                               sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
            if not hist_mc_control:
                hist_mc_control = MC_ctrl_tmp.Clone()
            else:
                hist_mc_control.Add(MC_ctrl_tmp)

        # Divide, multiply, and add to total shape
        hist_data_control.Divide(hist_mc_control)
        hist_data_control.Multiply(hist_mc_signal)
        style_hist(hist_data_control, ctrl) # Some shimmer
        shape_predict.Add(hist_data_control)

    c = ROOT.TCanvas()
    shape_predict.Draw()
    title_axes(shape_predict.GetHistogram(), var, "Events")
    c.SaveAs("test.pdf")


def make_plot_bins(var):
    """
    For a given variable, makes data VS background plots for all the relevant HT, Njets, Nbtag bins
    """
    # for njet, btag, ht_bins in product(n_j, n_b, ht):
        # make_plot(var, njet, btag, ht_bins)
    make_plot(var, "le3j", "ge0b", ["475_575"])


if __name__ == "__main__":
    print "Making lots of data VS bg plots..."

    for var in plot_vars:
        print "Doing plots for", var
        make_plot_bins(var)

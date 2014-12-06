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
from itertools import product

r.TH1.SetDefaultSumw2(True)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)

ROOTdir = "/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/"

# Define region bins
HTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][3:]
ht_scheme = ["incl", "excl"][0]  # option for individual bin, or inclusive
n_j = ["le3j", "ge4j", "ge2j"][:2]
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]

# MC processes that go into transfer factors
processes = ['DY', 'Data', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

# Control regions to get data shapes (+ proper titles for legend etc)
ctrl_regions = {"OneMuon":"Single #mu BG", "DiMuon":"#mu#mu BG"}

# Variable(s) you want to plot
# "MHT", "AlphaT", "Meff", "dPhi*", "jet variables", "MET (corrected)", "MHT/MET (corrected)", "Number_Good_vertices",
plot_vars = ["LeadJetPt"]
# plot_vars = ["Number_Btags"]

# Where you want to store plots
out_dir = "."
out_stem = "test"

def color_hist(hist, color):
    """
    Set marker/line/fill color for histogram
    """
    hist.SetLineColor(color)
    hist.SetFillColor(color)
    hist.SetMarkerColor(color)


def style_hist(hist, region):
    """
    Do some aesthetic stylings on hists.
    """
    hist.Rebin(4)
    if region == "OneMuon":
        color_hist(hist, r.kViolet+1)
    elif region == "DiMuon":
        color_hist(hist, r.kOrange)
    elif region == "Data":
        hist.SetMarkerColor(r.kBlack)
        # hist.SetMarkerSize(2)
        hist.SetMarkerStyle(20)
        hist.SetLineColor(r.kBlack)


def style_hist_err1(hist, region):
    """
    Do some aesthetic stylings on error bars.
    """
    # hist.Rebin(4)
    hist.SetMarkerStyle(0);
    hist.SetMarkerSize(0);
    hist.SetLineColor(r.kGray+3);
    hist.SetLineWidth(0);
    hist.SetFillColor(r.kGray+3);
    hist.SetFillStyle(3002)


def style_hist_err2(hist, region):
    """
    Do some alternate stylings on error bars.
    """
    # hist.Rebin(4)
    hist.SetMarkerStyle(0);
    hist.SetMarkerSize(0);
    hist.SetLineColor(r.kGray+3);
    hist.SetLineWidth(0);
    hist.SetFillColor(r.kGray+3);
    hist.SetFillStyle(3013)


def title_axes(hist, xtitle, ytitle="Events"):
    """
    Apply title to axes, do offsets, sizes
    """
    hist.SetXTitle(xtitle)
    hist.SetYTitle(ytitle)
    hist.SetTitleOffset(hist.GetTitleOffset("Y")*1.2, "Y")


def make_standard_text():
    """
    Generate standard boring text
    """
    t = r.TPaveText(0.6, 0.7, 0.85, 0.85, "NDC")
    t.AddText("CMS 2012, #sqrt{s} = 8 TeV")
    t.AddText("")
    t.AddText("#int L dt = 18.493 fb^{-1}")
    t.SetFillColor(0)
    t.SetFillStyle(0)
    t.SetLineColor(0)
    t.SetLineStyle(0)
    return t


def make_hists(var, njet, btag, htbins):
    """
    Makes component histograms for any plot: data in signal region, and a list of
    histograms that are BG estimates from doing data_control * transfer factor.
    Each hist in the list corresponds to one control region.
    Basically for each of the control regions, it gets data in
    control region, MC in signal & control regions (for all SM processes),
    and data in signal region. Then calculate transfer factor
    (MC_signal / MC_control), and scale data_control by that factor.

    Returns list comprising of data hist followed by component histograms
    in their own list (one for each control region)
    """

    # factor out common part - amount of MC in signal selection
    hist_mc_signal = None
    for p in processes:
        MC_signal_tmp = grabr.grab_plots(f_path="%s/Had_%s.root" % (ROOTdir, p),
                                         sele="Had", h_title=var, njet=njet, btag=btag, ht_bins=htbins)
        if not hist_mc_signal:
            hist_mc_signal = MC_signal_tmp.Clone("MC_signal")
        else:
            hist_mc_signal.Add(MC_signal_tmp)

    # Now do the control regions
    component_hists = []
    for ctrl in ctrl_regions:
        hist_data_control = grabr.grab_plots(f_path="%s/Muon_Data.root" % ROOTdir,
                                             sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
        hist_data_control.SetName(ctrl) # for styling later

        hist_mc_control = None
        for p in processes:
            MC_ctrl_tmp = grabr.grab_plots(f_path="%s/Muon_%s.root" % (ROOTdir, p),
                                           sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
            if not hist_mc_control:
                hist_mc_control = MC_ctrl_tmp.Clone()
            else:
                hist_mc_control.Add(MC_ctrl_tmp)

        # Divide, multiply, and add to total shape
        err = 0.
        integral = hist_mc_signal.IntegralAndError(1, hist_mc_signal.GetNbinsX(),r.Double(err))
        print integral, err
        hist_data_control.Scale(hist_mc_signal.Integral()/hist_mc_control.Integral())
        component_hists.append(hist_data_control)

    # Get data hist
    hist_data_signal = grabr.grab_plots(f_path="%s/Had_Data.root" % ROOTdir,
                                        sele="Had", h_title=var, njet=njet, btag=btag, ht_bins=htbins)
    style_hist(hist_data_signal,"Data")
    return hist_data_signal, component_hists


def make_plot(var, njet, btag, htbins):
    """
    For a given variable, for given HT, NJet, Nbtag bin,
    makes data VS background plot.
    """

    hist_data_signal, component_hists = make_hists(var, njet, btag, htbins)

    # Want to add hists to THStack by ascending Integral()
    component_hists.sort(key=lambda hist: hist.Integral())

    # Little note about putting error bands on each contribution:
    # There is a ROOT bug whereby if you try and make copies of the hists,
    # put into a THStack, and tell it to plot with E2 and set a fill style
    # like 3013, only the last hist will actually render properly,
    # others will be blocky. So to avoid this we build up TH1s and then
    # draw those ontop of the main block colours. (5.34.21 MacOSX w/Cocoa)
    shape = r.THStack("shape","Like a boss")
    error_hists = None

    leg = r.TLegend(0.65, 0.4, 0.8, 0.65)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetLineColor(0)
    leg.SetLineStyle(0)
    leg.AddEntry(hist_data_signal, "Data", "p")

    # Loop through all shape components: add to THStack, make error bars,
    # make legend
    for h in component_hists:
        style_hist(h, h.GetName()) # Some shimmer
        shape.Add(h)

        # copies for stat/syst error bars
        if not error_hists:
            h_stat = h.Clone()
            style_hist_err1(h_stat, h.GetName())
            error_hists = [h_stat]
        else:
            h_stat = error_hists[-1].Clone()
            h_stat.Add(h)
            style_hist_err1(h_stat, h.GetName())
            error_hists.append(h_stat)

    # reverse sort to add entries to the legend
    for h in sorted(component_hists, key=lambda hist: 1./hist.Integral()):
        leg.AddEntry(h, ctrl_regions[h.GetName()], "f")
    leg.AddEntry(error_hists[-1], "Stat. error", "F")

    # Finally draw all the pieces
    c = r.TCanvas()
    c.SetTicks()
    shape.Draw("HIST")
    [h.Draw("E2 SAME") for h in error_hists]
    title_axes(shape.GetHistogram(), var, "Events")
    hist_data_signal.Draw("ESAME")
    leg.Draw("SAME")
    txt = make_standard_text()
    txt.Draw("SAME")
    c.SaveAs("%s/%s.pdf" % (out_dir, out_stem))


def make_plot_bins(var):
    """
    For a given variable, makes data VS background plots for all the
    relevant HT, Njets, Nbtag bins
    """
    for v in var:
        print "Doing plots for", var
        # for njet, btag, ht_bins in product(n_j, n_b, ht):
            # make_plot(v, njet, btag, ht_bins)
        make_plot(v, "le3j", "ge0b", ["475_575"])


if __name__ == "__main__":
    print "Making lots of data VS bg plots..."
    make_plot_bins(plot_vars)

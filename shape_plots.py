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


# Variable(s) you want to plot
# "MHT", "AlphaT", "Meff", "dPhi*", "jet variables", "MET (corrected)", "MHT/MET (corrected)", "Number_Good_vertices",
plot_vars = ["LeadJetPt"]
# plot_vars = ["Number_Btags"]

# Where you want to store plots
out_dir = ""
out_title = ""


def style_hist(hist, region):
    """
    Do some aesthetic stylings on hists.
    """
    hist.Rebin(4)
    if region == "OneMuon":
        hist.SetLineColor(r.kViolet+2)
        hist.SetFillColor(r.kViolet+2)
        hist.SetMarkerColor(r.kViolet+2)
    elif region == "DiMuon":
        hist.SetLineColor(r.kOrange)
        hist.SetFillColor(r.kOrange)
        hist.SetMarkerColor(r.kOrange)
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
    if region == "OneMuon":
        hist.SetMarkerStyle(0);
        hist.SetMarkerSize(0);
        hist.SetLineColor(r.kGray+3);
        hist.SetLineWidth(0);
        hist.SetFillColor(r.kGray+3);
        hist.SetFillStyle(3002);
    elif region == "DiMuon":
        hist.SetMarkerStyle(0);
        hist.SetMarkerSize(0);
        hist.SetLineColor(r.kGray+3);
        hist.SetLineWidth(0);
        hist.SetFillColor(r.kGray+3);
        hist.SetFillStyle(3003);
    elif region == "Data":
        pass
        # hist.SetMarkerColor(r.kBlack)
        # hist.SetMarkerSize(2)
        # hist.SetMarkerStyle(20)
        # hist.SetLineColor(r.kBlack)


def style_hist_err2(hist, region):
    """
    Do some alternate stylings on error bars.
    """
    # hist.Rebin(4)
    if region == "OneMuon":
        hist.SetLineColor(r.kViolet+2)
        hist.SetFillColor(r.kViolet+2)
        hist.SetMarkerColor(r.kViolet+2)
        hist.SetFillStyle(3013)
    elif region == "DiMuon":
        hist.SetLineColor(r.kOrange)
        hist.SetFillColor(r.kOrange)
        hist.SetMarkerColor(r.kOrange)
        hist.SetFillStyle(3013)
    elif region == "Data":
        pass
        # hist.SetMarkerColor(r.kBlack)
        # hist.SetMarkerSize(2)
        # hist.SetMarkerStyle(20)
        # hist.SetLineColor(r.kBlack)


def title_axes(hist, xtitle, ytitle="Events"):
    """
    Apply title to axes
    """
    hist.SetXTitle(xtitle)
    hist.SetYTitle(ytitle)
    hist.SetTitleOffset(hist.GetTitleOffset("Y")*1.2, "Y")


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


    # Now do the single mu and di mu regions
    component_hists = []
    ctrl_regions = ["OneMuon", "DiMuon"]
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

    # Add hists to THStack by ascending Integral
    shape = r.THStack("shape","Awesome shape prediction")
    shape_stat = r.THStack("shape_stat","Awesome shape prediction with stat errors")
    shape_stat_syst = r.THStack("shape_stat_syst","Awesome shape prediction with stat & syst errors")

    component_hists.sort(key=lambda hist: hist.Integral())
    # Little note about putting error bands on each contribution:
    # There is a ROOT bug whereby if you try and make copies of the hists,
    # put into a THStack, and tell it to plot with E2 and set a fill style
    # like 3013, only the last hist will actually render properly,
    # others will be blocky. So to avoid this we build up TH1s and then
    # draw those ontop of the main block colours. (5.34.21 MacOSX w/Cocoa)
    error_hists = None
    for h in component_hists:
        style_hist(h, h.GetName()) # Some shimmer
        shape.Add(h)

        # copies for stat error bars
        # and copies for stat+syste error bars (at some point)
        if not error_hists:
            h_stat = h.Clone()
            style_hist_err1(h_stat, h.GetName())
            error_hists = [h_stat]
        else:
            h_stat = error_hists[-1].Clone()
            h_stat.Add(h)
            style_hist_err1(h_stat, h.GetName())
            error_hists.append(h_stat)

    c = r.TCanvas()
    c.SetTicks()
    shape.Draw("HIST")
    [h.Draw("E2 SAME") for h in error_hists]
    title_axes(shape.GetHistogram(), var, "Events")
    hist_data_signal.Draw("ESAME")
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

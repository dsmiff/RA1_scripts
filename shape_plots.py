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
# processes = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_signal_le1b = { "OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
                             "DiMuon": ['Zinv']}

processes_mc_signal_ge2b = { "OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop', 'Zinv'],
                             "DiMuon": []} # for >= 2btags dimu region not used

# Control regions to get data shapes (+ proper titles for legend etc)
ctrl_regions = {"OneMuon":"Single #mu BG", "DiMuon":"#mu#mu BG"}

# Variable(s) you want to plot
# "MHT", "AlphaT", "Meff", "dPhi*", "jet variables", "MET (corrected)", "MHT/MET (corrected)", "Number_Good_vertices",
plot_vars = ["AlphaT", "JetMultiplicity", "LeadJetPt", "LeadJetEta", "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected", "MHTovMET", "ComMinBiasDPhi", "EffectiveMass"]#, "Number_Btags"]
# plot_vars = ["LeadJetPt", "SecondJetEta"]
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


def style_hist(hist, region, rebin):
    """
    Do some aesthetic stylings on hists.
    """
    hist.Rebin(rebin)
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

def make_legend():
    """
    Generate blank legend
    """
    leg = r.TLegend(0.65, 0.4, 0.85, 0.65)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetLineColor(0)
    leg.SetLineStyle(0)
    leg.SetLineWidth(0)
    return leg


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
    t.SetLineWidth(0)
    return t

def make_bin_text(njet, btag, ht_bins):
    """
    Generate label of which bin
    """
    t = r.TPaveText(0.1, 0.91, 0.5, 0.95, "NDC")
    b_str = grabr.btag_string(btag) if grabr.btag_string(btag) else "geq 0 btag"

    tt = t.AddText("%s, %s, HT bin %s" % (njet, b_str, ', '.join(ht_bins)))
    tt.SetTextAlign(12)
    t.SetFillColor(0)
    t.SetFillStyle(0)
    t.SetLineColor(0)
    t.SetLineStyle(0)
    t.SetLineWidth(0)
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

    component_hists = []
    for ctrl in ctrl_regions:
        print "**** DOING", ctrl

        if "Muon" in ctrl:
            f_start = "Muon"
        elif "Photon" in ctrl:
            f_start = "Photon"
        # else:
            # f_start = "Had"

        # Data in control region:
        hist_data_control = grabr.grab_plots(f_path="%s/%s_Data.root" % (ROOTdir, f_start),
                                             sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
        hist_data_control.SetName(ctrl) # for styling later

        # MC in signal region
        if "0" in btag or "1" in btag:
            processes = processes_mc_signal_le1b
        else:
            processes = processes_mc_signal_ge2b

        print "MC in signal region:"
        hist_mc_signal = None
        for p in processes[ctrl]:
            MC_signal_tmp = grabr.grab_plots(f_path="%s/Had_%s.root" % (ROOTdir, p),
                                             sele="Had", h_title=var, njet=njet, btag=btag, ht_bins=htbins)
            if not hist_mc_signal:
                hist_mc_signal = MC_signal_tmp.Clone("MC_signal")
            else:
                hist_mc_signal.Add(MC_signal_tmp)

            print p, hist_mc_signal.Integral()

        # MC in control region
        print "MC in control region:"
        hist_mc_control = None
        for p in processes_mc_ctrl:
            MC_ctrl_tmp = grabr.grab_plots(f_path="%s/%s_%s.root" % (ROOTdir, f_start, p),
                                           sele=ctrl, h_title=var, njet=njet, btag=btag, ht_bins=htbins)
            if not hist_mc_control:
                hist_mc_control = MC_ctrl_tmp.Clone()
            else:
                hist_mc_control.Add(MC_ctrl_tmp)

            print p, hist_mc_control.Integral()

        mc_signal_err = r.Double(-1.)
        mc_signal_integral = hist_mc_signal.IntegralAndError(1, hist_mc_signal.GetNbinsX(), mc_signal_err)
        mc_control_err = r.Double(-1.)
        mc_control_integral = hist_mc_control.IntegralAndError(1, hist_mc_control.GetNbinsX(), mc_control_err)
        data_control_err = r.Double(-1.)
        data_control_integral = hist_data_control.IntegralAndError(1, hist_data_control.GetNbinsX(), data_control_err)

        print ctrl
        print "Data control: integral: %.3f +/- %.3f" % (data_control_integral, data_control_err)
        print "MC signal: integral: %.3f +/- %.3f"  % (mc_signal_integral, mc_signal_err)
        print "MC control: integral: %.3f +/- %.3f" % (mc_control_integral, mc_control_err)

        # Divide, multiply, and add to total shape
        # ROOT's Multiply()/Divide() are bin-by-bin. To propagate the errors,
        # we need copies of the hists we want to multiply/divide, with ALL bins
        # set to Integral +/- (Error on Integral)
        hist_mc_signal_factor = hist_mc_signal.Clone()
        hist_mc_control_factor = hist_mc_control.Clone()

        for i in range(1,1+hist_mc_signal_factor.GetNbinsX()):
            hist_mc_signal_factor.SetBinContent(i, mc_signal_integral)
            hist_mc_signal_factor.SetBinError(i, mc_signal_err)
            hist_mc_control_factor.SetBinContent(i, mc_control_integral)
            hist_mc_control_factor.SetBinError(i, mc_control_err)

        hist_mc_signal_factor.Divide(hist_mc_control_factor)
        hist_data_control.Multiply(hist_mc_signal_factor)
        print "Transfer Factor for %s: %.3f +/- %.3f" % (ctrl, hist_mc_signal_factor.GetBinContent(1), hist_mc_signal_factor.GetBinError(1))
        component_hists.append(hist_data_control)
        print "Estimate:", hist_data_control.Integral()

    # Get data hist
    hist_data_signal = grabr.grab_plots(f_path="%s/Had_Data.root" % ROOTdir,
                                        sele="Had", h_title=var, njet=njet, btag=btag, ht_bins=htbins)
    print "Data SR:", hist_data_signal.Integral()
    return hist_data_signal, component_hists


def make_plot(var, njet, btag, htbins, rebin=4):
    """
    For a given variable, NJet, Nbtag, HT bins,
    makes data VS background plot, where BG is from data control regions.
    """
    # Get our data & BG shapes
    hist_data_signal, component_hists = make_hists(var, njet, btag, htbins)

    style_hist(hist_data_signal, "Data", rebin)

    # Little note about putting error bands on each contribution:
    # There is a ROOT bug whereby if you try and make copies of the hists,
    # put into a THStack, and tell it to plot with E2 and set a fill style
    # like 3013, only the last hist will actually render properly,
    # others will be blocky. So to avoid this we build up cumulative TH1s and
    # then draw those ontop of the main block colours. (5.34.21 MacOSX w/Cocoa)
    shape = r.THStack("shape","")
    error_hists = None

    leg = make_legend()
    leg.AddEntry(hist_data_signal, "Data + stat. error", "pl")

    # Want to add hists to THStack by ascending Integral()
    component_hists.sort(key=lambda hist: hist.Integral())
    # Loop through shape components: mod style, add to THStack, make error bars
    for h in component_hists:
        style_hist(h, h.GetName(), rebin) # Some shimmer BEFORE adding to stack
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
    leg.AddEntry(error_hists[-1], "BG Stat. error", "F")

    # Finally draw all the pieces
    c = r.TCanvas()
    c.SetTicks()
    if hist_data_signal.GetMaximum() > error_hists[-1].GetMaximum():
        hist_data_signal.Draw()
        shape.Draw("HIST SAME")
    else:
        shape.Draw("HIST")
    [h.Draw("E2 SAME") for h in error_hists]
    title_axes(shape.GetHistogram(), var, "Events")
    hist_data_signal.Draw("ESAME")
    leg.Draw("SAME")
    stdtxt = make_standard_text()
    stdtxt.Draw("SAME")
    cuttxt = make_bin_text(njet, btag, htbins)
    cuttxt.Draw("SAME")
    c.SaveAs("%s/%s_%s_%s_%s_%s.pdf" % (out_dir, out_stem, var, njet, btag, htbins[0]))


def make_plot_bins(var):
    """
    For a given variable, makes data VS background plots for all the
    relevant HT, Njets, Nbtag bins
    """
    for v in var:
        print "Doing plots for", v
        # for njet, btag, ht_bins in product(n_j, n_b, ht):
        #     make_plot(v, njet, btag, ht_bins)
        make_plot(v, "le3j", "eq0b", ["475_575"])


if __name__ == "__main__":
    print "Making lots of data VS bg plots..."
    make_plot_bins(plot_vars)

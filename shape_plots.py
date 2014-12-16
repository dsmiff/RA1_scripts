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

r.TH1.SetDefaultSumw2(r.kTRUE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
r.TH1.AddDirectory(r.kFALSE)

# input files
# ROOTdir = "/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/" # original buggy
ROOTdir = "/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/"  # re-run
# ROOTdir = "/Users/robina/Dropbox/AlphaT/Root_Files_01Dec_aT_0p53_globalAlphaT_v1" #alphaT in muon regions

# Variable(s) you want to plot
# "MHT", "AlphaT", "Meff", "dPhi*", "jet variables", "MET (corrected)", "MHT/MET (corrected)", "Number_Good_vertices",
plot_vars = ["Number_Btags", "AlphaT", "JetMultiplicity", "LeadJetPt", "LeadJetEta",
             "SecondJetPt", "SecondJetEta", "HT", "MHT", "MET_Corrected",
             "MHTovMET", "ComMinBiasDPhi_acceptedJets", "EffectiveMass", "Number_Good_verticies"][1:]

# Where you want to store plots
# And what you want to call the plots - will be out_dir/out_stem_<var>_<njet>_<btag>_<htbin>.pdf
# out_dir = "./28Nov_aT_0p53_v1/" # original buggy
out_dir = "./11Dec_aT_0p53_forRobin_v0/" # re-run
# out_dir = "./01Dec_aT_0p53_globalAlphaT_v1/" # alphaT in muon regions

out_stem = "plot"

# Define region bins
# CURRENTLY OVERRIDEN IN make_plots METHOD
HTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][3:]
ht_scheme = ["incl", "excl"][0]  # option for individual bin, or inclusive
n_j = ["le3j", "ge4j", "ge2j"][:2]
n_b = ["eq0b", "eq1b", "eq2b", "eq3b", "ge0b", "ge1b"][:2]

# MC processes that go into transfer factors
processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_signal_le1b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
                            "DiMuon": ['Zinv']}

processes_mc_signal_ge2b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop', 'Zinv'],
                            "DiMuon": []}  # for >= 2btags dimu region not used

# Control regions to get data shapes (+ proper titles for legend etc)
ctrl_regions = {"OneMuon": "Single #mu BG", "DiMuon": "#mu#mu BG"}

# Sytematics on TF (as a %). Fn on njets & HT
tf_systs = {
    "le3j": {"200_275": 4, "275_325": 6, "325_375": 6, "375_475": 8, "475_575": 8, "575_675": 12, "675_775": 12, "775_875": 17, "875_975": 17, "975_1075": 19, "1075": 19},
    "ge4j": {"200_275": 6, "275_325": 6, "325_375": 11, "375_475": 11, "475_575": 11, "575_675": 18, "675_775": 18, "775_875": 20, "875_975": 20, "975_1075": 26, "1075": 26}
}

class Ratio_Plot():
    """
    Class to make a ratio plot
    """

    def __init__(self, var, njet, btag, htbins, rebin, log):
        self.var = var
        self.njet = njet
        self.btag = btag
        self.htbins = htbins
        self.htstring = self.make_ht_string(htbins)
        self.rebin = rebin
        self.log = log
        self.autorange_x = True  # to auto set x range for non-empty range
        self.autorange_y = True  # to auto set y range for sensible range
        self.c = r.TCanvas()
        self.up = r.TPad("u","",0.01,0.25,0.99,0.99)
        self.dp = r.TPad("d","",0.01,0.01,0.99,0.25)
        self.dp.SetBottomMargin(1.3*self.dp.GetBottomMargin())
        self.hist_data_signal = None
        self.component_hists = []
        self.transfer_factors = {}
        self.shape_stack = r.THStack("shape_stack", "")
        self.errors_all_hists = False  # set true if you want errors on all component hists as well
        self.error_hists_stat = None
        self.error_hists_stat_syst = None
        self.hist_ratio = None # For ratio plot data/MC points
        self.hist_ratio_stat = None # For ratio plot MC stat err bars
        self.hist_ratio_stat_syst = None # For ratio plot MC stat+syst err bars
        self.stdtxt = self.make_standard_text()
        self.cuttxt = self.make_bin_text(custom="#alpha_{T} > 0.53 in signal region")
        self.leg = self.make_legend()
        self.c.cd()

        # Now make plots
        self.make_hists()
        self.make_main_plot(self.up)
        self.c.cd()
        self.make_ratio_plot(self.dp, self.hist_data_signal, self.error_hists_stat_syst[-1], self.error_hists_stat[-1], self.error_hists_stat_syst[-1])
        self.c.cd()


    def make_ht_string(self, htbins):
        htstring = htbins[0].split("_")[0] + "_"
        if (htbins[-1] != "1075"):
            htstring += htbins[-1].split("_")[-1]
        else:
            htstring += "Inf"
        return htstring


    def save(self, odir=None, name=None):
        self.c.cd()
        if not name:
            # check outdir exists
            opath = os.path.abspath(out_dir)
            if not os.path.isdir(opath):
                os.makedirs(opath)
            self.c.SaveAs("%s/%s_%s_%s_%s_%s.pdf" % (out_dir, out_stem, self.var, self.njet, self.btag, self.htstring))
        else:
            self.c.SaveAs(name)


    def color_hist(self, hist, line_color, fill_color, marker_color):
        """
        Set marker/line/fill color for histogram
        """
        hist.SetLineColor(line_color)
        hist.SetFillColor(fill_color)
        hist.SetMarkerColor(marker_color)


    def rebin_hist(self, hist, rebin=None):
        if not rebin:
            rebin = self.rebin
        if hasattr(rebin, "__len__"):
            return hist.Rebin(len(rebin)-1, hist.GetName(), rebin)
        else:
            if (hist.GetNbinsX() % rebin != 0):
                print "WARNING: rebin factor not exact divisor of number of bins - not rebinning"
                print "Original:", hist.GetNbinsX(), "Tried rebin factor:", rebin
                rebin = 1
            if rebin != 1:
                return hist.Rebin(int(rebin))
            return hist


    def style_hist(self, hist, region):
        """
        Do some aesthetic stylings on hists, & rebin
        """
        # if hasattr(self.rebin, "__len__"):
        #     print "we got bins"
        #     hist = hist.Rebin(len(self.rebin)-1, hist.GetName(), self.rebin)
        # else:
        #     hist.Rebin(self.rebin)

        if region == "OneMuon":
            self.color_hist(hist, r.kBlack, r.kViolet + 1, r.kViolet + 1)
        elif region == "DiMuon":
            self.color_hist(hist, r.kBlack, r.kOrange, r.kOrange)
        elif region == "Data":
            hist.SetMarkerColor(r.kBlack)
            # hist.SetMarkerSize(2)
            hist.SetMarkerStyle(20)
            hist.SetLineColor(r.kBlack)


    def style_hist_err1(self, hist):
        """
        Do some aesthetic stylings on error bars.
        """
        hist.SetMarkerStyle(0)
        hist.SetMarkerSize(0)
        hist.SetLineColor(r.kGray + 3)
        hist.SetLineWidth(0)
        hist.SetFillColor(r.kGray + 3)
        hist.SetFillStyle(3002)


    def style_hist_err2(self, hist):
        """
        Do some alternate stylings on error bars.
        """
        hist.SetMarkerStyle(0)
        hist.SetMarkerSize(0)
        hist.SetLineColor(r.kGray + 3)
        hist.SetLineWidth(0)
        hist.SetFillColor(r.kGray + 3)
        hist.SetFillStyle(3013)


    def style_hist_ratio(self, hist):
        """
        Do some stylings on ratio plot
        """
        hist.SetMarkerColor(r.kBlack)
        # hist.SetMarkerSize(2)
        hist.SetMarkerStyle(20)
        hist.SetLineColor(r.kBlack)
        hist.GetYaxis().SetTitle("Data/MC")
        ratioY = self.up.GetAbsHNDC() / self.dp.GetAbsHNDC()
        # ratioX = self.up.GetAbsVNDC() / self.dp.GetAbsVNDC()
        # apparently hist.GetYaxis().Set... doesn't really work here?
        hist.SetTitleSize(hist.GetYaxis().GetTitleSize()*ratioY, "Y")
        hist.SetLabelSize(hist.GetYaxis().GetLabelSize()*ratioY, "Y")
        hist.SetTitleOffset(hist.GetYaxis().GetTitleOffset()/ratioY, "Y")
        hist.SetLabelOffset(hist.GetYaxis().GetLabelOffset()*ratioY, "Y")
        hist.GetYaxis().SetNdivisions(6+(100*6))
        hist.GetYaxis().SetRangeUser(0, 3.0)

        hist.SetTitleSize(hist.GetXaxis().GetTitleSize()*ratioY, "X")
        hist.SetLabelSize(hist.GetXaxis().GetLabelSize()*ratioY, "X")
        # hist.SetTitleOffset(hist.GetXaxis().GetTitleOffset()/ratioY, "X")
        hist.SetTitleOffset(9999, "X")
        hist.SetLabelOffset(hist.GetXaxis().GetLabelOffset()*ratioY, "X")
        hist.GetXaxis().SetTickLength(hist.GetXaxis().GetTickLength()*ratioY)


    def title_axes(self, hist, xtitle, ytitle="Events"):
        """
        Apply title to axes, do offsets, sizes
        """
        hist.SetXTitle(xtitle)
        hist.SetYTitle(ytitle)
        hist.SetTitleOffset(hist.GetTitleOffset("Y") * 1.2, "Y")


    def make_legend(self):
        """
        Generate blank legend
        """
        leg = r.TLegend(0.68, 0.49, 0.87, 0.72)
        leg.SetFillColor(0)
        leg.SetFillStyle(0)
        leg.SetLineColor(0)
        leg.SetLineStyle(0)
        leg.SetLineWidth(0)
        return leg


    def make_standard_text(self):
        """
        Generate standard boring text
        """
        t = r.TPaveText(0.66, 0.73, 0.87, 0.87, "NDC")
        t.AddText("CMS 2012, #sqrt{s} = 8 TeV")
        t.AddText("")
        t.AddText("#int L dt = 18.493 fb^{-1}")
        t.SetFillColor(0)
        t.SetFillStyle(0)
        t.SetLineColor(0)
        t.SetLineStyle(0)
        t.SetLineWidth(0)
        return t


    def make_bin_text(self, custom=None):
        """
        Generate label of which bin
        """
        t = r.TPaveText(0.1, 0.91, 0.9, 0.95, "NDC")
        b_str = grabr.btag_string(self.btag) if grabr.btag_string(self.btag) else "geq 0 btag"
        if custom:
            tt = t.AddText("%s, %s, HT bin %s, %s" % (self.njet, b_str, self.htstring, custom))
        else:
            tt = t.AddText("%s, %s, HT bin %s" % (self.njet, b_str, self.htstring))
        tt.SetTextAlign(12)
        t.SetFillColor(0)
        t.SetFillStyle(0)
        t.SetLineColor(0)
        t.SetLineStyle(0)
        t.SetLineWidth(0)
        return t


    def autorange_xaxis(self, h_1, h_2):
        """
        Return x axis range such that only filled bins are shown,
        for both h_1 and h_2.
        Plus a bit of padding on the left, and a lot more on the right
        """
        # Loook for low edge
        low_1 = -1000000.
        low_2 = -1000000.
        found_low_1 = False
        found_low_2 = False

        for i in range(1, 1 + h_1.GetNbinsX()):
            if not found_low_1 and h_1.GetBinContent(i) > 0.:
                low_1 = h_1.GetBinLowEdge(i)
                found_low_1 = True
            if not found_low_2 and h_2.GetBinContent(i) > 0.:
                low_2 = h_2.GetBinLowEdge(i)
                found_low_2 = True

        # Look for high edge
        high_1 = 1000000.
        high_2 = 1000000.
        found_high_1 = False
        found_high_2 = False

        for i in range(1 + h_1.GetNbinsX(), 1, -1):
            if not found_high_1 and h_1.GetBinContent(i) > 0.:
                high_1 = h_1.GetBinLowEdge(i+1)
                found_high_1 = True
            if not found_high_2 and h_2.GetBinContent(i) > 0.:
                high_2 = h_2.GetBinLowEdge(i+1)
                found_high_2 = True

        xmin = low_1 if low_1 < low_2 else low_2
        xmax = high_1 if high_1 > high_2 else high_2
        # xmin -= (2*h_1.GetBinWidth(1))  # add little bit of padding to LHS
        xmax += 0.4 * (xmax-xmin)  # add some space to RHS
        print xmin, xmax
        return xmin, xmax


    def set_syst_errors(self, h, htbin, njet):
        """
        Turns stat errors into stat+syst errors using LUT at top
        """
        for i in range(1, h.GetNbinsX() + 1):
            syst =  h.GetBinContent(i) * tf_systs[njet][htbin] / 100.
            err = np.hypot(h.GetBinError(i), syst)
            # print syst, err
            h.SetBinError(i, err)


    def make_hists(self):
        """
        Makes component histograms for any plot: data in signal region, and a
        list of histograms that are BG estimates from doing
        data_control * transfer factor.
        Each hist in the list corresponds to one control region.
        Basically for each of the control regions, it gets data in
        control region, MC in signal & control regions (for all SM processes),
        and data in signal region. Then calculate transfer factor
        (MC_signal / MC_control), and scale data_control by that factor.
        """

        for ctrl in ctrl_regions:
            print "**** DOING", ctrl

            if "Muon" in ctrl:
                f_start = "Muon"
            elif "Photon" in ctrl:
                f_start = "Photon"

            # Cumulative for this region
            hist_total = None
            hist_stat_total = None
            hist_syst_total = None

            for ht in self.htbins:

                # Data in control region:
                hist_data_control = grabr.grab_plots(f_path="%s/%s_Data.root" % (ROOTdir, f_start),
                                                     sele=ctrl, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                hist_data_control.SetName(ctrl)  # for styling later
                print "Data in control reigon:", hist_data_control.Integral()

                # MC in signal region
                if "0" in self.btag or "1" in self.btag:
                    processes = processes_mc_signal_le1b
                else:
                    processes = processes_mc_signal_ge2b

                print "MC in signal region:"
                hist_mc_signal = None
                for p in processes[ctrl]:
                    MC_signal_tmp = grabr.grab_plots(f_path="%s/Had_%s.root" % (ROOTdir, p),
                                                     sele="Had", h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                    print p, MC_signal_tmp.Integral()
                    if not hist_mc_signal:
                        hist_mc_signal = MC_signal_tmp#.Clone()
                    else:
                        # hist_mc_signal.Add(MC_signal_tmp.Clone())
                        hist_mc_signal.Add(MC_signal_tmp)

                print "Total MC signal region:", hist_mc_signal.Integral()

                # MC in control region
                print "MC in control region:"
                hist_mc_control = None
                for p in processes_mc_ctrl:
                    MC_ctrl_tmp = grabr.grab_plots(f_path="%s/%s_%s.root" % (ROOTdir, f_start, p),
                                                   sele=ctrl, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                    print p, MC_ctrl_tmp.Integral()
                    if not hist_mc_control:
                        # hist_mc_control = MC_ctrl_tmp.Clone()
                        hist_mc_control = MC_ctrl_tmp
                    else:
                        # hist_mc_control.Add(MC_ctrl_tmp.Clone())
                        hist_mc_control.Add(MC_ctrl_tmp)

                print "Total MC control region:", hist_mc_control.Integral()

                hist_data_control.Multiply(hist_mc_signal)
                hist_data_control.Divide(hist_mc_control)
                # hist_data_control = self.rebin_hist(hist_data_control) # This segfaults soometimes

                # Calculate syst error on TF for this bin
                h_syst = hist_data_control.Clone()
                self.set_syst_errors(h_syst, ht, self.njet)
                if not hist_total:
                    hist_total = hist_data_control
                    hist_stat_total = hist_data_control.Clone()
                    hist_syst_total = h_syst
                else:
                    hist_total.Add(hist_data_control)
                    hist_stat_total.Add(hist_data_control.Clone())
                    hist_syst_total.Add(h_syst)

                print ctrl, "Estimate:", hist_data_control.Integral(), hist_data_control.GetNbinsX()

            hist_total = self.rebin_hist(hist_total)
            self.component_hists.append(hist_total)

            # Do stat+syst err hists for this control region & store (NB cumulative)
            hist_stat_total = self.rebin_hist(hist_stat_total)
            hist_syst_total = self.rebin_hist(hist_syst_total)

            self.style_hist_err1(hist_stat_total)
            self.style_hist_err2(hist_syst_total)

            if not self.error_hists_stat:
                self.error_hists_stat = [hist_stat_total]
                self.error_hists_stat_syst = [hist_syst_total]
            else:
                hist_stat_total.Add(self.error_hists_stat[-1])
                self.error_hists_stat.append(hist_stat_total)
                hist_syst_total.Add(self.error_hists_stat_syst[-1])
                self.error_hists_stat_syst.append(hist_syst_total)


        # Get data hist
        self.hist_data_signal = grabr.grab_plots(f_path="%s/Had_Data.root" % ROOTdir,
                                            sele="Had", h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=self.htbins)

        self.hist_data_signal = self.rebin_hist(self.hist_data_signal)
        print "Data SR:", self.hist_data_signal.Integral()


    def make_main_plot(self, pad):
        """
        For a given variable, NJet, Nbtag, HT bins,
        makes data VS background plot, where BG is from data control regions.
        Lots of ugly ROOT hacks in here (axis ranges, etc)
        """
        pad.Draw()
        pad.cd()

        self.style_hist(self.hist_data_signal, "Data")

        # Make stack of backgrounds, and put error bands on each contribution:
        # There is a ROOT bug whereby if you try and make copies of the hists,
        # put into a THStack, and tell it to plot with E2 and set a fill style
        # like 3013, only the last hist will actually render properly,
        # others will be blocky. So to avoid this we build up cumulative TH1s and
        # then draw those ontop of the main block colours. (5.34.21 MacOSX w/Cocoa)
        #
        # If you only want an error band on the total, then it's easy: make a clone
        # of stack.Last(), and Draw("E2").

        # Loop through shape components: mod style, add to THStack
        # Want to add hists to THStack by ascending Integral()
        self.component_hists.sort(key=lambda hist: hist.Integral())
        for h in self.component_hists:
            # Some shimmer BEFORE adding to stack
            self.style_hist(h, h.GetName())
            self.shape_stack.Add(h)

        print "BG estimate from data:", self.shape_stack.GetStack().Last().Integral()
        # print "BG estimate from data:", self.error_hists_stat[-1].Integral()

        # add entries to the legend
        self.leg.AddEntry(self.hist_data_signal, "Data + stat. error", "pl")
        for h in reversed(self.component_hists):
            self.leg.AddEntry(h, ctrl_regions[h.GetName()], "f")
        self.leg.AddEntry(self.error_hists_stat[-1], "Stat. error", "F")
        self.leg.AddEntry(self.error_hists_stat_syst[-1], "Stat. + syst. error", "F")

        # Get x range - but can only set it for the stack once you've drawn it (fail)
        xmin, xmax = self.autorange_xaxis(self.hist_data_signal, self.shape_stack.GetStack().Last())
        if self.autorange_x:
            self.hist_data_signal.SetAxisRange(xmin, xmax, "X")

        # Urgh trying to set y axis maximum correctly is a massive ball ache,
        # since THStack doesn't account for error properly (that's now 2 ROOT bugs)
        sum_stack = self.shape_stack.GetStack().Last()  # the "sum" of component hists
        max_stack = sum_stack.GetMaximum() + self.error_hists_stat_syst[-1].GetBinError(sum_stack.GetMaximumBin())
        max_data = self.hist_data_signal.GetMaximum() + self.hist_data_signal.GetBinError(self.hist_data_signal.GetMaximumBin())
        print max_stack, max_data

        if max_stack < 0. or max_data < 0.:
            raise Exception("max_stack (%f) or max_data(%f) < 0!" % (max_stack, max_data))

        # Finally draw all the pieces
        pad.SetLogy(self.log)
        pad.SetTicks()

        if max_stack > max_data:
            self.shape_stack.Draw("HIST")
            if self.autorange_x: self.shape_stack.GetXaxis().SetRangeUser(xmin, xmax)
            # r.gPad.Update();
            # ymin = r.gPad.GetUymin()
            if self.autorange_y:
                ymin = 0. # 0 for lin axis, non-0 for log
                if self.log:
                    self.shape_stack.SetMaximum(max_stack * 3.)
                    ymin = self.error_hists_stat[0].GetMinimum(0.) * 0.75
                    if (ymin <= 0.): ymin = 0.01
                else:
                    self.shape_stack.SetMaximum(max_stack * 1.1)
                self.shape_stack.SetMinimum(ymin)  # setting maximum somehow FUs min - do manually
            self.shape_stack.Draw("HIST")
            self.hist_data_signal.Draw("SAME")
        else:
            # Trust ROOT to set y axis sensibly
            self.hist_data_signal.Draw()
            self.shape_stack.Draw("HIST SAME")
            if self.autorange_x: self.shape_stack.GetXaxis().SetRangeUser(xmin, xmax)
            self.hist_data_signal.Draw("SAME")

        if self.autorange_x: [h.GetXaxis().SetRangeUser(xmin, xmax) for h in self.error_hists_stat]
        if self.autorange_x: [h.GetXaxis().SetRangeUser(xmin, xmax) for h in self.error_hists_stat_syst]
        if self.errors_all_hists:
            [h.Draw("E2 SAME") for h in self.error_hists_stat]
            [h.Draw("E2 SAME") for h in self.error_hists_stat_syst]
        else:
            self.error_hists_stat[-1].Draw("E2 SAME")
            self.error_hists_stat_syst[-1].Draw("E2 SAME")
        self.hist_data_signal.Draw("SAME")  # data points ontop of everything
        pad.RedrawAxis()  # important to put axis on top of all plots
        self.title_axes(self.hist_data_signal, self.var, "Events")
        self.title_axes(self.shape_stack.GetHistogram(), self.var, "Events")
        self.leg.Draw()
        self.stdtxt.Draw("SAME")
        self.cuttxt.Draw("SAME")


    def make_ratio_plot(self, pad, h_data, h_mc, h_mc_stat=None, h_mc_stat_syst=None, fit=True):
        """
        Makes the little data/MC ratio plot
        """
        pad.Draw()
        pad.cd()
        pad.SetTicks()

        self.hist_ratio = h_data.Clone("ratio")
        self.hist_ratio_stat = h_mc_stat.Clone("mcstat")
        self.hist_ratio_stat_syst = h_mc_stat_syst.Clone("mcstatsyst")

        # Only want stat errs from data in SR on points
        # Also construct MC error bars
        h_mc_no_err = h_mc.Clone()
        for i in range(1, 1+h_mc.GetNbinsX()):
            h_mc_no_err.SetBinError(i, 0)
            if self.hist_ratio_stat.GetBinContent(i) != 0.:
                self.hist_ratio_stat.SetBinError(i, self.hist_ratio_stat.GetBinError(i)/self.hist_ratio_stat.GetBinContent(i))
            self.hist_ratio_stat.SetBinContent(i, 1)
            if self.hist_ratio_stat_syst.GetBinContent(i) != 0.:
                self.hist_ratio_stat_syst.SetBinError(i, self.hist_ratio_stat_syst.GetBinError(i)/self.hist_ratio_stat_syst.GetBinContent(i))
            self.hist_ratio_stat_syst.SetBinContent(i, 1)

        self.hist_ratio.Divide(h_mc_no_err)
        self.style_hist_ratio(self.hist_ratio)
        self.style_hist_ratio(self.hist_ratio_stat)
        self.style_hist_err1(self.hist_ratio_stat)
        self.style_hist_err2(self.hist_ratio_stat_syst)

        # Draw all the bits
        self.hist_ratio_stat.Draw("E2")
        self.hist_ratio_stat_syst.Draw("E2 SAME")
        self.hist_ratio.Draw("EP SAME")
        r.gPad.Update();
        # min = self.hist_ratio.GetXaxis().GetXmin() # NOPE DOESN'T WORK
        # max = self.hist_ratio.GetXaxis().GetXmax()
        xmin, xmax = self.autorange_xaxis(h_data, h_mc)
        # For some unbelievably fucking stupid reason, I have to use
        # gPad.GetUxmax for upper edge, but xmin for lower edge as
        # gPad.GetUxmin mis reports it
        # And GetXaxis.GetMax/Min doesn't even work, it ignores the fact
        # I've told it to change range
        # Stupid piece of shit
        xmax = r.gPad.GetUxmax()
        self.l = r.TLine(xmin, 1, xmax, 1)
        self.l.SetLineWidth(2)
        self.l.SetLineStyle(2)
        self.l.Draw()

        # for i in range(1, 1+self.hist_ratio.GetNbinsX()):
        #     print i, self.hist_ratio.GetBinCenter(i), ",", self.hist_ratio.GetBinContent(i)

        # Do fit to ratio
        # if (fit):
        #     fitfn = r.TF1("fitfn", "[0]")
        #     fitfn.SetParameter(0, 1.)
        #     fitfn.SetParLimits(0, 0., 100.)
        #     fitfn.SetLineColor(r.kBlue)
        #     result = self.hist_ratio.Fit("fitfn", "+")


def make_plot_bins(var):
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
        # plot = Ratio_Plot(v, "le3j", "eq0b", ["375_475"], rebin, log)
        # plot.save()


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
        # plot = Ratio_Plot(v, "ge4j", "eq0b", ["375_475"], rebin, log)
        # plot.save()


    # For inclusive HT
    for v in var:
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
        plot = Ratio_Plot(v, "le3j", "eq0b", HTbins, rebin, log)
        plot.save()
        # plot = Ratio_Plot(v, "ge4j", "eq0b", HTbins, rebin, log)
        # plot.save()

    # plot = Ratio_Plot("SecondJetEta", "le3j", "eq0b", HTbins, 2, False)
    # plot.save()
    # plot = Ratio_Plot("HT", "le3j", "eq0b", HTbins, 5, True)
    # plot.save()

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


def do_all_the_plots():
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

    for v, njet, btag, ht in product(plot_vars, n_j, n_b, HTbins):
        if v in rebin_d:
            rebin = rebin_d[v]
        else:
            rebin = 2
        if v in log_these:
            log = True
        else:
            log = False

        print  v, njet, btag, [ht]
        plot = Ratio_Plot(v, njet, btag, [ht], rebin, log)
        plot.save()

    # inclusive HT
    rebin = 2
    rebin_d = {"Number_Btags": 1, "JetMultiplicity": 1, "MHTovMET": 1,
                "ComMinBiasDPhi_acceptedJets": 10, "AlphaT": alphaT_bins,
                "MET_Corrected": 8, "HT": 5, "SecondJetPt": 4, "EffectiveMass": 10,
                "MHT": 8, "LeadJetPt": 4}

    log = False
    log_these = ["AlphaT", "ComMinBiasDPhi_acceptedJets", "HT", "LeadJetPt", "SecondJetPt", "EffectiveMass"]
    for v, njet, btag in product(plot_vars, n_j, n_b):
        if v in rebin_d:
            rebin = rebin_d[v]
        else:
            rebin = 2
        if v in log_these:
            log = True
        else:
            log = False
        print v, njet, btag, HTbins
        # plot = Ratio_Plot(v, njet, btag, ht, rebin, log)
        # plot.save()


if __name__ == "__main__":
    print "Making lots of data VS bg plots..."
    # make_plot_bins(plot_vars)
    do_all_the_plots()

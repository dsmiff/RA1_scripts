"""
This script makes a data VS background plot, but gets the backgrounds from
DATA control region shape, not MC. To do this, we define several control regions
(for each BG source), use MC to calculate transfer factors, then scale the
data control region plot by that factor. Oh yeah and whack in stat + syst
uncertainties, latter from closure tests. (NB syst invalid for fine jet multiplicity)

We can do this for bins of Njets, Nbtag, HT. And we look at lots of variables.

Note that for inclusive HT, we do the prediction in each HT bin and sum together.
This is the way the main analysis does it...

And we make it look b-e-a-utiful.
"""

import logging
import plot_grabber as grabr
import ROOT as r
from itertools import product, izip
import math
import numpy as np
import os
import array

r.PyConfig.IgnoreCommandLineOptions = True
r.TH1.SetDefaultSumw2(r.kFALSE)
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetOptFit(1111)
r.TH1.AddDirectory(r.kFALSE)

# setup logger - mostly done in plot_grabber
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


## FOR NORMAL HADRONIC PLOTS
signal_proc = "Had"
# # MC processes that go into transfer factors
processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_signal_le1b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
                            "DiMuon": ['Zinv']}

processes_mc_signal_ge2b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop', 'Zinv'],
                            "DiMuon": []}  # for >= 2btags dimu region not used

# # Control regions to get data shapes (+ proper titles for legend etc)
ctrl_regions = {"OneMuon": "Single #mu BG", "DiMuon": "#mu#mu BG", "QCD": "QCD BG (MC)"}

## FOR DIMUON FROM PHOTON
# signal_proc = "DiMuon"
# # MC processes that go into transfer factors
# processes_mc_ctrl = ['MC']

# processes_mc_signal_le1b = {"Photon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']}

# processes_mc_signal_ge2b = {"Photon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']}

# # Control regions to get data shapes (+ proper titles for legend etc)
# ctrl_regions = {"Photon": "#mu#mu BG from #gamma"}

# Sytematics on TF (as a %). Fn on njets & HT
tf_systs = {
    "le3j": {"200_275": 4, "275_325": 6, "325_375": 6, "375_475": 8, "475_575": 8, "575_675": 12, "675_775": 12, "775_875": 17, "875_975": 17, "975_1075": 19, "1075": 19},
    "ge4j": {"200_275": 6, "275_325": 6, "325_375": 11, "375_475": 11, "475_575": 11, "575_675": 18, "675_775": 18, "775_875": 20, "875_975": 20, "975_1075": 26, "1075": 26}
}


def check_dir_exists(d):
    opath = os.path.abspath(d)
    if not os.path.isdir(opath):
        os.makedirs(opath)

class PredictionPlot():
    """
    Class to make plot from data, BG shapes from data, and a neat ratio plot below that.
    """

    def __init__(self, ROOTdir, out_dir, var, njet, btag, htbins, rebin, log, title, qcd=False):
        self.ROOTdir = ROOTdir
        self.fineJetMulti = "fineJetMulti" in ROOTdir # whether fine Jet Multiplciity or not
        self.out_stem = "Prediction" # used for folder & plot names
        self.var = var
        self.njet = njet
        self.njet_string = grabr.jet_string_fine(njet) if self.fineJetMulti else grabr.jet_string_old(njet)
        self.btag = btag
        self.btag_string = grabr.btag_string(btag) # e.g. eq0b -> btag_zero
        self.htbins = htbins  # can be single bin or many - if this is a list, then it'll *SUM* over all the ht bins
        self.htstring = self.make_ht_string(htbins)
        self.rebin = rebin
        self.log = log
        self.autorange_x = True  # to auto set x range for non-empty range
        self.autorange_y = True  # to auto set y range for sensible range
        unique = self.njet_string+self.btag_string+self.htstring+self.var  # need unique names to stop segfault
        unique = "" # but not when actually running...
        self.c = r.gROOT.FindObject("c"+unique)
        if not self.c:
            self.c = r.TCanvas("c"+unique, "", 1200, 1000)
        self.c.cd()  # this seems important to avoid segfaults
        self.up = r.TPad("u"+unique, "", 0.01, 0.25, 0.99, 0.99)
        self.dp = r.TPad("d"+unique, "", 0.01, 0.01, 0.99, 0.25)
        self.dp.SetBottomMargin(1.3 * self.dp.GetBottomMargin())
        self.hist_data_signal = None
        self.component_hists = []
        self.transfer_factors = {}
        self.shape_stack = r.THStack("shape_stack"+unique, "")
        self.errors_all_hists = False  # set true if you want errors on all component hists as well
        self.error_hists_stat = None
        self.error_hists_stat_syst = None
        self.hist_ratio = None # For ratio plot data/MC points
        self.hist_ratio_stat = None # For ratio plot MC stat err bars
        self.hist_ratio_stat_syst = None # For ratio plot MC stat+syst err bars
        self.stdtxt = self.make_standard_text()
        self.cuttxt = self.make_bin_text(custom=title)
        self.leg = self.make_legend()
        self.plot_components = False  # plots ALL components, for debugging
        self.outdir = "%s/%s_%s_%s" % (out_dir, njet, btag, self.htstring)  # dir for putting all plots
        check_dir_exists(self.outdir)
        self.qcd = qcd  # whether to add in QCD MC in signal region. NOTE: *NOT* included in ratio plot
        # output file dir+name (without extension)
        self.outname = "%s/%s_%s_%s_%s%s%s%s" % (self.outdir,
                                                 self.out_stem,
                                                 self.var,
                                                 self.njet_string,
                                                 self.btag_string,
                                                 "_" if self.btag_string else "",
                                                 self.htstring,
                                                 "_QCD" if self.qcd else "")


    def make_plots(self):
        """
        Main routine for this class to make the required hists,
        then style and plots them, then draw a ratio plot below.
        """
        self.make_hists()
        # Now make plots
        self.make_main_plot(self.up)
        self.c.cd()

        # Take out the QCD MC from the ratio plot
        hist_mc_stat = self.error_hists_stat[:]
        hist_mc_stat_syst = self.error_hists_stat_syst[:]
        for h1,h2 in zip(hist_mc_stat,hist_mc_stat_syst):
            if "QCD" in h1.GetName().upper():
                hist_mc_stat.remove(h1)
                hist_mc_stat_syst.remove(h2)
        self.make_ratio_plot(self.dp, self.hist_data_signal, hist_mc_stat_syst[-1], hist_mc_stat[-1], hist_mc_stat_syst[-1])
        self.c.cd()


    def make_ht_string(self, htbins):
        """
        Make string out of HT bin(s)
        """
        # test if list or string
        if hasattr(htbins, "__iter__"):
            htstring = htbins[0].split("_")[0]
            if (htbins[-1] != "1075"):
                htstring += "_"+htbins[-1].split("_")[-1]
            else:
                # If doing inclusive, then want "_upwards"
                # If just the 1075 - Inf bin, no "upwards"
                if len(htbins) > 1:
                    htstring += "_upwards"
        else:
            htstring = htbins
        return htstring


    def save(self, odir=None, name=None):
        """
        Save the whole plot to file, using some auto directory structure if needed
        """
        self.c.cd()
        if not name:
            self.c.SaveAs("%s.pdf" % self.outname)
            self.c.SaveAs("%s.png" % self.outname)
            self.c.SaveAs("%s.C" % self.outname)
        else:
            self.c.SaveAs("%s/%s" %(odir, name))


    def color_hist(self, hist, line_color, fill_color, marker_color):
        """
        Set marker/line/fill color for histogram
        """
        hist.SetLineColor(line_color)
        hist.SetFillColor(fill_color)
        hist.SetMarkerColor(marker_color)


    def rebin_hist(self, hist, rebin=None):
        """
        Rebin a histogram either by combining rebin bins together, or by
        asking for a specific binning (pass list as rebin arg)

        NOTE: if you're using a ROOT version earlier than 5.34/22, you're
        gonna have abad time if you try setting the upper bin beyond the current
        upper bin edge. See: https://sft.its.cern.ch/jira/browse/ROOT-6706

        I don't want anyone else to waste a day of their life doing this.
        """
        if not rebin:
            rebin = self.rebin
        if hasattr(rebin, "__len__"):
            return hist.Rebin(len(rebin)-1, hist.GetName(), rebin)
        else:
            if (hist.GetNbinsX() % rebin != 0):
                log.warning("WARNING: rebin factor not exact divisor of number of bins - not rebinning")
                log.warning("Original: %d, Tried rebin factor: %d" % (hist.GetNbinsX(), rebin))
                rebin = 1
            if rebin != 1:
                return hist.Rebin(int(rebin))
            return hist


    def style_hist(self, hist, region):
        """
        Do some aesthetic stylings on hists, & rebin
        """
        if "OneMuon" in region:
            self.color_hist(hist, line_color=r.kBlack, fill_color=r.kViolet+1, marker_color=r.kViolet+1)
        elif "DiMuon" in region:
            self.color_hist(hist, line_color=r.kBlack, fill_color=r.kOrange, marker_color=r.kOrange)
        elif "Photon" in region:
            self.color_hist(hist, line_color=r.kBlack, fill_color=r.kGreen+2, marker_color=r.kGreen+2)
        elif "Data" in region:
            hist.SetMarkerColor(r.kBlack)
            hist.SetMarkerSize(1.2)
            hist.SetMarkerStyle(20)
            hist.SetLineColor(r.kBlack)
        elif "QCD" in region:
            self.color_hist(hist, line_color=r.kBlack, fill_color=r.kAzure+1, marker_color=r.kAzure+1)


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
        hist.SetMarkerSize(1.2)
        hist.SetMarkerStyle(20)
        hist.SetLineColor(r.kBlack)
        hist.GetYaxis().SetTitle("Data/Pred")
        if self.qcd:
            hist.GetYaxis().SetTitle("Data/Pred (no QCD)")
        ratioY = self.up.GetAbsHNDC() / self.dp.GetAbsHNDC()
        # ratioX = self.up.GetAbsVNDC() / self.dp.GetAbsVNDC()
        # apparently hist.GetYaxis().Set... doesn't really work here?
        hist.SetTitleSize(hist.GetYaxis().GetTitleSize()*ratioY, "Y")
        hist.SetLabelSize(hist.GetYaxis().GetLabelSize()*ratioY, "Y")
        hist.SetTitleOffset(hist.GetYaxis().GetTitleOffset()/ratioY, "Y")
        hist.SetLabelOffset(hist.GetYaxis().GetLabelOffset()*ratioY, "Y")
        hist.GetYaxis().SetNdivisions(6+(100*6))
        hist.GetYaxis().SetRangeUser(0, 2.0)

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
        leg = r.TLegend(0.7, 0.49, 0.88, 0.72)
        # leg.SetFillColorAlpha(r.kWhite, 0.5)
        leg.SetFillColor(0)
    	leg.SetFillStyle(0)
        # leg.SetCornerRadius(0.5)
        leg.SetLineColor(0)
        leg.SetLineStyle(0)
        leg.SetLineWidth(0)
        # leg.SetLineColorAlpha(0, 0)
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
        t = r.TPaveText(0.1, 0.91, 0.9, 0.95, "NDC NB")
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
        # Look for low edge
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
        log.debug("xmin: %g, xmax: %g"% (xmin, xmax))
        return xmin, xmax


    def plot_component(self, h, name):
        """
        Plot h on a separate canvas
        """
        # get a canvas - reuse the old one if it's available
        cc = r.gROOT.FindObject("cc")
        if not cc:
            cc = r.TCanvas("cc","")
            # cc = r.gRoot.FindObject("cc")
        cc.cd()
        cc.SetLogy(self.log)
        cc.SetTicks()
        cc.SetGrid()
        hh = h.Clone()
        self.title_axes(hh, self.var, "Events")
        self.rebin_hist(hh).Draw("HISTE")
        self.cuttxt.Draw("")
        # make folder for this var
        odir = "%s/%s" % (self.outdir, self.var)
        check_dir_exists(odir)
        ext = "" if ".pdf" in name else ".pdf"
        cc.SaveAs("%s/%s%s" % (odir, name, ext))


    def set_syst_errors(self, h, htbin, njet):
        """
        Turns stat errors into stat+syst errors using LUT at top
        """
        for i in range(1, h.GetNbinsX() + 1):
            try:
                syst =  h.GetBinContent(i) * tf_systs[njet][htbin] / 100.
            except KeyError:
                syst = 0
            if self.fineJetMulti:
                syst = 0
            err = np.hypot(h.GetBinError(i), syst)
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

            if "Muon" in ctrl:
                ctrl_start = "Muon"
            elif "Photon" in ctrl:
                ctrl_start = "Photon"

            sig_start = "Had"
            if "Muon" in signal_proc:
                sig_start = "Muon"
            elif "Photon" in signal_proc:
                sig_start = "Photon"


            # Cumulative for this region
            hist_total = None
            hist_stat_total = None
            hist_syst_total = None

            # Processes for MC in signal region
            # Check that there are actually processes to run over for this ctrl region...
            if "0" in self.btag or "1" in self.btag:
                processes = processes_mc_signal_le1b
            else:
                processes = processes_mc_signal_ge2b

            if ctrl in processes:
                if not processes[ctrl]:
                        continue

                log.debug("**** DOING %s" % ctrl)

                for ht in self.htbins:

                    # Data in control region:
                    log.debug("Data in control region")
                    hist_data_control = grabr.grab_plots(f_path="%s/%s_Data.root" % (self.ROOTdir, ctrl_start),
                                                         sele=ctrl, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                    hist_data_control.SetName(ctrl)  # for styling later
                    hist_data_control = self.rebin_hist(hist_data_control)
                    if self.plot_components:
                        self.plot_component(hist_data_control, "data_control_%s_%s" % (ctrl, self.make_ht_string(ht)))
                    log.debug("Data in control reigon: %g" % hist_data_control.Integral())

                    # MC in signal region
                    log.debug("MC in signal region:")
                    hist_mc_signal = None
                    for p in processes[ctrl]:
                        MC_signal_tmp = grabr.grab_plots(f_path="%s/%s_%s.root" % (self.ROOTdir, sig_start, p),
                                                         sele=signal_proc, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                        log.debug("%s %g" % (p, MC_signal_tmp.Integral()))
                        if not hist_mc_signal:
                            hist_mc_signal = self.rebin_hist(MC_signal_tmp)
                        else:
                            hist_mc_signal.Add(self.rebin_hist(MC_signal_tmp))

                    log.debug("Total MC signal region: %g" % hist_mc_signal.Integral())
                    if self.plot_components:
                        self.plot_component(hist_mc_signal, "hist_mc_signal_%s_%s" % (ctrl, self.make_ht_string(ht)))

                    # MC in control region
                    log.debug("MC in control region:")
                    hist_mc_control = None
                    for p in processes_mc_ctrl:
                        MC_ctrl_tmp = grabr.grab_plots(f_path="%s/%s_%s.root" % (self.ROOTdir, ctrl_start, p),
                                                       sele=ctrl, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                        log.debug("%s %g" % (p, MC_ctrl_tmp.Integral()))
                        if not hist_mc_control:
                            hist_mc_control = self.rebin_hist(MC_ctrl_tmp)
                        else:
                            hist_mc_control.Add(self.rebin_hist(MC_ctrl_tmp))

                    log.debug("Total MC control region: %g" % hist_mc_control.Integral())
                    if self.plot_components:
                        self.plot_component(hist_mc_control, "hist_mc_control_%s_%s" % (ctrl, self.make_ht_string(ht)))

                    hist_mc_signal.Divide(hist_mc_control)
                    if self.plot_components:
                        self.plot_component(hist_mc_signal, "mc_ratio_%s_%s" % (ctrl, self.make_ht_string(ht)))

                    hist_data_control.Multiply(hist_mc_signal)
                    if self.plot_components:
                        self.plot_component(hist_data_control, "scaled_data_%s_%s" % (ctrl, self.make_ht_string(ht)))
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

                    log.debug("%s Estimate: %g %g" % (ctrl, hist_data_control.Integral(), hist_data_control.GetNbinsX()))

                # Add the prediction to a list
                self.component_hists.append(hist_total)

                # Do stat+syst err hists for this control region & store (NB cumulative)
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

        # Add in QCD in signal region if desired
        if self.qcd:
            log.debug("**** DOING QCD")
            hist_qcd = None
            hist_qcd_stat = None
            hist_qcd_syst = None
            for ht in self.htbins:
                h_qcd_tmp = grabr.grab_plots(f_path="%s/%s_%s.root" % (self.ROOTdir, "Had", "QCD"),
                                             sele=signal_proc, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=ht)
                log.debug("QCD (%s): %g" % (ht, h_qcd_tmp.Integral()))
                h_qcd_tmp.SetName("QCD")  # for styling later
                h_qcd_tmp = self.rebin_hist(h_qcd_tmp)
                if not hist_qcd:
                    hist_qcd = h_qcd_tmp
                else:
                    hist_qcd.Add(h_qcd_tmp)
                # stat & syst error bars for this ht bin (as syst ht-specific)
                h_qcd_stat = h_qcd_tmp.Clone()
                h_qcd_syst = h_qcd_tmp.Clone()
                self.set_syst_errors(h_qcd_syst, ht, self.njet)
                if not hist_qcd_stat:
                    hist_qcd_stat = h_qcd_stat
                    hist_qcd_syst = h_qcd_syst
                else:
                    hist_qcd_stat.Add(h_qcd_stat)
                    hist_qcd_syst.Add(h_qcd_syst)

            self.component_hists.append(hist_qcd)
            log.debug("Total QCD: %g" % hist_qcd.Integral())

            # stat & syst error bars for QCD overall
            self.style_hist_err1(hist_qcd_stat)
            self.style_hist_err2(hist_qcd_syst)
            hist_qcd_stat.Add(self.error_hists_stat[-1])
            self.error_hists_stat.append(hist_qcd_stat)
            hist_qcd_syst.Add(self.error_hists_stat_syst[-1])
            self.error_hists_stat_syst.append(hist_qcd_syst)
            log.debug(hist_qcd_stat.Integral())

        # Get data hist
        sig_start = "Had"
        if "Muon" in signal_proc:
            sig_start = "Muon"
        elif "Photon" in signal_proc:
            sig_start = "Photon"
        self.hist_data_signal = grabr.grab_plots(f_path="%s/%s_Data.root" % (self.ROOTdir, sig_start),
                                            sele=signal_proc, h_title=self.var, njet=self.njet, btag=self.btag, ht_bins=self.htbins)

        self.hist_data_signal = self.rebin_hist(self.hist_data_signal)
        log.debug("Data SR: %g" % self.hist_data_signal.Integral())


    def make_main_plot(self, pad):
        """
        For a given variable, NJet, Nbtag, HT bins,
        makes data VS background plot, where BG is from data control regions.
        Lots of ugly ROOT hacks in here (axis ranges, etc)
        """
        self.c.cd()
        pad.Draw()
        pad.cd()
        # self.hist_data_signal.SetBinErrorOption(r.TH1.kPoisson)
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
        # EXCEPT for QCD hist - in which case we add it last, if it exists
        self.component_hists.sort(key=lambda hist: hist.Integral())
        for h in self.component_hists:
            h.SetBinErrorOption(r.TH1.kPoisson)
            # Some shimmer BEFORE adding to stack
            self.style_hist(h, h.GetName())
            if "QCD" not in h.GetName():
                self.shape_stack.Add(h)

        self.shape_stack.Add(next((h for h in self.component_hists if "QCD" in h.GetName()), None))
        log.debug("BG estimate from data: %g" % self.shape_stack.GetStack().Last().Integral())

        # add entries to the legend
        self.leg.AddEntry(self.hist_data_signal, "Data + stat. error", "pl")
        for h in reversed(self.component_hists):
            self.leg.AddEntry(h, ctrl_regions[h.GetName()], "f")
        self.leg.AddEntry(self.error_hists_stat[-1], "Stat. error", "F")
        if self.fineJetMulti:
            self.leg.AddEntry(self.error_hists_stat_syst[-1], "Stat. + syst. error NULL", "F")
        else:
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
        log.debug("max_stack %g, max_data %g" % (max_stack, max_data))

        if max_stack < 0. or max_data < 0.:
            raise Exception("max_stack (%f) or max_data(%f) < 0!" % (max_stack, max_data))

        # Finally draw all the pieces
        pad.SetLogy(self.log)
        pad.SetTicks()

        if max_stack > max_data:
            self.shape_stack.Draw("HIST")
            if self.autorange_x:
                self.shape_stack.GetXaxis().SetRangeUser(xmin, xmax)
            # r.gPad.Update();
            # ymin = r.gPad.GetUymin()
            if self.autorange_y:
                # Find the minimum of all the hists - use the error ones
                # as we want to see the error bar as well
                # This isn't trivial, as cnanot be 0 for log scale, and not
                # every hist has entries
                ymin = 0. # 0 for lin axis, non-0 for log
                if self.log:
                    self.shape_stack.SetMaximum(max_stack * 3.)
                    # get first hist with > 0 entries, as calling GetMinimum
                    # on one with 0 entries returns a dud number
                    h_nonzero = next((h for h in self.error_hists_stat if h.GetEntries() > 0), -1)
                    if h_nonzero:
                        ymin = h_nonzero.GetMinimum(0) * 0.75
                    else:
                        ymin = 0.1
                    # safeguard against stupid values
                    if (ymin <= 0.):
                        ymin = 0.01
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
        # pad.RedrawAxis()  # important to put axis on top of all plots
        r.gPad.RedrawAxis()
        self.title_axes(self.hist_data_signal, self.var, "Events")
        self.title_axes(self.shape_stack.GetHistogram(), self.var, "Events")
        self.leg.Draw()
        self.stdtxt.Draw("SAME")
        self.cuttxt.Draw("SAME")


    def make_ratio_plot(self, pad, h_data, h_mc, h_mc_stat=None, h_mc_stat_syst=None, fit=False):
        """
        Makes the little data/MC ratio plot
        h_mc is the total prediction
        h_mc_stat is the hist of the total stat error on the prediction
        h_mc_stat_syst is the hist of the total stat+syst error on the prediction
        fit is whether to fit a straight line to the ratio points.
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
        #
        # Actually this still mucks up sometimes
        xmax = r.gPad.GetUxmax()
        self.l = r.TLine(xmin, 1, xmax, 1)
        self.l.SetLineWidth(2)
        self.l.SetLineStyle(2)
        self.l.Draw()

        # Do fit to ratio
        # if (fit):
        #     fitfn = r.TF1("fitfn", "[0]")
        #     fitfn.SetParameter(0, 1.)
        #     fitfn.SetParLimits(0, 0., 100.)
        #     fitfn.SetLineColor(r.kBlue)
        #     result = self.hist_ratio.Fit("fitfn", "+")

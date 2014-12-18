import ROOT as r
import plot_grabber as grabr
import os

r.TH1.SetDefaultSumw2(True)
r.gROOT.SetBatch(1)

processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_signal_le1b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
                            "DiMuon": ['Zinv']}

c = r.TCanvas()
c.SetLogy()

folder = "/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/"
out_dir = "./11Dec_aT_0p53_forRobin_v0/"
njet = "ge4j"
btag = "eq0b"
htbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
          "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"][2]

var = "AlphaT"

def check_dir(odir):
    """
    Check directory exists
    """
    opath = os.path.abspath(odir)
    if not os.path.isdir(opath):
        os.makedirs(opath)
        print "Made dir:", opath


def make_component_plots(var=var, njet=njet, btag=btag, htbins=htbins):

    check_dir("%s/%s_%s_%s/%s" % (out_dir, njet, btag, htbins, var))

    # Data in SR
    had_data = grabr.grab_plots(f_path="%s/Had_Data.root" % folder,
                                sele = "Had", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
    had_data.Rebin(10)
    had_data.Draw("HISTE")
    c.SaveAs("%s/%s_%s_%s/%s/data_had.pdf" % (out_dir, njet, btag, htbins, var))

    # Data in OneMu CR
    mu_data = grabr.grab_plots(f_path="%s/Muon_Data.root" % folder,
                                sele = "OneMuon", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
    mu_data.Sumw2()
    mu_data.Rebin(10)
    mu_data.Draw("HISTE")
    c.SaveAs("%s/%s_%s_%s/%s/data_onemu.pdf" % (out_dir, njet, btag, htbins, var))

    # Data in DiMu CR
    dimu_data = grabr.grab_plots(f_path="%s/Muon_Data.root" % folder,
                                sele = "DiMuon", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
    dimu_data.Rebin(10)
    c.SetLogy()
    dimu_data.Draw("HISTE")

    c.SaveAs("%s/%s_%s_%s/%s/data_dimu.pdf" % (out_dir, njet, btag, htbins, var))

    # Set all data to be black
    for h in [had_data, mu_data, dimu_data]:
        h.SetLineColor(r.kBlack)
        h.SetMarkerColor(r.kBlack)
        h.SetMarkerStyle(21)


    # MC in SR, with and without Zinv
    mc_had = None
    for p in processes_mc_signal_le1b["OneMuon"]:
        print p
        h = grabr.grab_plots(f_path="%s/Had_%s.root" % (folder, p),
                                sele = "Had", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
        h.Sumw2()
        h.Rebin(10)
        if not mc_had:
            mc_had = h.Clone()
        else:
            mc_had.Add(h.Clone())

    mc_had_noZinv = mc_had.Clone()
    mc_had_noZinv.Draw("HISTE")
    c.SaveAs("%s/%s_%s_%s/%s/mc_had_noZinv.pdf" % (out_dir, njet, btag, htbins, var))

    mc_had_zinv = grabr.grab_plots(f_path="%s/Had_Zinv.root" % folder,
                                sele = "Had", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
    mc_had_zinv.Sumw2()
    mc_had_zinv.Rebin(10)
    mc_had_zinv.Draw("HISTE")
    c.SaveAs("%s/%s_%s_%s/%s/mc_had_zinv.pdf" % (out_dir, njet, btag, htbins, var))

    mc_had.Add(mc_had_zinv.Clone())

    mc_had.Draw("HISTE")
    print mc_had.Integral()
    c.SaveAs("%s/%s_%s_%s/%s/mc_had_withZinv.pdf" % (out_dir, njet, btag, htbins, var))

    had_data.Draw("SAME")
    c.SaveAs("%s/%s_%s_%s/%s/both_had.pdf" % (out_dir, njet, btag, htbins, var))

    # MC in OneMu CR
    mc_onemu = None
    for p in processes_mc_ctrl:
        print p
        h = grabr.grab_plots(f_path="%s/Muon_%s.root" % (folder,p),
                                sele = "OneMuon", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
        h.Sumw2()
        h.Rebin(10)
        if not mc_onemu:
            mc_onemu = h.Clone()
        else:
            mc_onemu.Add(h.Clone())

    mc_onemu.Draw("HISTE")
    c.SaveAs("%s/%s_%s_%s/%s/mc_onemu.pdf" % (out_dir, njet, btag, htbins, var))

    # Mc in DiMu CR
    mc_dimu = None
    for p in processes_mc_ctrl:
        print p
        h = grabr.grab_plots(f_path="%s/Muon_%s.root" % (folder,p),
                                sele = "DiMuon", h_title = var, njet = njet,
                                btag = btag, ht_bins = htbins)
        h.Sumw2()
        h.Rebin(10)
        if not mc_dimu:
            mc_dimu = h.Clone()
        else:
            mc_dimu.Add(h.Clone())
    mc_dimu.Draw("HISTE")

    c.SetLogy()
    c.SaveAs("%s/%s_%s_%s/%s/mc_dimu.pdf" % (out_dir, njet, btag, htbins, var))


    mc_ratio = mc_had.Clone() # has zinv in SR so use onemu only
    mc_ratio.Divide(mc_onemu)
    mc_ratio.Draw()
    c.SaveAs("%s/%s_%s_%s/%s/mc_ratio_withZinv.pdf" % (out_dir, njet, btag, htbins, var))

    mc_ratio_onemu = mc_had_noZinv.Clone()
    mc_ratio_onemu.Divide(mc_onemu)
    mc_ratio_onemu.Draw()
    c.SaveAs("%s/%s_%s_%s/%s/mc_ratio_onemu.pdf" % (out_dir, njet, btag, htbins, var))

    mc_ratio_dimu = mc_had_zinv.Clone()
    mc_ratio_dimu.Divide(mc_dimu)
    mc_ratio_dimu.Draw()
    c.SaveAs("%s/%s_%s_%s/%s/mc_ratio_dimu.pdf" % (out_dir, njet, btag, htbins, var))

    c.SetLogy(0)

    mu_data_scaled = mu_data.Clone() # for zinv in SR, onemu only
    mu_data_scaled.Multiply(mc_ratio)
    mu_data_scaled.Draw()
    c.SaveAs("%s/%s_%s_%s/%s/mu_data_scaled.pdf" % (out_dir, njet, btag, htbins, var))

    mu_data_scaled_proper = mu_data.Clone()
    mu_data_scaled_proper.Multiply(mc_ratio_onemu)
    mu_data_scaled_proper.Draw()
    c.SaveAs("%s/%s_%s_%s/%s/mu_data_scaled_proper.pdf" % (out_dir, njet, btag, htbins, var))

    dimu_data_scaled_proper = dimu_data.Clone()
    dimu_data_scaled_proper.Multiply(mc_ratio_dimu)
    dimu_data_scaled_proper.Draw()
    c.SetLogy()
    c.SaveAs("%s/%s_%s_%s/%s/dimu_data_scaled_proper.pdf" % (out_dir, njet, btag, htbins, var))

    mu_data_scaled_proper.Add(dimu_data_scaled_proper)
    mu_data_scaled_proper.Draw()
    mc_had.Draw("SAME")
    c.SetLogy()
    c.SaveAs("%s/%s_%s_%s/%s/total.pdf" % (out_dir, njet, btag, htbins, var))


if __name__ == "__main__":
    make_component_plots()
import ROOT as r
import plot_grabber as grabr

r.TH1.SetDefaultSumw2(True)

processes_mc_ctrl = ['DY', 'DiBoson', 'TTbar', 'WJets', 'Zinv', 'SingleTop']

processes_mc_signal_le1b = {"OneMuon": ['DY', 'DiBoson', 'TTbar', 'WJets', 'SingleTop'],
                            "DiMuon": ['Zinv']}

c = r.TCanvas()

# Data in SR
had_data = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Had_Data.root",  sele = "Had", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
had_data.Rebin(10)
had_data.Draw("HISTE")
print had_data.Integral()
c.SaveAs("data_had.pdf")

# Data in OneMu
mu_data = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Muon_Data.root",
                            sele = "OneMuon", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
mu_data.Sumw2()
mu_data.Rebin(10)
mu_data.Draw("HISTE")
c.SaveAs("data_onemu.pdf")

# Data in DiMu
dimu_data = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Muon_Data.root",
                            sele = "DiMuon", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
dimu_data.Rebin(10)
c.SetLogy()
dimu_data.Draw("HISTE")

c.SaveAs("data_dimu.pdf")

# Set all data to be black
for h in [had_data, mu_data, dimu_data]:
    h.SetLineColor(r.kBlack)
    h.SetMarkerColor(r.kBlack)
    h.SetMarkerStyle(21)


# MC in SR, with and without Zinv
mc_had = None
for p in processes_mc_signal_le1b["OneMuon"]:
    print p
    h = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Had_%s.root" % p,
                            sele = "Had", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
    h.Sumw2()
    h.Rebin(10)
    if not mc_had:
        mc_had = h.Clone()
    else:
        mc_had.Add(h.Clone())

mc_had_noZinv = mc_had.Clone()
mc_had_noZinv.Draw("HISTE")
c.SaveAs("mc_had_noZinv.pdf")

mc_had_zinv = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Had_Zinv.root",
                            sele = "Had", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
mc_had_zinv.Sumw2()
mc_had_zinv.Rebin(10)
mc_had_zinv.Draw("HISTE")
c.SaveAs("mc_had_zinv.pdf")

mc_had.Add(mc_had_zinv.Clone())

mc_had.Draw("HISTE")
print mc_had.Integral()
c.SaveAs("mc_had.pdf")

had_data.Draw("SAME")
c.SaveAs("both_had.pdf")

# MC in OneMu CR
mc_onemu = None
for p in processes_mc_ctrl:
    print p
    h = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Muon_%s.root" % p,
                            sele = "OneMuon", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
    h.Sumw2()
    h.Rebin(10)
    if not mc_onemu:
        mc_onemu = h.Clone()
    else:
        mc_onemu.Add(h.Clone())

mc_onemu.Draw("HISTE")
c.SaveAs("mc_onemu.pdf")

# Mc in DiMu CR
mc_dimu = None
for p in processes_mc_ctrl:
    print p
    h = grabr.grab_plots(f_path="/Users/robina/Dropbox/AlphaT/Root_Files_11Dec_aT_0p53_forRobin_v0/Muon_%s.root" % p,
                            sele = "DiMuon", h_title = "ComMinBiasDPhi_acceptedJets", njet = "le3j",
                            btag = "eq0b", ht_bins = ["375_475"])
    h.Sumw2()
    h.Rebin(10)
    if not mc_dimu:
        mc_dimu = h.Clone()
    else:
        mc_dimu.Add(h.Clone())


c = r.TCanvas()
mc_dimu.Draw("HISTE")
c.SetLogy()
c.SaveAs("mc_dimu.pdf")


mc_ratio = mc_had.Clone() # has zinv in SR so use onemu only
mc_ratio.Divide(mc_onemu)
mc_ratio.Draw()
c.SaveAs("mc_ratio_withZinv.pdf")

mc_ratio_onemu = mc_had_noZinv.Clone()
mc_ratio_onemu.Divide(mc_onemu)
mc_ratio_onemu.Draw()
c.SaveAs("mc_ratio_onemu.pdf")

mc_ratio_dimu = mc_had_zinv.Clone()
mc_ratio_dimu.Divide(mc_dimu)
mc_ratio_dimu.Draw()
c.SaveAs("mc_ratio_dimu.pdf")

c.SetLogy(0)

mu_data_scaled = mu_data.Clone() # for zinv in SR, onemu only
mu_data_scaled.Multiply(mc_ratio)
mu_data_scaled.Draw()
c.SaveAs("mu_data_scaled.pdf")

mu_data_scaled_proper = mu_data.Clone()
mu_data_scaled_proper.Multiply(mc_ratio_onemu)
mu_data_scaled_proper.Draw()
c.SaveAs("mu_data_scaled_proper.pdf")

dimu_data_scaled_proper = dimu_data.Clone()
dimu_data_scaled_proper.Multiply(mc_ratio_dimu)
dimu_data_scaled_proper.Draw()
c.SetLogy()
c.SaveAs("dimu_data_scaled_proper.pdf")

mu_data_scaled_proper.Add(dimu_data_scaled_proper)
mu_data_scaled_proper.Draw()
mc_had.Draw("SAME")
c.SetLogy()
c.SaveAs("total.pdf")
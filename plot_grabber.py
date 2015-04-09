import ROOT as r
from copy import deepcopy
import logging


# setup logger
console_handler = logging.StreamHandler()
root = logging.getLogger()
root.addHandler(console_handler)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def get_dirs(htbins = None, sele = "", btag = "", keyword = ""):
    """get the list of dirs to access multi files"""

    btag_str = btag_string(btag)

    # if htbins is a string, make it a single length list
    if type(htbins) == type(""):
        htbins = [htbins]

    out = []
    for ht in htbins:
        this_bin = []
        if btag_str: this_bin.append(btag_str)
        if sele != "Had":
            this_bin.append(sele)
        this_bin.append(ht)
        if keyword: this_bin.append(keyword)
        out.append("_".join(this_bin))
    return out

def btag_string(btag = ""):
    """get the relevant btag histo string"""

    d = {
            "eq0b": "btag_zero",
            "eq1b": "btag_one",
            "eq2b": "btag_two",
            "eq3b": "btag_three",
            "ge0b": "",
            "ge1b": "btag_morethanzero",
            "ge2b": "btag_morethanone",
            "ge3b": "btag_morethantwo",
            "ge4b": "btag_morethanthree"
        }

    return d[btag]

def jet_string_old(jet = ""):
    """get the relevant jet histo string"""

    if jet == "le3j":
        return "2"
    elif jet == "ge4j":
        return "3"
    else:
        return "all"

def jet_string_fine(jet = ""):
    """get the relevant jet histo string for fine jet multiplicity"""

    jet_cats = {
        "eq2j": "1",
        "eq3j": "2",
        "eq4j": "3",
        "ge5j": "4",
    }

    try:
        return jet_cats[jet]
    except KeyError:
        return None

def trig_eff_old(sele = "OneMuon", ht = "", njet = ""):
    """ list trigger efficiencies """

    # if inclusive jet selection, use ge4j effs
    if njet == "all":
        njet = "2"

    if "OneMuon" in sele:
        d = {"150_2": 0.872,"150_3": 0.881,
                "200_2": 0.875,"200_3": 0.881,
                "275_2": 0.878,"275_3": 0.882,
                "325_2": 0.879,"325_3": 0.884,
                "375_2": 0.881,"375_3": 0.886,
                "475_2": 0.882,"475_3": 0.888,
                "575_2": 0.884,"575_3": 0.889,
                "675_2": 0.885,"675_3": 0.890,
                "775_2": 0.886,"775_3": 0.891,
                "875_2": 0.888,"875_3": 0.890,
                "975_2": 0.887,"975_3": 0.890,
                "1075_2":0.884,"1075_3":0.896,}
    if "DiMuon" in sele:
        d = {"150_2": 0.984,"150_3": 0.984,
                "200_2": 0.985,"200_3": 0.984,
                "275_2": 0.985,"275_3": 0.984,
                "325_2": 0.986,"325_3": 0.986,
                "375_2": 0.986,"375_3": 0.985,
                "475_2": 0.986,"475_3": 0.986,
                "575_2": 0.986,"575_3": 0.986,
                "675_2": 0.987,"675_3": 0.986,
                "775_2": 0.986,"775_3": 0.986,
                "875_2": 0.987,"875_3": 0.986,
                "975_2": 0.987,"975_3": 0.988,
                "1075_2":0.987,"1075_3":0.987,}
    if "Had" in sele:
        d = {"200_2":0.818,  "200_3":0.789,
                "275_2":0.952,  "275_3":0.900,
                "325_2":0.978,  "325_3":0.959,
                "375_2":0.992,  "375_3":0.987,
                "475_2":0.998,  "475_3":0.996,
                "575_2":1.,     "575_3":1.,
                "675_2":1.,     "675_3":1.,
                "775_2":1.,     "775_3":1.,
                "875_2":1.,     "875_3":1.,
                "975_2":1.,     "975_3":1.,
                "1075_2":1.,    "1075_3":1.,}

    if "Photon" in sele:
        return 1

    # print "> Trig corr (%s): %.3f" % (ht+"_"+njet, d[ht+"_"+njet])

    return d[ht+"_"+njet]

def trig_eff_fine(sele = "OneMuon", ht = "", njet = ""):
    """ list trigger efficiencies for fine jet multiplicity """

    # if inclusive jet selection, use ge5j effs
    if njet == "all":
        njet = "4"

    if "OneMuon" in sele:
        d = {"150_1": 0.872,"150_2": 0.872,"150_3": 0.881,"150_4": 0.881,
                "200_1": 0.875,"200_2": 0.875,"200_3": 0.881,"200_4": 0.881,
                "275_1": 0.878,"275_2": 0.878,"275_3": 0.882,"275_4": 0.882,
                "325_1": 0.879,"325_2": 0.879,"325_3": 0.884,"325_4": 0.884,
                "375_1": 0.881,"375_2": 0.881,"375_3": 0.886,"375_4": 0.886,
                "475_1": 0.882,"475_2": 0.882,"475_3": 0.888,"475_4": 0.888,
                "575_1": 0.884,"575_2": 0.884,"575_3": 0.889,"575_4": 0.889,
                "675_1": 0.885,"675_2": 0.885,"675_3": 0.890,"675_4": 0.890,
                "775_1": 0.886,"775_2": 0.886,"775_3": 0.891,"775_4": 0.891,
                "875_1": 0.888,"875_2": 0.888,"875_3": 0.890,"875_4": 0.890,
                "975_1": 0.887,"975_2": 0.887,"975_3": 0.890,"975_4": 0.890,
                "1075_1":0.884,"1075_2":0.884,"1075_3":0.896,"1075_4":0.896,}
    if "DiMuon" in sele:
        d = {"150_1": 0.984, "150_2": 0.984, "150_3": 0.984, "150_4": 0.984,
                "200_1": 0.985, "200_2": 0.985, "200_3": 0.984, "200_4": 0.984,
                "275_1": 0.985, "275_2": 0.985, "275_3": 0.984, "275_4": 0.984,
                "325_1": 0.986, "325_2": 0.986, "325_3": 0.986, "325_4": 0.986,
                "375_1": 0.986, "375_2": 0.986, "375_3": 0.985, "375_4": 0.985,
                "475_1": 0.986, "475_2": 0.986, "475_3": 0.986, "475_4": 0.986,
                "575_1": 0.986, "575_2": 0.986, "575_3": 0.986, "575_4": 0.986,
                "675_1": 0.987, "675_2": 0.987, "675_3": 0.986, "675_4": 0.986,
                "775_1": 0.986, "775_2": 0.986, "775_3": 0.986, "775_4": 0.986,
                "875_1": 0.987, "875_2": 0.987, "875_3": 0.986, "875_4": 0.986,
                "975_1": 0.987, "975_2": 0.987, "975_3": 0.988, "975_4": 0.988,
                "1075_1":0.987, "1075_2":0.987, "1075_3":0.987, "1075_4":0.987,}
    if "Had" in sele:
        # note: these effs should be updated with new numbers from Adam
        d = {"200_1":0.84,"200_2":0.78, "200_3":0.72, "200_4":0.72, #200_4 is nan, so assume same as 200_3
                "275_1":0.95,"275_2":0.95, "275_3":0.92,"275_4":0.95,
                "325_1":0.99,"325_2":0.97, "325_3":0.97,"325_4":1.,
                "375_1":0.99,"375_2":0.99, "375_3":0.99,"375_4":0.97,
                "475_1":1.,  "475_2":1.,   "475_3":1.0, "475_4":1.0,
                "575_1":1.,  "575_2":1.,   "575_3":1.,  "575_4":1.,
                "675_1":1.,  "675_2":1.,   "675_3":1.,  "675_4":1.,
                "775_1":1.,  "775_2":1.,   "775_3":1.,  "775_4":1.,
                "875_1":1.,  "875_2":1.,   "875_3":1.,  "875_4":1.,
                "975_1":1.,  "975_2":1.,   "975_3":1.,  "975_4":1.,
                "1075_1":1., "1075_2":1.,  "1075_3":1., "1075_4":1.,}

    if "Photon" in sele:
        return 1

    # print "> Trig corr (%s): %.3f" % (ht+"_"+njet, d[ht+"_"+njet])

    return d[ht+"_"+njet]

def lumi(sele = "mu"):
    """get the luminosity in fb-1"""

    d = {
            "Had": 18.493,
            "OneMuon": 19.131,
            "DiMuon": 19.131,
            "Photon": 19.12
    }

    # print "> Lumi corr (%s): %.3f (*10.)" % (sele, d[sele])

    return d[sele]*10.

def sb_corr(samp = ""):
    """get the process sideband correction"""

    d = {
            "Zinv": .94,
            "WJets": .93,
            "DY": .94,
            "TTbar": 1.18,
            "DiBoson": 1.18,
            "SingleTop": 1.18
    }

    # print "> Sb corr (%s): %.2f" % (samp, d[samp])

    return d[samp] if samp in d.keys() else 1

def grab_plots(f_path = "", h_title = "", sele = "OneMuon", njet = "", btag = "", ht_bins = []):
    """main function to extract single plot from various cats"""

    if f_path:
        f = r.TFile.Open(f_path)
        f.Get._creates = True  # not quite sure what this does. but it stops root from leaking memory and keeps it's ram usage MUCH smaller
    else:
        return

    if not f or f.IsZombie():
        raise Exception("Cannot open file", f_path)

    h_total = None
    for d in get_dirs(htbins = ht_bins, sele = sele, btag = btag):
        if "fineJetMulti" in f_path:
            jet_string = jet_string_fine
            trig_eff = trig_eff_fine
        else:
            jet_string = jet_string_old
            trig_eff = trig_eff_old
        log.debug(f_path)
        log.debug("%s/%s_%s" % (d, h_title, jet_string(njet)))
        h_tmp = f.Get("%s/%s_%s" % (d, h_title, jet_string(njet)))
        if not h_tmp:
            raise Exception("Cannot get plot %s/%s_%s" % (d, h_title, jet_string(njet)) )
        h = h_tmp.Clone()
        if "Data" not in f_path:
            # apply ht bin trig effs
            h.Scale( trig_eff(sele = sele,
                            ht = d.split("_")[-2] if "1075" != d[-4:] else d.split("_")[-1],
                            njet = jet_string(njet)) )
            if "SMS" not in f_path.split("/")[-1]:
                h.Scale( sb_corr(f_path.split("/")[-1].split("_")[1].split(".")[0]) )
            h.Scale( lumi(sele) )
        if not h_total:
            h_total = h.Clone()
        else:
            h_total.Add(h)
    h_total_clone = deepcopy(h_total)
    f.Close()

    return h_total_clone

if __name__ == "__main__":
    print ">>> Running plot_grabber debugger."
    try:
        dave = grab_plots(f_path = "/Users/robina/Dropbox/AlphaT/Root_Files_28Nov_aT_0p53_v1/Muon_DY.root",
                            sele = "OneMuon", h_title = "AlphaT", njet = "le3j",
                            btag = "eq0b", ht_bins = ["475_575"])
    except:
        print "Balls up."
        raise
    else:
        print "Hoo mutha fuckin ray!"

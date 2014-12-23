"""
Make component plots into beamer pres
"""

import sys
import os
from shutil import copyfile
import time
import re
from itertools import product
import subprocess

template = "comp_template.tex"
new_tex_file = "comp_new.tex"
slides_file = "comp_slides.tex"
title = "Component slides"
subtitle = "So many slides"
date = time.strftime("%d/%m/%y")

# Var to plot components of
var = "ComMinBiasDPhi_acceptedJets"
# Directory holding plots
plot_dir = "/Users/robina/Dropbox/AlphaT/RA1_scripts/11Dec_aT_0p53_forRobin_v0/" #ge4j_eq0b_200_Inf/"
# Set njet/btag/HT bin
njet = "ge4j"
btag = "eq0b"
lo_ht = "200"
hi_ht = "Inf"
sel_bin = "%s %s %s %s" % (njet, btag, lo_ht, hi_ht)
incl_dir = sel_bin.replace(" ", "_")

# HT bins to plot - can do this intelligently by finding last occurance
# of _ in the above and then asking for whatever is either side of it
allHTbins = ["200_275", "275_325", "325_375", "375_475", "475_575",
             "575_675", "675_775", "775_875", "875_975", "975_1075", "1075"]

print hi_ht, lo_ht
s = 0; e = -2
for i, htbin in enumerate(allHTbins):
    if htbin.startswith(lo_ht):
        print htbin
        s = i
    if htbin.endswith(hi_ht):
        print htbin
        e = i

HTbins = allHTbins[s:e+1]
print HTbins

# Control regions to plot
ctrl_regions = ["OneMuon", "DiMuon"]

# Use template - change title, subtitle, include file
with open(template, "r") as t:
    with open(new_tex_file, "w") as f:
        substitute = {"@TITLE": title, "@SUBTITLE": subtitle,
                      "@FILE": slides_file, "@DATE": date}
        for line in t:
            for k in substitute:
                if k in line:
                    line = line.replace(k, substitute[k])
            f.write(line)


# Templates for various slides
one_plot_slide = \
r"""
\section{@SLIDE_TITLE}
\begin{frame}{@SLIDE_TITLE}
    %\vspace{-.3cm}
    \begin{center}
        \includegraphics[width=0.90\textwidth]{@PLOT}
    \end{center}
\end{frame}
"""

four_plot_slide = \
r"""
\section{@SLIDE_TITLE}
\begin{frame}{@SLIDE_TITLE}
    \vspace{-.3cm}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \begin{center}
            $Data_{control}$
            \\
            \includegraphics[width=0.85\textwidth]{@DATAC}
            \\
            $MC_{control}$
            \\
            \includegraphics[width=0.85\textwidth]{@MCC}
            \end{center}
        \end{column}

        \begin{column}{0.5\textwidth}
            \begin{center}
            $MC_{signal}$
            \\
            \includegraphics[width=0.85\textwidth]{@MCS}
            \\
            $MC_{ratio} = \frac{MC_{signal}}{MC_{control}}$
            \\
            \includegraphics[width=0.85\textwidth]{@MCR}
            \end{center}
        \end{column}
    \end{columns}
\end{frame}
"""

six_plot_slide = \
r"""
\section{@SLIDE_TITLE}
\begin{frame}{@SLIDE_TITLE}
    \vspace{-.3cm}
    \begin{columns}
        \begin{column}{0.33\textwidth}
            \begin{center}
            @PLOT1_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT1}
            \\
            @PLOT4_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT4}
            \end{center}
        \end{column}

        \begin{column}{0.33\textwidth}
            \begin{center}
            @PLOT2_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT2}
            \\
            @PLOT5_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT5}
            \end{center}
        \end{column}

        \begin{column}{0.33\textwidth}
            \begin{center}
            @PLOT3_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT3}
            \\
            @PLOT6_TITLE
            \\
            \includegraphics[width=1.1\textwidth]{@PLOT6}
            \end{center}
        \end{column}
    \end{columns}
\end{frame}
"""

# Now make the slides file
with open(slides_file, "w") as slides:
    # First add the inclusive HT plot
    slide = one_plot_slide.replace("@SLIDE_TITLE", "%s - %s" % (var.replace("_"," "), sel_bin))
    slide = slide.replace("@PLOT", "%s/%s/plot_%s_%s.pdf" % (plot_dir, incl_dir, var, incl_dir))
    slides.write(slide)

    # Next plot the data VS BG hists for each HT bin
    slide = six_plot_slide.replace("@SLIDE_TITLE", "%s - individual $H_{T}$ bins" % (var.replace("_"," ")))
    for i, ht in enumerate(HTbins[:6]):
        slide = slide.replace("@PLOT%d_TITLE" % (i+1), ht.replace("_", " - "))
        slide = slide.replace("@PLOT%d" % (i+1), "%s/%s_%s_%s/plot_%s_%s_%s_%s.pdf" % (plot_dir, njet, btag, ht, var, njet, btag, ht))
    slides.write(slide)
    if len(HTbins) > 6 and len(HTbins) <= 12:
        slide = six_plot_slide.replace("@SLIDE_TITLE", "%s - individual $H_{T}$ bins" % (var.replace("_"," ")))
        for i,ht in enumerate(HTbins[6:12]):
            slide = slide.replace("@PLOT%d_TITLE" % (i+1), ht.replace("_", " - "))
            slide = slide.replace("@PLOT%d" % (i+1), "%s/%s_%s_%s/plot_%s_%s_%s_%s.pdf" % (plot_dir, njet, btag, ht, var, njet, btag, ht))
        # Tidy up extra plotholders
        for j in range(i, 6):
            slide = slide.replace("@PLOT%d_TITLE" % (j+1), "")
            slide = slide.replace("@PLOT%d" % (j+1), "")
        slides.write(slide)


    # Now go through each HT bin and for each control region, plot data_control,
    # MC_signal/control, MC_ratio (& scaled data?)
    for ht, ctrl in product(HTbins, ctrl_regions):
        slide = four_plot_slide.replace("@SLIDE_TITLE", "%s %s %s %s" % (njet, btag, ctrl, ht.replace("_", " - ")))
        slide = slide.replace("@DATAC", "%s/%s_%s_%s/%s/data_control_%s_%s" % (plot_dir, njet, btag, ht, var, ctrl, ht))
        slide = slide.replace("@MCC", "%s/%s_%s_%s/%s/hist_mc_control_%s_%s" % (plot_dir, njet, btag, ht, var, ctrl, ht))
        slide = slide.replace("@MCS", "%s/%s_%s_%s/%s/hist_mc_signal_%s_%s" % (plot_dir, njet, btag, ht, var, ctrl, ht))
        slide = slide.replace("@MCR", "%s/%s_%s_%s/%s/mc_ratio_%s_%s" % (plot_dir, njet, btag, ht, var, ctrl, ht))
        slides.write(slide)

# Now make the pdf
# Use lualatex for custom font
subprocess.call(["lualatex", new_tex_file])


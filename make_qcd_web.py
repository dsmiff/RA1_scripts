"""Make QCD version fo prediction webpages from normal prediction webpages,
and edit the prediction pages to include links to +QCD plots

hacky hacky
"""

import os
import fnmatch
import fileinput
import re
import shutil


def make_qcd_html(html_name):
    """html_name is the original html file we want to copy & edit"""

    html_qcd_name = re.sub(r'\.html', '_QCD.html', html_name)

    # make copy of the original so we can edit the non-QCD html file
    html_backup_name = re.sub(r'\.html', '.htmlBK', html_name)
    print "backup copy:", html_backup_name
    shutil.copyfile(html_name, html_backup_name)

    print "Making", html_qcd_name
    with open(html_backup_name, "r") as f_old:
        with open(html_name, "w") as f:
            with open(html_qcd_name, "w") as f_qcd:

                for line in f_old:
                    f.write(line)
                    # If there's a png in the line, let's replace it with the QCD version
                    # which has the same filename but _QCD just before the png
                    # if re.search(r'\.png', line):
                    line = re.sub(r'\.png', r'_QCD.png', line)
                    # Need to change all the Prediction*.html filenames as well
                    # Need the ? to make * non-greedy
                    line = re.sub(r'(Prediction.*?)\.html', r'\1_QCD.html', line)

                    f_qcd.write(line)

                    # Add in a link to toggle QCD on/off to the original & QCD html file
                    if re.search(r'Toggle', line):
                        f_qcd.write('<br>\nQCD MC: <a href="{0}">    Without QCD MC </a><br>\n'.format(html_name))
                        f.write('<br>\nQCD MC: <a href="{0}">    With QCD MC </a><br>\n'.format(html_qcd_name))


if __name__ == "__main__":
    for html in os.listdir("."):
        if fnmatch.fnmatch(html, "Prediction*.html"):
            print html
            # make_qcd_html(html)

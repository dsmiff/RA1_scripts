#!/bin/bash -e

# Script that condor runs on worker node

VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
host=`hostname`
# some information for debugging
echo "I am running on $host"
echo "I got the following parameters: $@"
# source CMSSW env
. $VO_CMS_SW_DIR/cmsset_default.sh
# get CMSSW
scramv1 project CMSSW CMSSW_7_3_0
cd CMSSW_7_3_0/src/
eval `scramv1 runtime -sh`
cd ../..
ls
python shape_plots_condor.py $@

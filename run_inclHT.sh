#!/bin/bash

# Run all vars for all bins for inclusive HT for all variables
# Have to do it like this until the pyROOT script stops segfaulting grr
declare -a vars=("Number_Btags" "AlphaT" "LeadJetPt" "LeadJetEta"
                 "SecondJetPt" "SecondJetEta" "HT" "MHT" "MET_Corrected"
                 "MHTovMET" "ComMinBiasDPhi_acceptedJets" "EffectiveMass"
                 "Number_Good_verticies" "JetMultiplicity")
# declare -a jets=("le3j" "ge4j")  # for normal jet bins
declare -a jets=("eq2j" "eq3j" "eq4j" "ge5j") # for fine jet binning
declare -a btags=("eq0b" "eq1b")

for v in "${vars[@]}"
do
    for j in "${jets[@]}"
    do
        for b in "${btags[@]}"
        do
            echo $v
            python shape_plots_inclHT.py $v $j $b
        done
    done
done
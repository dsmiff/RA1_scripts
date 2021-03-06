#!/bin/bash

# Run all vars for all bins for exclusive HT for all variables
# Have to do it like this until the pyROOT script stops segfaulting grr
declare -a vars=("Number_Btags" "AlphaT" "LeadJetPt" "LeadJetEta"
                 "SecondJetPt" "SecondJetEta" "HT" "MHT" "MET_Corrected"
                 "MHTovMET" "ComMinBiasDPhi_acceptedJets" "EffectiveMass"
                 "Number_Good_verticies" "JetMultiplicity")
declare -a jets=("le3j" "ge4j")
declare -a btags=("eq0b" "eq1b")

for v in "${vars[@]}"
do
    for j in "${jets[@]}"
    do
        for b in "${btags[@]}"
        do
            echo $v
            python shape_plots_exclHT.py $v $j $b
        done
    done
done
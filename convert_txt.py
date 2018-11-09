from pyspecdata import *
import os
import sys

directory = "/Users/alecabeatonjr/gsyr/exp_data/test_equip"
file_name = "Hahn_echo"
F = open(directory+"/"+file_name+".txt", "r")

print F.readlines()
F.close()


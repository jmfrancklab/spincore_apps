#!/usr/bin/bash
b=`basename $1 .ipynb`
jupyter nbconvert --to python $b.ipynb
sed -i.bak 's/^\(# \)In\[.*/\1/' $b.py && rm $b.py.bak

#!/usr/bin/bash
echo "about to construct wrapper..."
swig -python -o ppg_lang_wrap.c ppg_lang.i
echo "wrapper constructed."
echo "about to compile module..."
gcc -shared -DMS_WIN64 -I$conda_headers -I$spincore -I$numpy -L$conda_libs -L$spincore ppg_lang.c ppg_lang_wrap.c -lpython27 -lmrispinapi64 -o _ppg_lang.pyd
echo "module compiled."
pycode=$(cat <<-END
from numpy import *
import ppg_lang
ppg_lang.load([
    ('marker','start',1),
    ('pulse',10.0,'ph1',r_[0,1,2,3]),
    ('delay',10.0),
    ('marker','cpmg_start',2),
    ('pulse',20.0,'ph2',r_[0,2]),
    ('delay',20.0),
    ('jumpto','cpmg_start'),
    ('jumpto','start')
    ])
END
)
python -c "$pycode"

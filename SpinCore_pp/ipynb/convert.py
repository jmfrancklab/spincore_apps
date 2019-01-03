from nbformat import v3, v4
import sys
import re

jupyter_magic_re = re.compile("^get_ipython\(\).magic\(u'(.*)'\)")
jupyter_cellmagic_re = re.compile("^get_ipython\(\).run_cell_magic\(u'(.*)'\)")

assert sys.argv[1].endswith('.py'),"this is supposed to be called with a .py file argument!"
with open(sys.argv[1]) as fpin:
    text = fpin.read().decode('utf8')

text = text.split('\n')
text = [j for j in text if j[:5] != '# In[']
newtext = []
last_had_hash = False
last_had_code = False
for thisline in text:
    if thisline.startswith('# coding: utf-8'):
        pass
    elif thisline.startswith('# In['):
        pass
    elif thisline.startswith('# Out['):
        pass
    elif thisline.startswith('# '):
        if not last_had_hash:
            newtext.append('# <markdowncell>')
        newtext.append(thisline)
        last_had_hash = True
        last_had_code = False
    else:
        if not last_had_code:
            newtext.append('# <codecell>')
        m = jupyter_magic_re.match(thisline)
        if m:
            thisline = '%'+m.groups()[0]
        else:
            m = jupyter_cellmagic_re.match(thisline)
            if m:
                thisline = '%%'+m.groups()[0]
        newtext.append(thisline)
        last_had_hash = False
        last_had_code = True
text = '\n'.join(newtext)

text += """
# <markdowncell>
# If you can read this, reads_py() is no longer broken! 

"""

nbook = v3.reads_py(text)

nbook = v4.upgrade(nbook)  # Upgrade v3 to v4
nbook.metadata.update({'kernelspec':{'name':"Python [Anaconda2]",
    'display_name':'Python [Anaconda2]',
    'language':'python'}})

jsonform = v4.writes(nbook) + "\n"
with open(sys.argv[1].replace('.py','.ipynb'), "w") as fpout:
    fpout.write(jsonform.encode('utf8'))


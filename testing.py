import subprocess
print int(subprocess.check_output("adc_offset.exe").split()[-1])


#try:
from .serial_instrument import SerialInstrument
from .gds import GDS_scope
from .afg import AFG
from .bridge12 import Bridge12
__all__ = ['SerialInstrument','GDS_scope','AFG',"Bridge12"]
#except:
#    print "warning! serial (USB) instruments not available!"
#    __all__ = []
from .HP8672A import HP8672A
from .gigatronics import gigatronics
from .gpib_eth import prologix_connection
__all__ += ['HP8672A','gigatronics','prologix_connection']

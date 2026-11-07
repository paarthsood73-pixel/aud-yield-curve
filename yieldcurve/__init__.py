"""Bootstrap an AUD zero curve from deposits, FRAs and par swap rates."""
from .bootstrap import bootstrap, load_instruments
from .curve import ZeroCurve
from .instruments import FRA, Deposit, Swap

__all__ = ["bootstrap", "load_instruments", "ZeroCurve", "Deposit", "FRA", "Swap"]
__version__ = "0.1.0"

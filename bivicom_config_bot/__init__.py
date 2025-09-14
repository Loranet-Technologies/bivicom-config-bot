"""
Bivicom Configuration Bot

A comprehensive network automation toolkit for configuring and deploying 
infrastructure on Bivicom IoT devices.

This package combines device discovery, SSH automation, UCI network configuration, 
and infrastructure deployment into a unified workflow.
"""

__version__ = "1.0.2"
__author__ = "Loranet Technologies"
__email__ = "info@loranet.com"
__description__ = "A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices"

# Import main modules
from . import master
from . import gui_enhanced

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "master",
    "gui_enhanced",
]

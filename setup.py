#!/usr/bin/env python3
"""
Setup script for Bivicom Configuration Bot
A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bivicom-config-bot",
    version="1.0.2",
    author="Loranet Technologies",
    author_email="info@loranet.com",
    description="A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Loranet-Technologies/bivicom-config-bot",
    project_urls={
        "Bug Reports": "https://github.com/Loranet-Technologies/bivicom-config-bot/issues",
        "Source": "https://github.com/Loranet-Technologies/bivicom-config-bot",
        "Documentation": "https://github.com/Loranet-Technologies/bivicom-config-bot#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "gui": ["plyer>=2.0.0"],
        "build": ["pyinstaller>=4.0"],
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "bivicom-bot=bivicom_config_bot.master:main",
            "bivicom-gui=bivicom_config_bot.gui_enhanced:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sh", "*.md", "*.json", "*.txt", "*.env.example"],
    },
    keywords=[
        "bivicom", "iot", "automation", "network", "configuration", 
        "ssh", "docker", "nodered", "tailscale", "openwrt", "uci"
    ],
    zip_safe=False,
)

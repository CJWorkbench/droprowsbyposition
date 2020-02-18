#!/usr/bin/env python

from setuptools import setup

setup(
    name="droprowsbyposition",
    version="0.0.2",
    description="Drop specified rows",
    author="Adam Hooper",
    author_email="adam@adamhooper.com",
    url="https://github.com/CJWorkbench/droprowsbyposition",
    packages=[""],
    py_modules=["droprowsbyposition"],
    install_requires=["pandas==0.25.0", "cjwmodule>=1.4.0"],
)

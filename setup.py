#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoadTest-Pilot Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="loadtest-pilot",
    version="1.0.0",
    author="LoadTest-Pilot Team",
    author_email="",
    description="🚀 Lightweight API Performance & Load Testing Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/LoadTest-Pilot",
    py_modules=["loadtest_pilot"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "loadtest-pilot=loadtest_pilot:main",
        ],
    },
    keywords="api testing load testing performance benchmark http cli",
    project_urls={
        "Bug Reports": "https://github.com/gitstq/LoadTest-Pilot/issues",
        "Source": "https://github.com/gitstq/LoadTest-Pilot",
    },
)

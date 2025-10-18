#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bonnet",
    version="1.0.0",
    author="Blake Smith",
    author_email="blakeinvictoria@gmail.com",
    description="A CLI tool for managing structured knowledge base (memory) and preparing highly compressed XML context",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
        "python-dateutil>=2.8.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bonnet=bonnet.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

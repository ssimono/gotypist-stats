#! /usr/bin/env python3
from setuptools import setup

setup(
    name="gotypist-stats",
    version="1.1.0",
    python_requires=">=3.6",
    packages=["gotypist_stats"],
    entry_points={"console_scripts": ["gotypist-stats = gotypist_stats.__main__:main"]},
    install_requires=["tabulate"],
    extras_require={"dev": ["mypy", "pyflakes", "black"]},
    license="MIT",
    author="Simon Alfassa",
    author_email="simon@sa-web.fr",
    description="Get high-level metrics from your gotypist training sessions",
    long_description=open("./README.md").read(),
    long_description_content_type="text/markdown",
    keywords="gotypist typing statistics",
    url="https://github.com/ssimono/gotypist-stats",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Topic :: Education",
    ],
)

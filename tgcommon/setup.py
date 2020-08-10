
from setuptools import setup

setuptools.setup(
    name="tgcommon-oranges",
    version="0.0.3",
    author="oranges",
    author_email="email@oranges.net.nz",
    description="Common code for the tg cogs",
    long_description="Common code for the tg cogs connecting to a tg ss13 database",
    long_description_content_type="text", #text/markdown later
    url="https://github.com/optimumtact/orangescogs",
    packages=['tgcommon'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

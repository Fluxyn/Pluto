# Pluto
#### v0.0.1 beta
Pluto is a small, new programming language written 100% in Python 3. I made this language partly for fun but also to add another small and easy-to-learn programming language out there. My goal is to eventually implement complex functions and have many libraries and APIs for Pluto.

## Installation
Currently, the only way to install Pluto is to download the files from GitHub and use `python install /location/of/pluto/download` to install it onto your system.
In the future, I may make an application (maybe an IDE to go with it) for Windows and MacOS.

## Usage
You can use Pluto in the command line to run your files:
```console
foo:~$ pluto /location/of/pluto-file.plu
```

See [the wiki](https://github.com/lukarao/Pluto/wiki) for more detailed documentation on the language and command line usage.

## Compatibility
Pluto has been tested on Windows 10 (Pluto might not work on older or newer versions of Windows). I am currently working on Pluto compatibility for MacOS. 

## Dependencies
The Pluto compiler is made using Python and built-in Python packages/modules (json, re, sys, time, subprocess, os, contextlib, itertools, ast and distutils), so all you need is a Python interpreter. 

You also need a C complier to execute the generated C code. If you don't have a C complier, I suggest using the option `--show_c` to get the C code and running it with an online C compiler such as [OnlineGDB](https://www.onlinegdb.com/) or [Ideone](https://ideone.com/).

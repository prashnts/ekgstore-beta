.. EKG Store documentation master file, created by
   sphinx-quickstart on Fri Jul 29 14:27:56 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EKG Store's documentation!
=====================================

EKGStore is a command-line utility and Python library to extract the waveforms
and metadata from the PDF files generated from ECG machines.

This is achieved by converting the ``PDF`` files to a more robust ``SVG`` format
which can be handled at a much greater ease, and then applying heuristics
derived from model files.

A very brief overview of architecture is as follows:

- Convert PDF to SVG using Inkscape.
- Parse the SVG to obtain labeled waveforms and calibaration markers.
- Normalise the waveforms with reference to the calibaration markers.
- Extract and parse the metadata.
- Generate ``csv`` and ``json``.


Command-line Usage
------------------

After installing the tool, it will be available throughout the system and can
be invoked by executing ``ekgstore`` in a terminal.

As default behaviour, this tool will find all the files in current directory
and all subdirectories and write output to directory called ``output``.

More advanced behaviour is supported by supplying ``-i`` (or ``--input``) and
``-o`` (or ``--output``) options. Check out the examples below for typical
cases

1. Process all files in current and all children directories. Write
   all output in "output" directory ::
    $ ekgstore

2. Process files in directories "foo" and "bar" only ::

    $ ekgstore -i foo -i bar

3. Process a single file::

    $ ekgstore -i path/to/file.pdf

4. Process all files like "anna_1.pdf", "anna_2.pdf" etc. in any directory::

    $ ekgstore -i '**/anna_*.pdf'

5. Specify output directory::

    $ ekgstore -o path/to/directory

These can be referred at any time by supplying ``-h`` or ``--help`` options.


Using as a Python library
-------------------------

Check out the ``api`` below for advance usage information.


.. toctree::
   :maxdepth: 1

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


###############Folders description##################

-Installation
PaPo (that's how we call the extractor) Package and dependencies
        -Source
Source code for the Package without my test suite, which will be delivered with the current git repository to the next maintainer.
        -Bins
Script to extract data from docx file and generate xml file.
        
################INSTALLATION#################

Start installing python 2.7 if you do not have it, it can also be downloaded from https://www.python.org/download/

Install setuptools module (ez_setup) by double clicking it, it can also be downloaded from https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py

Install papofeed

One of the dependencies are still not automatically downloaded, so you will need to install it:
open a command line.
        go to your python 2.7 folder, usually at c:\python27
        in the scprips folder run 'easy_install.exe lxml'
        

################Usage##################
in the bin folder, run just double click docx2xml, make sure there is a docx file in the folder named questionnaire (this is the document to be parsed).


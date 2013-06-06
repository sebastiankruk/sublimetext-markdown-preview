#!/usr/bin/python
# -*- coding: utf-8 -*-

#extensions.py

import re
import sys, getopt

CAPTURE_IMAGE=re.compile(r"""<p>                                            # initial p
                             <img\s+ 
                                  src="(?P<img_src>[^"]+)"\s+               # src 
                                  alt="(?P<img_alt>[^"]+)"\s+               # we will fiddle with ALT a little
                                  title="[^"]+"\s*                          # the actual title we will replace - so we don't capture it
                                   />\s*
                                   <div[^>]*>\s*
                                   (?:<p[^>]*>
                                         Figure\s+(?P<fig_number>\d+)[.]    # we need to know the number of this figure
                                   (?:\s+(?P<img_id>[$]fig\d+):)?\s*        # extracting figure ID if present
                                      (?P<fig_title>.+)</p>)?""", re.X)     # we need to know the title


CAPTURE_IMAGE_ID=re.compile(r"""<p[^>]*>
                                  Figure\s+\d+[.]                           # Figure 1
                                (?:\s+(?P<img_id>[$]fig\d+):)?\s*           # extracting figure ID if present
                                .+</p>""", re.X)                            # "title"


CAPTURE_ANY_IMAGE_ID=re.compile(r"""(?P<img_id>[$]fig\d+)""", re.X)         # this should capture occurrences of any Image IDs

CAPTURE_REF_IMAGE_ID=re.compile(r"""(?P<ref_label>[Ff]igure)\s+             # capturing to ensure proper case of Figure/figure
                                    (?P<img_id>[$]fig\d+)""", re.X)         # this should capture proper references of any Image IDs



CAPTURE_EMPTY_HREFS=re.compile(r"""<a\s+href=["][$]["]>""", re.X)                 # we will replace those with alert()

class MarkdownExtensions(object):
    """
    Class that wraps markdown extensions processing
    """
    def __init__(self):
        self.__figure_ids=dict()

    def process(self, text):
        """
        Call this method to do the actual processing
        """
        self.__figure_ids=dict()

        self._extract_figure_ids(text) # we just extract information don't care about 

        t_output = CAPTURE_IMAGE.sub(self._process_match, text)
        t_output = CAPTURE_REF_IMAGE_ID.sub(self._fix_figure_references, t_output)
        t_output = CAPTURE_ANY_IMAGE_ID.sub(self._fix_any_figure_references, t_output)
        t_output = CAPTURE_EMPTY_HREFS.sub(self._fix_empty_hrefs, t_output)

        return t_output

    def debug(self):
        return self.__figure_ids

    def _process_match(self, m):
        """
        Cleans up the IMG+Figure tags in the article
        """
        groupdict = m.groupdict()
        groupdict['img_alt'] = ' '.join(groupdict['img_alt'].split('-'))

        img_template = """<p id="figure_%(fig_number)s"><img src="%(img_src)s" title="%(fig_title)s" alt="%(img_alt)s" /></p>"""
        fig_template = """<div class="wp-caption aligncenter"><p class="wp-caption-text"><p>Figure %(fig_number)s. %(fig_title)s&nbsp;<a href="javascript:history.back()">&#x21A9;</a></p>"""

        if 'img_id' in groupdict and groupdict['img_id'] in self.__figure_ids:
            template = img_template + fig_template
            groupdict['fig_number'] = self.__figure_ids[groupdict['img_id']]
            print "Processing img number %s" % groupdict['fig_number']
        else:
            template = img_template
            groupdict['fig_title'] = groupdict['img_alt']
            groupdict['fig_number'] = "0"
            print "Processing img alt <%s>" % groupdict['img_alt'] 

        return template % groupdict


    def _extract_figure_ids(self, t_input):
        """
        Records all figure IDs
        """
        last_figure_id = 1

        for id in CAPTURE_IMAGE_ID.findall(t_input):
            if not id in self.__figure_ids:
                self.__figure_ids[id] = str(last_figure_id)
                last_figure_id += 1

        print "Found following figure IDs: ", self.__figure_ids

        # find all IDsed - to check if did not reference something non-existing

        for figid in set(CAPTURE_ANY_IMAGE_ID.findall(t_input)):
            if not figid in self.__figure_ids:
                print "!!!\nWARNING: Referencing undefined figure ID = %s\n!!!" % figid


    def _fix_figure_references(self, m):
        """
        Replaces all existing references to figure IDs with their numbers
        """
        ref_template = """<a href="#figure_%(figure_number)s">%(ref_label)s %(figure_number)s</a>"""

        groupdict = m.groupdict()

        if "img_id" in groupdict and groupdict["img_id"] in self.__figure_ids:
            groupdict["figure_number"] = self.__figure_ids[groupdict["img_id"]]

            print "Made reference to figure %(figure_number)s clickable" % groupdict

            return ref_template % groupdict

        return m.group()

    def _fix_any_figure_references(self, m):
        """
        Replaces all existing references to figure IDs with their numbers (but without "Figure" before)
        """
        groupdict = m.groupdict()

        if "img_id" in groupdict and groupdict["img_id"] in self.__figure_ids:
            return self.__figure_ids[groupdict["img_id"]]

        return m.group()



    def _fix_empty_hrefs(self, m):
        """
        Replaces empty references with javascript:alert('That post is coming soon') 
        """
        print "Found empty reference"
        return "<a href=\"javascript:alert('That post is coming soon')\">"


def convert(input_file, output_file):
    """
    The actual converter
    """
    print "Opening file %s" % input_file

    f_input = open(input_file, "r")
    t_input = f_input.read()
    f_input.close()

    ext = MarkdownExtensions()

    t_output = ext.process(t_input)

    f_output = open(output_file, "w+")
    f_output.write(t_output)
    f_output.close()

    print "Saved to file %s" % output_file



def help(state=0):
    """
    To know how to call this script
    """
    print 'fix-post.py -i <inputfile> -o <outputfile>'
    sys.exit(state)

def clean_path(path):
    """
    Converts Cygwin paths to windows paths
    """
    if path.startswith('/cygdrive/'):
        apath = path.split("/")
        apath = [apath[2] + ":"] + apath[3:]
        path = "\\".join(apath)

    return path

def main(argv):
    """
    Main class
    """
    input_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv,"i:o:",["input=","output="])
    except getopt.GetoptError:
        help(2)


    for opt, arg in opts:
        if opt == '-h':
            help()
        elif opt in ("-i", "--input"):
            input_file = clean_path(arg)
        elif opt in ("-o", "--output"):
            output_file = clean_path(arg)

    if input_file and output_file:
        convert(input_file, output_file)
    else:
        help(1)


if __name__ == "__main__":
   main(sys.argv[1:])
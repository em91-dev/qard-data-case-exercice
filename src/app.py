#!/bin/env python

import os
import re
import string
import json
import pandas as pd
import pyspark
import pytesseract
import pdf2image
import spacy

import time
from pyspark.sql import SparkSession
from pyspark import SparkContext

DATA_SITE = "https://github.com/ierpDesbieres/qard-data-case/tree/main/data"

DATA_DIR = "/qard-data-case/data" # Input data
PRENOMS_DB = "/db/Prenoms.csv" # Input database with first names
OUT_DIR = "/out" # Top, directory of the generated files
OUT_OCR_SUBDIR = "ocr" # Cache directory of the text files
OUT_RESULT_JSON = "result.json" # Final result

def normalize_name(name):
    """ Transform names in a "normalized" format
    """
    accdic = {"à": "a", "ä": "a",
              "é": "e", "è": "e", "ë": "e",
              "î": "i", "ï": "i",
              "ô": "o", "ö": "o",
              "û": "u", "ü": "u"}
    return name.lower().translate(accdic)

def get_text(file):
    """ Extract text from pdf using tesseract
    """
    f = os.path.join(DATA_DIR, file)
    text = ''
    pages = pdf2image.convert_from_path(f)
    for page in pages:
        text += '\n' + pytesseract.image_to_string(page)
    return text

def extract_names_with_regex(text):
    """ Extract names from text using regular expressions
    """
    lowacc = "àäéèëîïôöùûü"
    uppacc = lowacc.upper()
    prefix = '[M][A-Za-z\.]+\s+'
    firstname = '[A-Z][A-Za-z{}\-]*'.format(lowacc, lowacc)
    lastname = '[A-Z][A-Za-z{}{}\-]+'.format(lowacc, uppacc)
    fullname = '({})?{}[ ]+{}'.format(prefix, firstname, lastname)
    l = re.findall(r'({})'.format(fullname), text, re.MULTILINE)
    names = set()
    for x in l:
        name = x[0]
        if x[1] != "":
            name = name.replace(x[1], "", 1).replace("\n", "")
        names.add(name)
    return sorted(list(names))

def extract_names_with_prenoms_list(text):
    """ Extract names from text using first names referenced in a database
           https://www.data.gouv.fr/fr/datasets/liste-de-prenoms/
           https://www.data.gouv.fr/fr/datasets/r/55cd803a-998d-4a5c-9741-4cd0ee0a7699
    """
    df = pd.read_csv(PRENOMS_DB, sep=";", encoding="ISO-8859-1")
    prenoms = set(df["01_prenom"].to_list())
    stopprenoms = set(["la", "le", "les", "elle", "sera"])
    prenoms = prenoms - stopprenoms
    l = re.sub(r'\s+', ' ', (text.replace('\n', ' '))).split()
    names = set()
    for a, b in zip(l[:-1], l[1:]):
        if a[0].isupper() and b[0].isupper():
            if a.lower() in prenoms:
                b2 = b.translate(str.maketrans('', '', string.punctuation))
                names.add(a + " " + b2)
    return sorted(list(names))

def extract_names_with_spacy(text):
    """ Extract names from text using Spacy tagger
    """
    nlp = spacy.load("fr_core_news_md")
    names = set()
    titres = ["madame", "mademoiselle", "monsieur",
              "mesdames", "mesdemoiselles", "messieurs",
              "mm", "mr", "mrs"]
    for line in text.split('\n'):
        doc = nlp(line)
        for ent in doc.ents:
            if ent.label_ == 'PER':
                name = ent.text
                if 1 <= name.count(' ') <= 2:
                    namesplit = name.split(' ')
                    if namesplit[-1][0].isupper():
                        if namesplit[0].lower() in titres:
                            name = " ".join(namesplit[1:])
                        names.add(name)
    return sorted(list(names))

def extract_names_from_text(text):
    """ Extract names from text using a combination of all methods
    """
    methods = [extract_names_with_regex,
               extract_names_with_prenoms_list,
               extract_names_with_spacy]
    normnames = dict()
    rawnames = set()
    for method in methods:
        names = method(text)
        rawnames = rawnames.union(names)
        for n in set([normalize_name(n) for n in names]):
            normnames[n] = normnames[n] + 1 if n in normnames else 1
    names = []
    for name in rawnames:
        if normnames[normalize_name(name)] > 1:
            names.append(name)
    return names

def get_text_from_cache(pdfile):
    """ Make the OCR transformation from pdf to a text, or return
        the text from the cache directory if it exists already
    """
    b = os.path.basename(pdfile).replace(".pdf", ".text")
    cached = os.path.join(OUT_DIR, OUT_OCR_SUBDIR)
    if not os.path.exists(cached):
        os.makedirs(cached)
    cachef = os.path.join(cached, b)
    print(cachef)
    if not os.path.isfile(cachef):
        text = get_text(os.path.join(DATA_DIR, os.path.basename(pdfile)))
        open(cachef, "w").write(text)
    return open(cachef, "r").read()

def extract_names_from_pdf(pdfile):
    """ Extract the names from a pdf file
    """
    text = get_text_from_cache(pdfile)
    return extract_names_from_text(text)

def run_spark_job(files):
    """ Execution of the task through Spark
    """
    SparkContext.getOrCreate()
    spark = SparkSession \
                .builder \
                .master("local") \
                .appName("Detection of names") \
                .getOrCreate()
    sc = SparkContext.getOrCreate()
    rdd = sc.parallelize(files).map(lambda f: (f, extract_names_from_pdf(f)))
    out = rdd.collect()
    spark.stop()
    #sc.stop()
    return out

def save_result_as_json(out):
    """ Save and return the result in JSON nformat and return it
    """
    dictionary = {"site": DATA_SITE, "files": [] }
    for f, n in out:
        dictionary["files"].append({"path": f, "names": n})
    jsonf = os.path.join(OUT_DIR, OUT_RESULT_JSON)
    with open(jsonf, "w") as jf:
        json.dump(dictionary, jf, indent=4)
    return json.load(open(jsonf, "r"))

if __name__ == "__main__":
    #print(extract_names_from_text(get_text_from_cache("1.pdf")))
    files = os.listdir(DATA_DIR)
    out = run_spark_job(files)
    res = save_result_as_json(out)
    print(res)



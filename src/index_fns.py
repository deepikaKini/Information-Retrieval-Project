###########################################################################
#
# index_fns.py
# - routines to read files and generate index data
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:01:34
###########################################################################


from progress.bar import Bar
import string
import os
import math

from debug_fns import *


################################################################
# Collecting data from a CACM abstract file:
# terms, postings, doc term freq., doc attributes, etc.
################################################################
def scan_CACM_abstract(docDir, docEntry, vocab, postings, docIndex):
    (fileName, docId) = docEntry
    # RZ: For CACM, have to change encoding to latin-1 from default UTF-8
    nextFile = open(docDir + "/" + fileName, "r", encoding="latin-1")

    # Initialization
    docFreq = dict()
    termPositions = dict()
    position = 0
    title = ""
    titleFinished = False

    # Get term counts and positions
    for line in nextFile:
        # Strip whitespace from beginning/end of the line.
        line = line.strip()

        # Grab title lines (with capitalization intact)
        # NOTE: does *not* advance to next line of the file
        if not titleFinished and not line in {
            "",
            "<pre>",
            "<html>",
            "</pre>",
            "</html>",
        }:
            # Add a space for multi-line titles
            if title != "":
                title += " "
            title += line

        elif line == "" and title != "":
            titleFinished = True

        # Ignore blank lines and formatting tags from CACM collection.
        # NOTE: Indexes titles along with body text
        if not line in {"", "<pre>", "<html>", "</pre>", "</html>"}:
            # Casefold (convert to lower case), and replace punctuation by spaces
            line = line.lower().translate(
                str.maketrans(string.punctuation, " " * len(string.punctuation))
            )

            for term in line.split():
                if term in docFreq.keys():
                    docFreq[term] += 1
                    termPositions[term].append(position)
                else:
                    docFreq[term] = 1
                    termPositions[term] = [position]

                position += 1

    # Add postings to the index.
    Wd_sum = 0
    for term in docFreq:
        # Update vocabulary doc frequency count
        if term in vocab.keys():
            vocab[term] = vocab[term] + 1
        else:
            vocab[term] = 1

        # Update postings
        next_post = [docId, docFreq[term]]
        next_post.append(termPositions[term])

        if term in postings.keys():
            postings[term].append(next_post)
        else:
            postings[term] = [next_post]

        # Doc weight: using Zobel & Moffat page 5 document term weight as-written
        Wd_sum += 1 + math.log(docFreq[term])

    # Record document index entry
    docIndex[docId] = [fileName, title, math.sqrt(Wd_sum)]

    nextFile.close()


################################################################
# Generate index for all CACM abstracts
################################################################
def index_collection(docDir, config):
    # Vocab, postings, and document index represented using dictionaries
    vocab = dict()
    postings = dict()
    docIndex = dict()

    # Generate list of document names and integer identifiers (starting from 1)
    docNames = sorted(os.listdir(docDir))
    docPairs = zip(docNames, range(1, len(docNames) + 1))

    # Indexing: show a simple progress bar while indexing documents.
    bar = Bar("Indexing " + docDir + ":", max=len(docNames))
    for docEntry in docPairs:
        scan_CACM_abstract(docDir, docEntry, vocab, postings, docIndex)
        bar.next()
    bar.finish()

    config["terms"] = len(vocab.keys())
    config["docs"] = len(docNames)

    return (vocab, postings, docIndex)


################################################################
# Generate skips from postings
################################################################
def generate_skip_lists(postings, sublist_size):
    # Note: Postings have variable length because of position data
    # Generating as 'raw' list of integers
    skipDict = dict()

    for term in postings:
        skipDict[term] = []

        # Read postings (which varying length) and write posts at appropriate locations
        # (i.e., every sublist_size entries)
        # DEBUG: Offset is relative to the beginning of the list
        offset = 2 + postings[term][0][1]
        for i in range(1, len(postings[term])):
            if i % sublist_size == 0:
                # Store document id, and location of next offset
                skipDict[term].extend([postings[term][i - 1][0], offset])

            # Add docId, frequency, and position entries to offset
            offset += 2 + postings[term][i][1]

    return skipDict


################################################################
# Generate:
# * raw postings file data (as a single integer list)
# * raw vocab file with integer offsets and doc freq per term
#   (supports using raw postings for retrieval)
#
# NOTE: Skip lists inserted at front of postings if passed
################################################################
def raw_vocab_postings(vocab, postings, config, skips=None):
    # Compute raw postings and offsets for each vocab term
    rawPostings = []
    rawVocab = dict()

    start_offset = 0
    for term in sorted(postings.keys()):
        rawVocab[term] = (start_offset, vocab[term])

        if skips:
            rawPostings.extend(skips[term])
            start_offset += len(skips[term])

        for docId, docFreq, positions in postings[term]:
            rawPostings.extend([docId, docFreq])
            rawPostings.extend(positions)
            start_offset += 2 + len(positions)

    config["postings"] = len(rawPostings)

    return (rawVocab, rawPostings)

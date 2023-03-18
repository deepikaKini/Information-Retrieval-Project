###########################################################################
#
# io_fns.py
#   - Serialization and output messages
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:04:35
###########################################################################

import json
import os
import heapq
from debug_fns import *


################################################################
# Output Messages
################################################################
def print_index_files(outdir, vocabFile, postingsFile, docIndexFile, configFile):
    print("[ Index dir: " + outdir + " ]")
    print("        Vocab file: " + vocabFile)
    print("     Postings file: " + postingsFile)
    print("    Doc Index file: " + docIndexFile)
    print("    Config + stats: " + configFile)


def showCollectionInfo(indexDir, configDict):
    print("[ Searching Index Directory: ", indexDir, " ]")
    for item in configDict:
        print("  ", item, ":", configDict[item])
    print("")


def announce_query(config, query, valid_query, skipped):
    # Create banner to make queries easier to spot at the terminal
    print("\n>>--------------------------------------------")
    print("  Searching", config["indexDir"])
    if len(skipped) > 0:
        print("  OUT-OF-VOCABULARY:", *skipped)
        print("  REVISED Query:\n   ", *valid_query)
    else:
        print("  Query:\n   ", *valid_query)
    print(">>--------------------------------------------\n")

    if config["debug"]:
        showCollectionInfo(config["indexDir"], config)


def showResults(heap, k, docIndex, skipped, config):
    print("[ Results ]\n    Matching Documents:", len(heap))

    print("    Total reads:", config["posts_read"] + config["skips_read"])
    print("      * Postings read:", config["posts_read"])
    print("      * Skip pointers read:", config["skips_read"])
    if len(skipped) > 0:
        print("    *OUT-OF-VOCABULARY:", *skipped)

    print("\n--------------------------------------------")
    print(" Top-" + str(k) + " documents (", len(heap), "matches", ")")
    print("--------------------------------------------\n")

    topk_hits = heapq.nlargest(k, heap)
    i = 1
    for score, docId in topk_hits:
        (file_name, title, Wd) = docIndex[docId]
        print(str(i) + ". " + "{:.2f}".format(score) + " " + file_name + "\n  " + title)
        i += 1

    if len(topk_hits) < 1:
        print("  ** No matching documents found.")


################################################################
# JSON Serialization (easy dict/list save/load)
################################################################
def write_json(obj, out_dir, file_name):
    json.dump(
        obj, open(os.path.join(out_dir, file_name + ".json"), "wt"), sort_keys=True
    )


def read_json(in_dir, file, int_keys=False):
    jdata = json.load(open(os.path.join(in_dir, file + ".json"), "rt"))
    if not int_keys:
        return jdata
    else:
        return {int(k): v for (k, v) in jdata.items()}


################################################################
# Write Index Data
################################################################
def write_index(config, outDir, rawVocab, rawPostings, docIndex):
    # Write out final index files in JSON
    config_file = "CONFIG_STATS"
    write_json(rawVocab, outDir, config["vocabFile"])
    write_json(rawPostings, outDir, config["postingsFile"])
    write_json(docIndex, outDir, config["docIndexFile"])
    write_json(config, outDir, config_file)

    # Message at terminal
    print_index_files(
        outDir,
        config["vocabFile"],
        config["postingsFile"],
        config["docIndexFile"],
        config_file,
    )

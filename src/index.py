###########################################################################
#
# index.py
#   - Main program for indexing CACM abstracts
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:11:46
###########################################################################

# Includes for this tool, start timer
from debug_fns import *
import debug_fns

dTimer = DebugTimer("Indexing")  # START timer
from io_fns import *
from index_fns import *
from compression_fns import *

# Python library includes
import os
import argparse

dTimer.qcheck("Python module load")


################################################################
# Main program
################################################################
def main():
    # Command line argument handling.
    # Use formatter to show default parameter values with --help
    # NOTE: ArgumentParser creates variables based on the '--X' name
    argParser = argparse.ArgumentParser(
        description="Simple text indexer: index collection in one directory & write index data to another directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argParser.add_argument("indir", type=str, help="input dir for collection")
    argParser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show debug messages & write index debug data",
    )
    argParser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default="./index-data",
        help="output dir for index files",
    )
    argParser.add_argument(
        "-s",
        "--skipsize",
        type=int,
        default=1,
        help="skip size; use 1 for no skip list",
    )
    argParser.add_argument(
        "-c", "--delta", action="store_true", help="apply delta compression"
    )

    args = argParser.parse_args()

    ##################################
    # Configuration
    ##################################
    # Set debug flag (for debugging output)
    debug_fns.DEBUG = args.debug

    # In / out directories and index configuration
    docDir = args.indir
    outDir = args.outdir
    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)

    skipSize = args.skipsize
    apply_deltac = args.delta

    config = {
        "delta": args.delta,
        "skip_size": args.skipsize,
        "docDir": args.indir,
        "indexDir": outDir,
        "vocabFile": "vocabulary",
        "postingsFile": "postings",
        "docIndexFile": "doc_index",
    }

    ##################################
    # Indexing
    ##################################

    # Create initial index with explicit dictionaries and lists
    (vocab, postings, docIndex) = index_collection(docDir, config)
    dTimer.qcheck("Index construction")

    # Create skip lists if requested.
    skipDict = None
    if skipSize > 1:
        (skipDict) = generate_skip_lists(postings, sublist_size=skipSize)
        dTimer.qcheck("Skip list construction")

    # Apply delta compression if requested.
    out_postings = postings
    if apply_deltac:
        out_postings = delta_compress(postings)
        dTimer.qcheck("Delta compression applied")

    # Convert postings to integer list
    rawVocab = None
    rawPostings = None
    if skipSize > 1:
        # If using skips, prepend skip lists to each posting list
        (rawVocab, rawPostings) = raw_vocab_postings(
            vocab, out_postings, config, skipDict
        )
    else:
        (rawVocab, rawPostings) = raw_vocab_postings(vocab, out_postings, config)
    dTimer.qcheck("Conversion to raw integer list")

    # Write out final index files (in JSON)
    write_index(config, outDir, rawVocab, rawPostings, docIndex)
    dTimer.qcheck("Index files written to disk")

    ##################################
    # Debug data & reporting times
    ##################################
    # Write out DEBUG data in JSON if requested
    if args.debug:
        write_json(vocab, outDir, config["vocabFile"] + "-initial")
        write_json(postings, outDir, config["postingsFile"] + "-initial")
        write_json(skipDict, outDir, "skips")
        dTimer.qcheck("Index debug files written to disk")

    # Report execution times
    print("")
    print(dTimer)


if __name__ == "__main__":
    main()

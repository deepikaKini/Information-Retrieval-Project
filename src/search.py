###########################################################################
#
# search.py
#   - Main program for executing queries
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:12:16
###########################################################################

# Includes for this tool
from debug_fns import *
import debug_fns

dTimer = DebugTimer("Search")  # START timer
from io_fns import *
from query_fns import *

# Python libraries
import argparse

dTimer.qcheck("Python module load")


################################################################
# Main program
################################################################
def main():
    # Command line argument handling.
    argParser = argparse.ArgumentParser(
        description="Run one query of given type on the passed index (dir) & show results",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argParser.add_argument("idir", type=str, help="Directory containing index data")
    argParser.add_argument("term", nargs="+", help="Search term(s)")

    argParser.add_argument(
        "-d", "--debug", action="store_true", help="show debug output"
    )
    argParser.add_argument("-k", "--topk", default=10, help="number of results")

    # Arguments for query type -- there can only be one.
    group = argParser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-b",
        "--bow",
        action="store_true",
        default=True,
        help="query type: bag-of-words",
    )
    group.add_argument(
        "-c", "--conjunct", action="store_true", help="query type: conjunctive"
    )
    group.add_argument("-p", "--phrase", action="store_true", help="query type: phrase")

    # Separate parameter group for scoring functions
    group2 = argParser.add_mutually_exclusive_group(required=False)
    group2.add_argument(
        "-w",
        "--words",
        action="store_true",
        default="True",
        help="scoring: matched words",
    )
    group2.add_argument("-t", "--tfidf", action="store_true", help="scoring: tf-idf")

    args = argParser.parse_args()

    # DEBUG parsing
    # print(argParser.parse_args())

    ##################################
    # Configuration, Args, & Loading
    ##################################
    # Set debug flag (for debugging output)
    debug_fns.DEBUG = args.debug

    # Load configuration data and statistics
    indexDir = args.idir
    config = read_json(indexDir, "CONFIG_STATS")
    delta = bool(config["delta"])
    (doc_count, term_count) = (int(config["docs"]), int(config["terms"]))
    config["debug"] = args.debug

    # Load index data
    docIndex = read_json(indexDir, config["docIndexFile"], int_keys=True)
    vocab = read_json(indexDir, config["vocabFile"])
    postings = read_json(indexDir, config["postingsFile"])

    # Collect query information
    query = args.term
    bow = args.bow
    tfidf = args.tfidf
    phraseQ = args.phrase
    topk = int(args.topk)

    # Identify query type
    query_type = "bow"
    if args.conjunct:
        query_type = "conjunct"
    if args.phrase:
        query_type = "phrase"

    # Identify scoring function
    score_type = "words"
    if args.tfidf:
        score_type = "tfidf"

    ##################################
    # Execute query
    ##################################
    # HACK: Store query information in the config dict
    config["query_type"] = query_type
    config["score_type"] = score_type

    # Identify terms include/missing within the index
    # DEBUG: Casefold needed here (i.e., lower case conversion)
    valid_query = []
    terms_skipped = []
    for t in query:
        lt = t.lower()
        if lt not in vocab:
            terms_skipped.append(lt)
        else:
            valid_query.append(lt)

    if len(valid_query) < 1:
        # Stop if query cannot be executed
        print(
            ">>> ERROR: Query contains no vocabulary terms for collection in "
            + config["indexDir"]
        )
        return 1

    # Set scoring functions
    qscore = always_one
    dscore = always_one
    if config["score_type"] == "tfidf":
        qscore = q_idf(vocab, config)
        dscore = d_tf

    # Create banner to make queries easier to spot at the terminal
    announce_query(config, query, valid_query, terms_skipped)

    # Run the query
    scoreHeap = None
    config["skips_read"] = 0
    config["posts_read"] = 0

    if query_type == "bow":
        scoreHeap = disjunct_query(
            valid_query, config, vocab, postings, docIndex, qscore, dscore
        )
    elif query_type == "conjunct":
        scoreHeap = conjunct_query(
            valid_query, config, vocab, postings, docIndex, qscore, dscore
        )
    elif query_type == "phrase":
        scoreHeap = conjunct_query(
            valid_query, config, vocab, postings, docIndex, qscore, dscore, phrase=True
        )
    else:
        dcheck("Invalid query type", query_type)

    dTimer.qcheck("Query execution")

    # Report results adn timing information
    showResults(scoreHeap, topk, docIndex, terms_skipped, config)
    dTimer.qcheck("Reporting results")

    print("\n")
    print(dTimer)
    print(">>---------\n")


if __name__ == "__main__":
    main()

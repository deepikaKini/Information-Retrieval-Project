###########################################################################
#
# query_fns.py
#   - Routines to execute queries
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:33:37
###########################################################################

# Include built-in heap for python
import math
import heapq
import sys
from debug_fns import *
from io_fns import *

# Large int to use in returning all matches
ALL = 10000


################################################################
# Scoring functions
################################################################
def q_idf(vocab, config):
    # Zobel & Moffat page 6
    def score(t, curr_post):
        return math.log(1 + config["docs"] / vocab[t][1])

    return score


def d_tf(t, curr_post):
    # Zobel & Moffat page 6
    return 1 + math.log(curr_post[t][1])


def always_one(t, curr_post):
    return 1


################################################################
# Routines for Reading Posting
################################################################
def initialize_plist_refs(query, skipSize, vocab):
    # Initialize a list of posting file pointers for query terms
    # ( current_index, posts_read, postlist_start_index )
    pl_dict = dict()
    if skipSize > 1:
        for t in query:
            # DEBUG: Need to record the start of the non-skip postings for use in skip lists
            start_index = vocab[t][0] + 2 * math.floor(vocab[t][1] / skipSize)
            pl_dict[t] = [start_index, 0, start_index]

    else:
        pl_dict = {t: [vocab[t][0], 0, vocab[t][0]] for t in query}

    curr_post = dict()
    return (curr_post, pl_dict)


def advance_pl(t, next_post, pl_dict):
    (curr_index, num_reads, list_start_index) = pl_dict[t]
    
    return (curr_index + len(next_post), num_reads + 1, list_start_index)


def skip_pl(t, curr_post, config, skip_entry, pl_dict, skip_ref, skipSize):
    # Update posting list and skip list pointers using skip entry for term t
    # (index_pointer, number of items skipped/read, start_index)
    (index_pointer, items_read, start_index) = pl_dict[t]
    if index_pointer < start_index + skip_entry[1]:
        pl_dict[t] = [
            pl_dict[t][2] + skip_entry[1],
            skip_ref[t][1],
            pl_dict[t][2],
        ]

    # Update index into posting list for next skip AND number of postings skipped
    skip_ref[t] = [skip_ref[t][0] + 2, skip_ref[t][1] + skipSize]

    # Hack: store number of skip reads in config dict
    config["skips_read"] = config["skips_read"] + 1
    return (pl_dict, skip_ref)


def read_post(t, config, curr_post, pl_dict, vocab, postings, skip_doc_id=-1):
    # Use sublist operation to read posts
    (curr_index, item_no, start_index) = pl_dict[t]

    # DEBUG: If asked to read past end of list, return post to indicate this
    if item_no >= vocab[t][1]:
        curr_post[t] = [-1, -1, -1]
        return (curr_post, pl_dict, True)

    # Read doc id as-is for non-delta compressed entries
    nextPost = None
    if not config["delta"] or item_no == 0:
        nextPost = postings[curr_index : curr_index + postings[curr_index + 1] + 2]

    else:
        # Decode delta compressed id and positions
        docId = curr_post[t][0]
        if skip_doc_id > docId:
            docId = skip_doc_id

        nextPost = postings[curr_index : curr_index + postings[curr_index + 1] + 2]
        nextPost[0] += docId

        positionAccum = nextPost[2]
        for i in range(3, len(nextPost)):
            positionAccum += nextPost[i]
            nextPost[i] = positionAccum

    # Update current post and list pointer for term t; & record postings read
    curr_post[t] = nextPost
    pl_dict[t] = advance_pl(t, nextPost, pl_dict)
    config["posts_read"] = config["posts_read"] + 1

    return (curr_post, pl_dict, False)


def skip_forward(t, nextDocId, config, curr_post, pl_dict, skip_ref, vocab, postings):
    # Returns current post and posting list dicts, + whether list has been exhausted
    skipSize = int(config["skip_size"])
    skipped = False
    skip_doc_id = -1

    # Skip forward if appropriate
    finished = False
    while curr_post[t][0] < nextDocId and not finished:
        if skipSize > 1 and vocab[t][1] > skipSize and not skipped:
            # Advance through skip list entries, update post AND skip pointers
            while skip_ref[t][1] < vocab[t][1] and postings[skip_ref[t][0]] < nextDocId:
                # Read skip entry from the posting list
                skip_entry = [postings[skip_ref[t][0]], postings[skip_ref[t][0] + 1]]
                (pl_dict, skip_ref) = skip_pl(
                    t, curr_post, config, skip_entry, pl_dict, skip_ref, skipSize
                )
                skip_doc_id = skip_entry[0]

            skipped = True

        else:
            # Read a posting
            (curr_post, pl_dict, finished) = read_post(
                t, config, curr_post, pl_dict, vocab, postings, skip_doc_id
            )
            skip_doc_id = -1

    # Return whether list is complete
    return (curr_post, pl_dict, finished)


################################################################
# Query functions
################################################################
def conjunct_query(
    query, config, vocab, postings, docIndex, qt_score, dt_score, phrase=False
):
    hlist = []
    maxDocId = int(config["docs"])
    skipSize = config["skip_size"]

    # Get list sizes
    sizes = sorted([(t, vocab[t][1]) for t in query], key=lambda x: x[1])
    posts = sum([e[1] for e in sizes])
    ordered_terms = [e[0] for e in sizes]

    ##################################
    # Query detail message
    ##################################
    if phrase:
        print("[ Phrase Query ]")
    else:
        print("[ Conjunct Query ]")
    print("    Postings (", posts, "):", sizes)
    if config["score_type"] == "tfidf":
        idf_values = [(t, qt_score(t, None)) for t in ordered_terms]
        idf_strings = [f"({entry[0]}: {entry[1]:.2f})" for entry in idf_values]
        print("    Query term idf:", *idf_strings)
    print("    Scoring:", config["score_type"])
    print("    Skip size:", skipSize, "\n")

    ##################################
    # Running conjunct query
    ##################################
    # DEBUG: Initial skip contains skipSize elements; skips always start at location 0 in posting list
    (curr_post, pl_dict) = initialize_plist_refs(query, skipSize, vocab)
    for t in query:
        (curr_post, pl_dict, _) = read_post(
            t, config, curr_post, pl_dict, vocab, postings
        )

    skip_ref = {t: [vocab[t][0], skipSize] for t in query}

    # CONJUNCT Document-at-a-time retrieval
    finished = False
    while not finished:
        nextDocId = max([curr_post[t][0] for t in query])
        docScore = 0
        positions = dict()

        for t in ordered_terms:
            (curr_post, pl_dict, list_finished) = skip_forward(
                t, nextDocId, config, curr_post, pl_dict, skip_ref, vocab, postings
            )
            finished = finished or list_finished

            if curr_post[t][0] == nextDocId:
                # Update score and record term positions
                docScore += qt_score(t, curr_post) * dt_score(t, curr_post)
                positions[t] = curr_post[t][2:]

                # Advance to next post, record whether list is exhausted
                (curr_post, pl_dict, list_finished) = read_post(
                    t, config, curr_post, pl_dict, vocab, postings
                )
                finished = list_finished or finished

            else:
                # Doc not in all postings lists - do not finish scoring nextDocId
                docScore = 0
                break

        ##################################
        # phrase queries
        ##################################
        if len(positions) == len(query) and len(query) > 1 and phrase:
            phrase_matched = False
            # If phrase query, confirm that query terms can be found adjacent in-order
            all_positions = []
            for t in query:
                all_positions.extend([(t, l) for l in positions[t]])

            # Simple sliding window match: create pattern to match at each location
            all_positions = sorted(all_positions, key=lambda x: x[1])
            for i in range(0, len(all_positions) - len(query)):
                start_index = all_positions[i][1]
                pattern = list(
                    zip(query, list(range(start_index, start_index + len(query))))
                )

                if all_positions[i : i + len(query)] == pattern:
                    phrase_matched = True
                    break

            # Mark unmatched if phrase not found in correct order with adjacent terms
            if not phrase_matched:
                docScore = 0

        ##################################
        # Add to heap.
        # Normalize score by document size
        # if needed.
        ##################################
        if docScore > 0:
            if config["score_type"] != "words":
                docScore /= docIndex[nextDocId][2]
            heapq.heappush(hlist, (docScore, nextDocId))

    # Return heap list holding scored documents and number of posts read
    return hlist


def disjunct_query(query, config, vocab, postings, docIndex, qt_score, dt_score):
    # List for heap (priority queue).
    # NOTE: Skips are NOT used for disjunctive queries
    hlist = []
    maxDocId = int(config["docs"])
    skipSize = int(config["skip_size"])

    # Get list sizes (for reporting only)
    sizes = sorted([(t, vocab[t][1]) for t in query], key=lambda x: x[1])
    posts = sum([e[1] for e in sizes])
    ordered_terms = [e[0] for e in sizes]

    ##################################
    # Query detail message
    ##################################
    print("[ Disjunct Query ]\n    Postings (", posts, "):", sizes)
    print("    Scoring:", config["score_type"])

    if config["score_type"] == "tfidf":
        idf_values = [(t, qt_score(t, None)) for t in ordered_terms]
        idf_strings = [f"({entry[0]}: {entry[1]:.2f})" for entry in idf_values]
        print("    Query term idf:", *idf_strings)
    print("    Skip size:", skipSize, "\n")

    ##################################
    # Running disjoint query
    ##################################
    # Initialize list pointers, read first post from each list
    (curr_post, pl_dict) = initialize_plist_refs(query, skipSize, vocab)
    for t in query:
        (curr_post, pl_dict, _) = read_post(
            t, config, curr_post, pl_dict, vocab, postings
        )
    # curr_post = {t: read_post(t, config, None, pl_dict, postings) for t in query}

    # DISJUNCT Docment-at-a-time retrieval
    minDocId = min([curr_post[t][0] for t in query])
    finished = {t: False for t in query}
    while False in finished.values():
        docScore = 0

        for t in query:
            if not finished[t] and curr_post[t][0] == minDocId:
                # Update score, read next post, record whether list is finished
                docScore += qt_score(t, curr_post) * dt_score(t, curr_post)
                (curr_post, pl_dict, finished[t]) = read_post(
                    t, config, curr_post, pl_dict, vocab, postings
                )

        # Normalize score by document length if needed
        if config["score_type"] != "words":
            docScore /= docIndex[minDocId][2]
        heapq.heappush(hlist, (docScore, minDocId))

        # Recheck for minimum doc id
        minDocId = maxDocId
        for t in query:
            if not finished[t]:
                minDocId = min(minDocId, curr_post[t][0])

    # Return heap list holding scored documents and number of posts read, and #skips read (0)
    return hlist

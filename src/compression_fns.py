###########################################################################
#
# compression_fns.py
#   - Routines for compressing posting lists
#
###########################################################################
# Revision History
# v 1.0.0 Original Version: Richard Zanibbi, Mar 03 2023 21:00:08
###########################################################################


################################################################
# Delta compression
################################################################
def delta_compress_ints(int_list):
    # Compress a list of integers
    diffs = [int_list[i] - int_list[i - 1] for i in range(1, len(int_list))]
    out_list = [int_list[0]]
    out_list.extend(diffs)
    return out_list


def delta_compress_list(post_list):
    # Posting lists contain a (0) docId, (1) document frequency for a term, and (2) a list of word positions
    # Compress both the docIds and the word positions.
    diffs = [
        [
            post_list[i][0] - post_list[i - 1][0],
            post_list[i][1],
            delta_compress_ints(post_list[i][2]),
        ]
        for i in range(1, len(post_list))
    ]
    out_list = [
        [post_list[0][0], post_list[0][1], delta_compress_ints(post_list[0][2])]
    ]
    out_list.extend(diffs)
    return out_list


def delta_compress(postings):
    delta_postings = dict()

    for term in postings:
        delta_postings[term] = delta_compress_list(postings[term])

    return delta_postings

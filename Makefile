install:
	# >> Add progress bar package (user package list)
	#
	# For creating submissions, black, a2ps, ps2pdf (from the `ghostscript`
	# tool) are required. These are installed on the CS systems already.
	pip3 install --user black progress tqdm

submit:
	./bin/create_zip src

clean:
	# >> Delete index files in ./index-data
	# >> Delete code submission files
	# >> Delete cached python data
	#
	rm -f ./index-data/*
	rm -f *.zip source-listing.pdf
	rm -rf ./__pycache__ src/__pycache__


index_call:
	./index cacm

index: index_call

search_call:
	./search -k 10 index-data information

search: search_call 


# Test rule
test:
	# Single term
	./search index-data entropy
	./search -c index-data entropy
	./search -p index-data entropy
	# Two terms in same docs, never a phrase
	./search index-data information entropy
	./search -c index-data information entropy
	./search -p index-data information entropy
	# Two terms in same docs, often as a phrase
	./search index-data information retrieval
	./search -c index-data information retrieval
	./search -p index-data information retrieval

help:
	@echo ""
	##### Indexing help  ####
	python3 src/index.py --help
	@echo ""
	##### Retrieval help ####
	python3 src/search.py --help

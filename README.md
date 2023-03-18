# README : CACM Abstract Exercise

**Prof. Zanibbi, Spring 2023 (Information Retrieval course @ RIT)**

**Note**: This markdown (.md) file is in the same format used for 
READMEs on GitHub, GitLab, etc. To see a nicely formatted version of 
this file, load it in a markdown file viewer.

---

This is a simple sytem for indexing the CACM abstract collection provided by Croft et al. The initial version contains functions that need to be reimplemented (marked using comments). Please see the writeup for additional details. 


## Directory Contents

This directory contains:

* `bin/` : submission scripts
* `cacm/` : directory containing CACM abstract collection (from Croft et al.)
* `index-data/` : default directory for index output files
* `src/` : python source file directory **(EDIT the files in this directory)**
* `Makefile` installation, running programs, cleaning up (**Note**: students may add rules to this file for your own use!)
* `./index` : bash script for indexing 
* `./search` : bash script for queries 

To understand how the `./index` and `./search` programs work, use the `cat`
command to see the script, e.g., 

```
cat ./index
```
The file can also be opened in any text editor. 

## Installation

To install needed python packages, issue:

```
make
```
## Indexing

The python `src/index.py` program is used for indexing. To make this easier to
use, the `./index` bash script is provided in the current directory.

To see how to run the program, issue:

```
./index -h
```

For an example of outputs produced by the indexing program, issue:

```
make index
```
The generated files are written to the `index-data/` directory.

## Search (Retrieval)

The python `src/search.py` program is used to execute a query over an existing index directory. `./search` is a bash script in the current directory than can be used to run commands more easily.

To see the options for the program, issue: 

```
./search -h
```

To see an example search, after running `make index` as described above, issue:

```
make search
```

Search results are printed to the terminal.

## Cleaning Up

To remove current index files in `index-data`, cached python files, and any intermediate submission files (described below), issue:

```
make clean
```

## Debugging Tools

The file `debug_fns.py` provides the timer used for recording execution times, along with convenience functions 
for printing out messages and variable values. These are being provided to make it easier to debug your program
by checking variable values with accompanying messages.

**Importing.** See `src/search.py` for how to import the debug module and its DEBUG flag variable, which the provided command line
arguments are used to set.

**Debug functions (`check`, `pcheck`, etc.).** 

* The main debug functions are `check`, for printing a message and variable value, and `pcheck`, which pausing, prompting the user to press a key. 
* There are variations to add newlines before showing variable values (`ncheck`, `npcheck`)
* Other variations add '[DEBUG]' to the message prefix (`dcheck`, `dpcheck`), optionally combined with newlines before variable values (`dncheck`, `dnpcheck`) 

**Showing/Hiding Debug Output (`-d`).** 

* When you run the `search` and `index` programs with the `-d` flag, all messages from `check()` and `pcheck()` will be written to the standard output (i.e., the terminal). 
* If the `-d` flag is missing, these
functions will produce no output. 
* Use this to quickly show/hide debug messages *without* editing your program.

**Simple Example.** After importing `debug_fns`, if we have a list `L = [1, 2, 3]`, then this function call:

```
check("List L",L)
```
will produce this output:

```
List L: [1, 2, 3]
```
To introduce a pause after the message is printed, this function call:

```
pcheck("List L",L)
```
will produce this output:

```
List L : [1, 2, 3]
Press any key to continue...	
```


Any data type with a built-in string function can be passed as the second argument: this includes all primitive
variable types (int, string, bool, etc.), lists, tuples, dictionaries, and sets, for example.





## Submitting your Program

**When your program is ready to submit**, run the following command from the current directory:

```
make submit
```

This will create two files in the top-level directory:

1. `source-code.zip` 
2. `source-listing.pdf` 

Submit these files through MyCourses (see write-up for complete submission instructions).

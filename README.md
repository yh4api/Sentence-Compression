# Sentence-Compression
reference: Dependency Tree Based Sentence Compression, Katja Filippova and Michael Strube

usage:
python sc_main.py [\d] [-p-d]
the second parameter is how many tree path you want to keep, default is 10. Only when you do not need -p -d argument can this integer be omitted.
-p is to parse the sentence, otherwise the rest of the code will be executed using the old tree data. I type -p only when I process an experiement with new sentence
-d is to print out the dependency tree.

tools: <br/>
1. stanford corenlp dependency parser <br/>
2. language modeling tool: ngram-count <br/>
3. ilp tool: lpsolve <br/>

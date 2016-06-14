import re
import sys

word_dic = {}
inf = open("train_corpus_all", "r")
for x in inf:
	x = x.splitlines()[0]
	xs = x.split()
	for s in xs:
		if s in word_dic.keys():
			word_dic[s] += 1
		else:
			word_dic[s] = 1

inf.close()
if "-f" in sys.argv:
	for k, v in word_dic.iteritems():
		print k+" "+str(v)
else:
	for k in word_dic.keys():
		print k

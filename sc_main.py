import sys
import re
import xml.etree.ElementTree as ET
import os 
from subprocess import call
from parse_dep_func import *
import shutil
#w_freq = {}

limit = 10 if len(sys.argv) < 2 else sys.argv[1]
j = 0
words = []
word_sort_list = {}
cwd = os.getcwd()
for line in open('/home/yhlin/corenlp/raw_text/input'):
	for word in line.strip().split():
		j += 1
		word_sort_list[word] = word_sort_list.get(word, [])
		word_sort_list[word].append(j)
		w_freq[word] = w_freq.get(word, 0) + 1
		words.append(word)



create_w_c_matrix(j)
if "-p" in sys.argv:
	os.chdir("/home/yhlin/corenlp/")
	res = call("python '/home/yhlin/corenlp/callParser.py'", shell=True)
	os.chdir(cwd)

input_f = "/home/yhlin/corenlp/outputXML/input.xml"

tree = ET.parse(input_f)

#global max_depth = 0
#gram_prob = {} 
#w_counts = {}
load_lm()
load_dictionary(w_counts)

pos = ["" for i in range(j+2)]

root = ""
#ET.dump(tree)
#ET.dump(tree.getroot().find("./document/sentences/sentence/dependencies[@type=\"collapsed-dependencies\"]"))

def to_lower_first(dependency):
	for dep in dependency:
		for d in dep:
			if d.attrib["idx"] == "1":
				d.text = d.text.lower()



def walk_tree(tree):
	root = tree.getroot()
	sentences = root.find("./document/sentences")
	ind = 1
	for child in sentences:
		res = child.find("./dependencies[@type=\"collapsed-dependencies\"]")	
		basic_res = child.find("./dependencies[@type=\"basic-dependencies\"]")	

		tokens = child.find("./tokens")
		#ET.dump(tokens)
		#print len(pos), words
		for token in tokens:
			pos[int(token.attrib["id"])] = token.find("POS").text
				
		check_copy_loop(res)
		check_cop(res)
		first_token = tokens[0]
		if first_token.find("NER").text == "O" and first_token.find("word").text != "I":
			to_lower_first(res)
			w = first_token.find("word").text
			word_sort_list[w.lower()] = word_sort_list.get(w.lower(), []) + word_sort_list[w]
			w_freq[w.lower()] = w_freq.get(w.lower(), 0) + w_freq[w]
		check_combine(res, 0)
		walk(res, 0, 0 , "ROOT")
		pobj_combine(res, basic_res, pos)
		add_path(res , pos, words)
		#ET.dump(res)
		convert_ilf(res, limit)
		shutil.copyfile("obj_func", "lpsolve/input.txt")
		os.chdir("lpsolve")
		call("./run.bat", shell=True)
		os.chdir("../")
		restore_sentence(res, word_sort_list, words)
		ind += 1
			
walk_tree(tree) 
m_depth = get_max_depth()

if "-d" in sys.argv:
	print "\n"
	ET.dump(tree.getroot().find("./document/sentences/sentence/dependencies[@type=\"collapsed-dependencies\"]"))

#print_w_connection_matrix() 

import sys
import re
import xml.etree.ElementTree as ET
import math
import copy


max_depth = 0 
gram_prob = {}
post_prob = {}
gram_prob_orig = {}
w_counts = {}
w_connection_matrix = [[]]
tag_connection_matrix = {}
combine_d = {}
total_c = 0
w_freq = {}
def get_kid(text):
	text = re.sub('\s', ' ', text)
	text = re.sub(' {2,}', ' ', text)
	m = prog.search(text)
	if m != None: #VP (VBP include)
		pa = m.group(1)
		kid = m.group(2)
		print "phrase="+pa
		print kid
		get_kid(kid)
	else: #VBP include
		n = text.split()
		POS = n[0]
		word = n[1]
		print "POS "+POS
		print "word "+word
def get_max_depth():
	return max_depth
def print_w_connection_matrix():
	for l in w_connection_matrix:
		print l
	
def create_w_c_matrix(j):
	global w_connection_matrix
	w_connection_matrix = [[0 for i in range(j+2)] for k in range(j+2)]
	
def print_json(text, level):
	if text.startswith("("):
		out.write( "\"data\":{\"type\":\""+text[1:]+"\"},\"children\":[{")
	elif text.endswith(")"):
		print_json(text[:-1], level+1)
		out.write( "}]")
		if level==0:
			out.write("},{")
	else:
		out.write("\"data\":{")
		out.write("\"word\":\""+text+"\", \"type\":\"TK\"")
		out.write("}, \"children\":[]")

def get_kid2(text):
	text = text.rstrip()
	text = re.sub(r'\s', ' ', text)
	text = re.sub(r' {2,}', ' ', text)
#	text = text[1:-1]
	ts = text.split()
	for t in ts:
		print_json(t, 0)	
#	text = text.replace("(", "',['")
#	text = text.replace(")", "'],'")
#	text = "['" + text + "']"

def load_lm():
	global gram_prob
	global post_prob
	lm = "lm.dat"
	lm_f = open(lm, "r")
	start = 0
	for l in lm_f:
		l = l.strip()
		if l == "":
			continue
		if l.find("1-grams")!= -1:
			start = 3
			continue
		elif l.find("2-grams")!= -1:
			#print post_prob	
			start = 1
			continue
		elif l.find("3-grams") != -1:
			start = 2
		if start == 1:
			l = l.splitlines()[0]
			m = l.split("\t")
			#print l, m
			prob = m[0]
			word = m[1]
			gram_prob[word] = gram_prob.get(word, math.pow(10, float(prob)))
		elif start == 3:
			l = l.splitlines()[0]
			m = l.split("\t")
			if len(m) <= 2:
				continue
			prob = m[0]
			word = m[1]
			post = m[2]
			post_prob[word] = post_prob.setdefault(word, [prob, post])
	lm_f.close()

def load_dictionary(w_counts):
	global total_c
	dictionary = "dictionary_f"
	dict_f = open(dictionary, "r")
	for f in dict_f:
		f = f.splitlines()[0]
		fs = f.split()
		w_counts[fs[0]] = int(fs[1])
	total_c = sum(w_counts.values())
	dict_f.close()

def add_path(dependencies, POS, words):
	#VBP, VBD, VBZ add connection to ROOT
	#CC
	ind = 0
	root_orig = dependencies.find("./dep[@type=\"root\"]")
	root_verb_orig = root_orig.find("./dependent").attrib["idx"]
	#print words, POS
	for ii in POS:
		if ii in ["VBP", "VBD", "VBZ"]:
			#print ind
			if root_verb_orig == str(ind):
				ind += 1
				continue
			else:
				n_copy = copy.deepcopy(root_orig)
				n_copy.find("./dependent").set("idx", str(ind))
				n_copy.find("./dependent").text = words[ind-1]
				conj_k = dependencies.find('./dep/dependent[@idx=\"'+str(ind)+'\"]/..')
				if conj_k != None:
					n_copy.find("./d_weight").text = conj_k.find("./d_weight").text
					n_copy.find("./depth").text = conj_k.find("./depth").text
					dependencies.append(n_copy)
		ind += 1
					
	for deps in dependencies:
		if deps.attrib["type"].startswith("conj"):
			conj_n_id = deps.find("./governor").attrib["idx"]
			if POS[int(conj_n_id)][0] == "V":
				continue
			conj_k = deps.find("./dependent")
			conj_p = dependencies.find('./dep/dependent[@idx=\"'+str(conj_n_id)+'\"]/..')
			n_copy = copy.deepcopy(conj_p)
			n_copy.find("./dependent").set("idx", conj_k.attrib["idx"])
			n_copy.find("./dependent").text = conj_k.text
			n_copy.find("./d_weight").text = deps.find("./d_weight").text
			n_copy.find("./depth").text = deps.find("./depth").text
			dependencies.append(n_copy)
			dependencies.remove(deps) #should I keep nodes? nodes can't be deleted in order to restore the sentence
		
def convert_ilf(dependencies, limit_length):
	global w_connection_matrix
	edge_num = 1
	m_d = get_max_depth()
	obj_func = open("obj_func", "w")
	obj_func_str = "max: "
	for deps in dependencies:
		p = deps.find("./governor")
		k = deps.find("./dependent")
		w_connection_matrix[int(p.attrib["idx"])][int(k.attrib["idx"])] = edge_num
		tag_connection_matrix[deps.attrib["type"]] = tag_connection_matrix.get(deps.attrib["type"], [])
		tag_connection_matrix[deps.attrib["type"]].append((int(p.attrib["idx"]), int(k.attrib["idx"])))
		#print edge_num, p.attrib["idx"], k.attrib["idx"]
		obj_func_str = obj_func_str + str(math.sqrt(int(deps.find("depth").text)+1)*float(deps.find("./d_weight").text)*float(deps.find("./l_h_weight").text)/m_d) +"x"+ str(edge_num) + " +"
		edge_num += 1
	#print_w_connection_matrix()	
	obj_func.write(obj_func_str[:-1]+";\n")
	#write ROOT constraint
	constraint = ""
	for r in w_connection_matrix[0]:
		if r != 0:
			constraint = constraint+ "x" +str(r) + "+"
	obj_func.write(constraint[:-1]+"= 1 ;\n")
	sen_length = len(w_connection_matrix) 
	#write one-HEAD-only constraint
	for l in range(1, sen_length):
		constraint = ""
		count = 0
		for n in range(1, sen_length):
			t = w_connection_matrix[n][l]
			if t != 0:
				constraint = constraint + "x" + str(t)+ "+"
				count += 1
		if constraint!="" and count > 1:
			obj_func.write(constraint[:-1]+"= 1 ;\n")
		
	#write connectivity constraint
	for l in range(1, sen_length):
		for n in w_connection_matrix[l]:
			constraint = ""
			if n != 0 :
				for a in range(0, sen_length):
					if w_connection_matrix[a][l] != 0:
						constraint = constraint + "x" + str(w_connection_matrix[a][l])+ "+"
				obj_func.write(constraint[:-1] + "- x" + str(n) +"> 0;\n")
	#write grammar constraint
	####
	### check each node to make sure it includes at least subj, subjpass, dobj, cop if in its childpath
	for s in ["nsubj", "nsubjpass", "csubj", "cop"]:
		for t in tag_connection_matrix.get(s, []):
			c = w_connection_matrix[t[0]][t[1]]
			constraint = "x"+str(c)
			for x in range(0, sen_length):
				r = w_connection_matrix[x][t[0]]
				if r != 0:
					constraint = constraint + "- x"+str(r)
					pass
			obj_func.write(constraint + " = 0;\n")
					

	####
	#write length constraint
	constraint = ""
	for e in range(1, edge_num):
		constraint = constraint + "x" + str(e) + "+"
	obj_func.write(constraint[:-1] + "<" + str(limit_length)+";\n")
	obj_func.write("binary ")
	constraint = ""
	for e in range(1, edge_num):
		constraint = constraint + "x"+str(e)+","
	obj_func.write(constraint[:-1]+";\n")
	obj_func.close()
	#print_w_connection_matrix()	

def put_conj_back():
	pass

def restore_sentence(dependencies, wsl, str_list):
	comb_str_list = ["" for q in range(0, len(w_connection_matrix))]
	to_print_out = [0 for q in range(0, len(w_connection_matrix))]
	put_conj_back()
	ans = []
	lp_solve_out = open("lpsolve/output1.txt", "r")
	start = 0
	for l in lp_solve_out:
		if l.startswith("Actual values of the variables"):
			start = 1
			continue
		if start:
			ans.append(l[-3])
	lp_solve_out.close()
	ans_ind = 1
	for a in ans:
		#print a, ans_ind
		if a == "1":
			d = dependencies.find("./dep["+str(ans_ind)+"]")
			d_p = int(d.find("governor").attrib["idx"])
			d_k = int(d.find("dependent").attrib["idx"])
			to_print_out[d_p] = 1
			to_print_out[d_k] = 1
			comb_str_list[d_k] = d.find("dependent").text
			if d.attrib["type"].startswith("prep"):
				s = d.attrib["type"].split("_")
				if len(s) > 1:
				  	comb_str_list[d_k] = "_".join(s[1:]) + "_"+comb_str_list[d_k]
		ans_ind += 1 
#	print comb_str_list 
#	print "\n"
	s = ""
	ordx = 0
	for c in comb_str_list:
		if c != "":
			cs = c.split("_")
			if len(cs) > 1:
				cs.reverse()
				for css in cs[1:]:
					d_k = max([v for v in wsl[css] if v < ordx])
					to_print_out[d_k] = 1
		ordx += 1
								

#	print to_print_out
#	print "\n"
	ind = 0
	for t in to_print_out[1:]:
		if t ==1 :
#			s = s + comb_str_list[ind]+" "
			s = s + str_list[ind]+" "
		ind += 1
	print s
	
def d_weight(text):
#	fi * log(FA/FI)
	text_right_most = text.split("_")[-1]
	return w_freq[text_right_most] * math.log((total_c+len(w_counts))/(w_counts.get(text, 0)+1))

def walk(deps, p_node, depth, p_text):
	global max_depth, w_freq
	global w_connection_matrix
	kids = deps.findall("./dep/governor[@idx=\""+str(p_node)+"\"]/..")
	if depth > max_depth:
		max_depth = depth
	i = 1
	for k in kids:
		#ET.dump(k)
		k_node = k.find("./dependent")
	#	ET.dump(k_node)
		k_id = k_node.attrib["idx"]
	#	print int(p_node), int(k_id)
		#w_connection_matrix[int(p_node)][int(k_id)] = 1
		if k.attrib["type"] in ["ccomp", "root"]:
			walk(deps, k_id, depth+1, k_node.text)
			k.append(ET.fromstring("<depth>"+str(depth+1)+"</depth>"))
		#elif k.attrib["type"].endswith("cl"):
		#	walk(deps, k_id, depth-1, k_node.text)
		#	k.append(ET.fromstring("<depth>"+str(depth-1)+"</depth>"))
		else:
			walk(deps, k_id, depth, k_node.text)
			k.append(ET.fromstring("<depth>"+str(depth)+"</depth>"))
		#k.append(ET.fromstring("<l_h_weight>"+str(gram_prob[p_text+" "+k.attrib["type"]])+"</l_h_weight>"))
		k.append(ET.fromstring("<l_h_weight>"+cal_l_h_weight(p_text, k.attrib["type"])+"</l_h_weight>"))

		k.append(ET.fromstring("<d_weight>"+str(d_weight(k_node.text))+"</d_weight>"))
		i+=1
#	return max_depth

def cal_l_h_weight(h_text, l_label):
	
	if h_text+" "+l_label not in gram_prob:
		p = float(post_prob.get(h_text, [0,0])[1])+float(post_prob[l_label][0])
		return str(math.pow(10, p))
	else:
		return str(gram_prob[h_text+" "+l_label])


def walk_combine(deps, p_node_id, p_node=None):
	kids = deps.findall("./dep/governor[@idx=\""+str(p_node_id)+"\"]/..")
	i = 1
	for k in kids:
		k_node = k.find("./dependent")
		ET.dump(k)
		#ET.dump(k_node)
		if k.attrib["type"] =="det":
			 pass
		out.write("{")
		#print k_node.text+":::"+k.attrib["type"]
		k_id = k_node.attrib["idx"]
		out.write("\"children\":[")
		#print k_id
		walk_combine(deps, k_id, k)
		out.write("],")
		out.write("\"data\":{\"word\":\""+k_node.text+"_"+k.attrib["type"]+"_"+k_id+"\", \"type\":\"TK\"}")
		if i == len(kids):
			out.write("}")
		else:
			out.write("},")
		i+=1

def record_c(k_id, p_id):
	if p_id not in combine_d:
		combine_d[p_id] = "_".join(k_id, p_id)
	else:
		combine_d[p_id] = "_".join(k_id, combine_d[p_id])

def check_NER(deps, tokens):
	node_id = 0
	for t in tokens:
		if t.find("NER").text not in["O", "PERSON"]:
			combine_NER(deps, node_id, tokens, t.find("NER").text)
		node_id += 1

def combine_NER(deps, p_node_id, tokens, self_text):

	kids = deps.findall("./dep/governor[@idx=\""+str(p_node_id)+"\"]")
	self_node = deps.find("./dep/dependent[@idx=\""+str(p_node_id)+"\"]")
	kids.reverse()
	for k in kids:
		if k.attrib["type"] == "nn":
			k_node = k.find("./dependent")
			if tokens[k_node.attrib["idx"]].find("NER").text == self_text:
				text = k_node.text
				combine_t = "_".join([k_node.text, self_node.text])
				self_node.text = combine_t
				deps.remove(k)
				


def check_combine(deps, p_node_id):
	global combine_d
	kids = deps.findall("./dep/governor[@idx=\""+str(p_node_id)+"\"]/..")
	self_node = deps.find("./dep/dependent[@idx=\""+str(p_node_id)+"\"]")

	kids.reverse()
	i = 1
	for k in kids:
		k_node = k.find("./dependent")
		if k.attrib["type"] == "det":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
		#	record_c(k_node.attrib["idx"],self_node.attrib["idx"])
			deps.remove(k)
			continue
		elif k.attrib["type"] == "poss":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		elif k.attrib["type"] == "aux":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		elif k.attrib["type"] == "auxpass":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		elif k.attrib["type"] == "neg":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		k_id = k_node.attrib["idx"]
		check_combine(deps, k_id)
		i += 1

def pobj_combine(collapsed_dep, basic_dep, POS):#Happens when there are two consecutive IN, like because of, inside of, such as ... AFTER WALK
	for dep in collapsed_dep:
		if dep.attrib["type"] == "pobj":
			g = dep.find("governor")
			if POS[int(g.attrib["idx"])][0] != "V":
				continue
				
			d = dep.find("dependent")

			orig_d = basic_dep.find("./dep[@type=\"pobj\"]/dependent[@idx=\""+d.attrib["idx"]+"\"]/..")
			to_del = ""
			to_dels = collapsed_dep.findall("./dep/governor[@idx=\""+g.attrib["idx"]+"\"]/..")
			for td in to_dels:
				if td.find("dependent").attrib["idx"] == orig_d.find("governor").attrib["idx"]:
					to_del = td
					break
			dep.attrib["type"] = to_del.attrib["type"]
			collapsed_dep.remove(to_del)

def check_copy_loop(dependency):
	deps = dependency.findall('dep')
	for ds in deps:
		d = ds.find('dependent')
		if "copy" in d.keys():
			g = ds.find('governor')
			if g.attrib["idx"] == d.attrib["idx"]:
				dependency.remove(ds)
					
			
		
def check_cop(dependency):
	deps = dependency.findall('dep')
	for d in deps:
		if d.attrib["type"] == "cop":
			to_switch_p = d.find("governor")
			to_switch_p_id = to_switch_p.attrib["idx"]
			to_switch_p_text = to_switch_p.text
	
			to_switch_k = d.find("dependent")
			to_switch_k_id = to_switch_k.attrib["idx"]
			to_switch_k_text = to_switch_k.text
		#	print to_switch_p_id, to_switch_k_id
#			ET.dump(d)
			switch_cop_head(dependency, to_switch_p_id, to_switch_k_id, to_switch_k_text)

			to_switch_p.attrib["idx"] = to_switch_k_id
			to_switch_p.text = to_switch_k_text
	
			to_switch_k.attrib["idx"] = to_switch_p_id
			to_switch_k.text = to_switch_p_text

def switch_cop_head(deps, p, k, p_text):
	#grand_p = deps.find("./dep/dependent[@idx=\""+str(to_switch_p)+"\"]/..") should be this complete node 
	grand_p = deps.find("./dep/dependent[@idx=\""+str(p)+"\"]")
	grand_p.attrib["idx"] = k
	grand_p.text = p_text
	
	
	nsubj = deps.find("./dep[@type=\"nsubj\"]/governor[@idx=\""+str(p)+"\"]")
	if nsubj!=None:
		nsubj.attrib["idx"] = k
		nsubj.text = p_text
	cc = deps.find("./dep[@type=\"cc\"]/governor[@idx=\""+str(p)+"\"]")
	if cc != None:
		cc.attrib["idx"] = k
		cc.text = p_text
	aux = deps.find("./dep[@type=\"aux\"]/governor[@idx=\""+str(p)+"\"]")
	if aux != None:
		aux.attrib["idx"] = k
		aux.text = p_text
	mark = deps.find("./dep[@type=\"mark\"]/governor[@idx=\""+str(p)+"\"]")
	if mark != None:
		mark.attrib["idx"] = k
		mark.text = p_text

	"""
	for candidate in deps.findall("./dep/governor[@idx=\""+str(p)+"\"]/.."):
		c = candidate.find("dependent")
		if int(c.attrib["idx"]) < int(p):
			g = candidate.find("governor")
			g.attrib["idx"] = k
			g.text = p_text
		else:
			break
	"""


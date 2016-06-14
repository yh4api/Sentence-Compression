import sys
import re
import xml.etree.ElementTree as ET
import os

#inf = open(sys.argv[1], "r")

exp = '(.*?)\((.*)\)(.*)'
prog = re.compile(exp)

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

def walk(deps, p_node, p_text):
	kids = deps.findall("./dep/governor[@idx=\""+str(p_node)+"\"]/..")
	i = 1
	for k in kids:
		#ET.dump(k)
		k_node = k.find("./dependent")
		#ET.dump(k_node)
		#print k_node.text+":::"+k.attrib["type"]
		k_id = k_node.attrib["idx"]
		k_text = k_node.text
		out.write(p_text+" "+k.attrib["type"]+"\n")
		#print k_id
		walk(deps, k_id, k_text)
		"""
		if i == len(kids):
			out.write("]}")
		else:
			out.write("]},")
		"""
		i+=1
	if kids == []:
		#print "leaf"
		out.write(p_text+" END\n")

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

def check_combine(deps, p_node_id):
	kids = deps.findall("./dep/governor[@idx=\""+str(p_node_id)+"\"]/..")
	self_node = deps.find("./dep/dependent[@idx=\""+str(p_node_id)+"\"]")

	"""	
	for k in kids:
		k_node = k.find("./dependent")
		if k_node.attrib[idx] < p_node_id:
			left_kids.append(k)
		else:
			right_kids.append(k)
	for k in left_kids.reverse():
		k_node = k.find("./dependent")
		if k.attrib["type"] == "det":
			text = k_node.text
			combine_t = " ".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		elif k.attrib["type"] == "poss":
			text = k_node.text
			combine_t = " ".join([k_node.text, self_node.text])
			self_node.text = combine_t
			deps.remove(k)
			continue
		k_id = k_node.attrib["idx"]
		check_combine(deps, k_id)

	"""
	kids.reverse()
	i = 1
	for k in kids:
		k_node = k.find("./dependent")
		if k.attrib["type"] == "det":
			text = k_node.text
			combine_t = "_".join([k_node.text, self_node.text])
			self_node.text = combine_t
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
#			print to_switch_p_id, to_switch_k_id
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
out = open("train_corpus", "w")

def print_tree(tree):
	root = tree.getroot()
	sentences = root.find("./document/sentences")
	ind = 1
	for child in sentences:
		res = child.find("./dependencies[@type=\"collapsed-dependencies\"]")
		check_copy_loop(res)
		check_cop(res)

		first_token = child.find("./tokens/token[1]")
		if first_token.find("NER").text == "O" and first_token.find("word").text != "I":
			to_lower_first(res)
			
		check_combine(res, 0)
		walk(res, 0, "ROOT")
		ind += 1	

def to_lower_first(dependency):
	for dep in dependency:
		for d in dep:
			if d.attrib["idx"] == "1":
				d.text = d.text.lower()

if os.path.isfile(sys.argv[1]):
	print sys.argv[1]
	tree = ET.parse(sys.argv[1])
	print_tree(tree)
elif os.path.isdir(sys.argv[1]):
	file_list = os.listdir(sys.argv[1])
	for f in file_list:
		print f
		f_n = sys.argv[1]+"/"+f
		tree =ET.parse(f_n)
		print_tree(tree)

out.close()

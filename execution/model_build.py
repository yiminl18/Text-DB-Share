import numpy as np
import pdfplumber
import sys
import os
import Levenshtein
import json
# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
nltk.download('punkt')


def extract_bold_text(file):
    #find all bold words and the corresponding page number 
    bold_text_with_page_num = [] # (pg_num, text)
    bold_words = [] 
    with pdfplumber.open(file) as pdf: 
        for page_num, page in enumerate(pdf.pages):
            bold_t = page.filter(lambda obj: (obj["object_type"] == "char" and "Bold" in obj["fontname"]))
            text = [text for text in bold_t.extract_text().split('\n') if text != '']
            bold_text_with_page_num.extend([(page_num, text) for text in text])
            words = bold_t.extract_words()
            bold_words.extend([word for word in words])
    return bold_text_with_page_num, bold_words


def phrase_matching(words, phrase, loc):
    #return the matching phrase in bold_word_with_page_num starting from loc 
    target_words = phrase.split()
    #print(len(target_words),loc)
    sequence = ' '.join([word['text'] for word in words[loc:loc+len(target_words)]])
    #print(sequence)
    x0 = -1
    if(sequence == phrase):
        x0 = words[loc]['x0']
    return x0

def find_phrase_position(bold_text_with_page_num, bold_words):
    #compute the position of each phrase by finding matching phrases 
    loc = 0
    locations = []
    bold_vec = []
    i = 0
    for page_num, text in bold_text_with_page_num:
        #print(text, page_num)
        x0 = phrase_matching(bold_words, text, loc)
        if(x0 != -1):
            locations.append((text,x0))
            loc += len(text.split())
            bold_vec.append([text,x0,page_num])
            #print((text,x0,page_num))
        else:
            print('text not mathcing!', text)
        i+=1
        
    return bold_vec 

def filter_by_example(bold_vec, section_loc, delta):
    #filter the candidate headers by using the text location info 
    for i in range(len(bold_vec)):
        x0 = bold_vec[i][1]
        if(len(section_loc) == 1):
            if(abs(x0-section_loc[0]) <  delta or x0 < section_loc[0]):
                bold_vec[i].append(1)
            else:
                bold_vec[i].append(-1)
        elif(len(section_loc) == 2):
            if(abs(x0-section_loc[0]) < delta or abs(x0-section_loc[1]) < delta):
                bold_vec[i].append(1)
            else:
                bold_vec[i].append(-1)
        else:
            bold_vec[i].append(-1)
    return bold_vec


def construct_prompt(candidate_header):
    prompt = ''
    
    for header in candidate_header:
        template = 'Is the following phrase a header of section,' + header + '?. If yes, return 1; if NO, return 0. '
        prompt += template

    prompt += 'each answer is in a new line.'
    return prompt 

def filter_by_LLM(bold_vec):
    #filter the candidate headers by asking LLM for semantic meaning check 
    candidate_header = []
    for i in range(len(bold_vec)):
        #print(bold_vec[i])
        if(bold_vec[i][3] == 1):
            candidate_header.append(bold_vec[i][0])
    #print(candidate_header)
    prompt = (construct_prompt(candidate_header),'')
    #print(prompt)
    response = model('gpt4_azure',prompt)
    #print(response)
    ids = response.split('\n')
    #print(len(candidate_header), len(ids))
    keys = []
    for i in range(len(candidate_header)):
        if(ids[i] == '1'): 
            keys.append(candidate_header[i])
    #print(keys)
    selected = []
    for i in range(len(bold_vec)):
        if(bold_vec[i][3] == 1 and bold_vec[i][0] in keys):
            selected.append(bold_vec[i])
    return selected

def create_tree_by_example(node_vecs):
    #schema of node_vecs is: name, text_location, page_num, level
    #transform to a dict 
    tree = {}
    ids = 1
    for node in node_vecs:
        n = {}
        n['name'] = node[0]
        n['text_location'] = node[1]
        n['page_number'] = node[2]
        n['child_edge'] = []
        if(node[3] == 1):
            n['level'] = 1 #section
        elif(node[3] == 2):
            n['level'] = 2 #subsection
        else:
            n['level'] = 0 #root 
        tree[ids] = n
        ids = ids + 1
    return tree

def tree_table_content_by_example(section_loc,delta,file_path):
    bold_text_with_page_num, bold_word_with_page_num = extract_bold_text(file_path)
    #print(bold_word_with_page_num)
    bold_vec = find_phrase_position(bold_text_with_page_num, bold_word_with_page_num)
    #print(bold_vec)
    selected_bold_vec = filter_by_example(bold_vec, section_loc, delta)
    #print(selected_bold_vec)
    final = filter_by_LLM(selected_bold_vec)
    print(final)
    #print('****')
    return create_tree_by_example(final)

def extract_meta(response):
    #extract name of headers in different granularities 
    text = response.split('\n')
    meta = []
    for header in text:
        if('.' not in header):
            continue
        header = header.strip()
        words = header.split(' ',1)
        node_level = words[0].strip()
        node_name = words[1].strip()
        labels = node_level.split('.')

        #print(labels)

        if(labels[1].isdigit() is False):#this is the level of section 
            #print(node_id, header)
            node = {}
            node['level'] = 1 #section 
            node['name'] = node_name
            meta.append(node)
            #print(node)

        else:
            #level of subsection 
            node = {}
            node['level'] = 2
            node['name'] = node_name
            meta.append(node)
            #print(node)
        
    return meta 
    #return tree

#parse response stable for two levels 
def parse_response(response, tree):
    text = response.split('\n')
    node_id = 1
    children = []
    parent_node = node_id
    loc = 0
    lastSectionID = 1
    for header in text:
        #print('before',loc, len(text), header)
        if(header =='' or '.' not in header):
            loc += 1
            if(loc == len(text)):
                lastSectionID = parent_node
            continue
        header = header.strip()
        words = header.split(' ',1)
        node_level = words[0].strip()
        node_name = words[1].strip()
        labels = node_level.split('.')

        if(labels[1].isdigit() is False):#this is the level of section 
            #print(node_id, header)
            node = {}
            node['level'] = 1 #section 
            node['name'] = node_name
            tree[node_id] = node
            #add child edge 
            tree[parent_node]['child_edge'] = children
            tree[parent_node]['parent_edge'] = -1
            lastSectionID = node_id
            parent_node = node_id
            node_id = node_id + 1
            children = []

        else:
            #level of subsection 
            node = {}
            node['level'] = 2
            node['name'] = node_name
            tree[node_id] = node
            children.append(node_id)
            #add parent edge 
            tree[node_id]['parent_edge'] = parent_node
            tree[node_id]['child_edge'] = []
            node_id = node_id + 1
        loc += 1

    #handle last section 
    #print(lastSectionID,children)
    tree[lastSectionID]['parent_edge'] = -1
    tree[lastSectionID]['child_edge'] = children
    return tree

def parse_response_robust(response, tree, doc):#skip headers which are not present in doc 
    doc = doc.lower()
    text = response.split('\n')
    node_id = 1
    children = []
    parent_node = node_id
    loc = 0
    lastSectionID = 1
    sec_flag = 0
    for header in text:
        #print('before',loc, len(text), header)
        if(header =='' or '.' not in header):#skip garbage lines 
            loc += 1
            if(loc == len(text)):
                lastSectionID = parent_node
            continue
        header = header.strip()
        words = header.split(' ',1)
        node_level = words[0].strip()
        node_name = words[1].strip()
        
        if('.' not in node_level):
            continue
        labels = node_level.split('.')
        

        if(labels[1].isdigit() is False):#this is the level of section 
            #print(node_id, header)
            #print(node_name.lower(), len(doc))
            if(node_name.lower() not in doc):
                sec_flag = 1
                continue
            sec_flag = 0
            node = {}
            node['level'] = 1 #section 
            node['name'] = node_name
            tree[node_id] = node
            #add child edge 
            tree[parent_node]['child_edge'] = children
            tree[parent_node]['parent_edge'] = -1
            lastSectionID = node_id
            parent_node = node_id
            node_id = node_id + 1
            children = []

        else:
            #level of subsection 
            if(sec_flag == 1):#if section not exist, remove all subsections belonging to it 
                continue
            if(node_name.lower() not in doc):
                continue
            node = {}
            node['level'] = 2
            node['name'] = node_name
            tree[node_id] = node
            children.append(node_id)
            #add parent edge 
            tree[node_id]['parent_edge'] = parent_node
            tree[node_id]['child_edge'] = []
            node_id = node_id + 1
        loc += 1

    #handle last section 
    #print(lastSectionID,children)
    tree[lastSectionID]['parent_edge'] = -1
    tree[lastSectionID]['child_edge'] = children
    return tree

def read_text(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
    return text

def tree_table_content_by_gpt_paper(file_path):
    tree = {}
    text = read_text(file_path)
    instruction = 'Give me table of content for the following document, which includes the header of each section and sub-section. Make sure the name of header are the original phrases in the document. Make sure the order of section are in the same order in the given document. Example: 1. Section1, 1.1 Section 1.1. '
    prompt = (instruction,text)
    response = model('gpt4_long',prompt)
    print(response)
    #write_file(response)
    return parse_response(response, tree)

def tree_table_content_by_gpt_civic(file_path):
    tree = {}
    text = read_text(file_path)
    instruction = 'Give me table of content for the following document, which includes the header of each section and sub-section.  Make sure the order of section are in the same order in the given document. Example: 1. Section1, 1.1 Section 1.1. Only keep two levels, The first section starts with Capital Improvement Projects (Design). Make sure the name of header are the *original* phrases in the document.'
    prompt = (instruction,text)
    response = model('gpt4',prompt)
    return parse_response(response, tree, text) 

def write_table_content(file_path, out_path):
    tree = {}
    text = read_text(file_path)
    # instruction = 'Give me table of content for the following document, which includes the header of each section and sub-section. Make sure the name of header are the original phrases in the document. Make sure the order of section are in the same order in the given document. Example: 1. Section1, 1.1 Section 1.1. '
    instruction = 'Give me table of content for the following document, which includes the header of each section.  Make sure the order of section are in the same order in the given document. Make sure the name of header are the "original" phrases in the document. Do not create new words. Example: 1. Section1.'
    prompt = (instruction,text)
    response = model('gpt4',prompt)
    write_file(out_path, response)

def write_2_json(tree, dict_path):
    with open(dict_path, 'w') as file:
        json.dump(tree, file)

def read_tree_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def display_tree(tree):
    for id, node in tree.items():
        print(id)
        for key, value in node.items():
            print(key, value)

def find_coarse_leaves(tree):
    #note that coarse leaves are not only sub-sections, but also sections without children
    leaves = []
    for id, node in tree.items():
        #print(node)
        child_edges = node['child_edge']
        if(len(child_edges) == 0):# leaf node 
            leaves.append(id)
    return leaves

def create_fine_nodes(tree, text):
    #add fine-grained nodes from paragraphs and sentences 

    #extract all paragraphs
    paras = extract_paragraph_nodes(text)
    #print(len(paras))
    #extract deepest level in current tree
    start_level = 0
    for value in tree.values():
        #print(value)
        level = value['level']
        if(level > start_level):
            start_level = level

    paragraph_level = start_level + 1
    ids = len(tree) + 1

    leaves = find_coarse_leaves(tree) #leaves store the node id 
    # for i in leaves:
    #     print(tree[i]['name'])

    #find the paragraph locations for the deepest coarse nodes in current tree 
    matches = find_paragraph_location(paras, tree, leaves) # matches: [header, pid]
    
    #print(matches)
    
    #compute the pid range for leaves
    ranges = find_paragraph_range(matches, len(paras)-1)

    #print(ranges)

    #insert paragraph nodes into the tree 
    tree, para_id_map = create_paragraph_nodes(paras, tree, paragraph_level, ids)

    #print(para_id_map)
    #update deepest coarse nodes by adding children edges 
    tree = udpate_child_edges_for_leaves(ranges, tree, leaves, para_id_map)
    #display_tree(tree)
    

    sentence_level = paragraph_level + 1
    #insert sentence nodes into the tree 
    tree = create_sentence_nodes(sentence_level, tree, paras, para_id_map)

    return tree
    
def create_sentence_nodes(sentence_level, tree, paras, para_id_map):
    ids = len(tree) + 1
    for i in range(len(paras)):
        para = paras[i]
        # Tokenize the paragraph into sentences
        sentences = sent_tokenize(para)

        # Print the sentences
        for sentence in sentences:
            node = {}
            node['content'] = sentence
            parent_node = para_id_map[i]
            node['parent_edge'] = parent_node
            node['level'] = sentence_level
            tree[ids] = node
            ids += 1 

    return tree

def create_paragraph_nodes(paras, tree, paragraph_level, ids):
    para_id_map = {}# map: pid to node_id
    for i in range(len(paras)):
        node = {}
        node['level'] = paragraph_level
        node['pid'] = i
        node['parent_edge'] = 0
        tree[ids] = node
        para_id_map[i] = ids
        ids += 1
    return tree, para_id_map



def udpate_child_edges_for_leaves(ranges, tree, leaves, para_id_map):
    #para_id_map: pid to node_id for paragraphs 
    for id, node in tree.items():
        if(id not in leaves):
            continue
        header = node['name']
        if(header in ranges):
            interval = ranges[header]
            child = []
            for i in range(interval[0],interval[1]+1):
                para_node_id = para_id_map[i]
                child.append(para_node_id)#update child nodes for leaves
                tree[para_node_id]['parent_edge'] = id#update parent nodes for paragraphs 
            #print(child)
            node['child_edge'] = child
        else:
            node['child_edge'] = []
    return tree 
        
def add_front_node(tree):
    #add the front node before the first section
    #childs: paragraphs whose parent is 0
    front_node = {}
    front_node['level'] = 1
    front_node['name'] = 'front'
    front_node['parent_edge'] = -1
    childs = []
    for id, node in tree.items():
        if('parent_edge' in node):
            parent_edge = node['parent_edge']
            if(parent_edge == 0):
                childs.append(int(id))
    front_node['child_edge'] = childs
    tree["0"] = front_node
    return tree

def find_paragraph_range(matches, sz): #sz is the maximum pid 
    ranges = {}
    pids = []
    headers = []
    for header, pid in matches.items():
        headers.append(header)
        pids.append(pid)
    
    for i in range(1,len(pids)):
        ranges[headers[i-1]] = (pids[i-1],pids[i]-1)
    max_ids = len(pids)-1
    #print(len(headers), len(pids))
    ranges[headers[max_ids]] = (pids[max_ids],sz)
    
    return ranges


def find_paragraph_location(paras, tree, leaves):
    pid = 0
    matches = {}
    #for the coarsest nodes, find their paragraph locations 
    for id, node in tree.items():
        if(id not in leaves):
            continue
        header = node['name']
        #print('before', header)

        #find the first paragraph where header shows in the top 
        while(pid < len(paras)):
            if(paragraph_match(header, paras[pid]) == 0):
                pid = pid + 1
                continue
            #match found
            #print('after', header)
            matches[header] = pid
            pid = pid + 1 
            break 
    #print(matches)
    return matches


def levenshtein_similarity(str1, str2):
    return Levenshtein.ratio(str1, str2)

def paragraph_match(header, para):
    sz = len(header)
    # if(header == 'Acknowledgment'):
    #     print(para)
    if(levenshtein_similarity(para[:sz].upper(), header.upper()) >= 0.9):
        return 1
    if(contains_letter_or_number(header) is False and header in para):#fix for noise header 
        return 1
    if(header in para or header.upper() in para):
        return 1
    if(header.lower() in para.lower()):#modified for notice
        return 1
    return 0

def contains_letter_or_number(s):
    return any(char.isalnum() for char in s)

def extract_paragraph_nodes(text):
    can_paras = text.split('\n\n')
    paras = []
    for p in can_paras:
        if(p == ''):
            continue
        paras.append(p)
    return paras

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def tree_build_by_example_pipeline(pdf_file, text_file):
    section_loc_civic = [64]#67.5
    delta = 2
    section_loc = section_loc_civic
    tree = tree_table_content_by_example(section_loc,delta,pdf_file)
    display_tree(tree)
    text = read_text(text_file)
    tree = create_fine_nodes(tree, text)
    return tree 

def tree_build_gpt_pipeline(text_file, table_content_file):
    if(table_content_file != ''):
        text = read_text(text_file)
        table_content = read_text(table_content_file)
        tree = parse_response_robust(table_content, {}, text)#parse_response works for paper and civic
    else:
        #tree = tree_table_content_by_gpt_paper(text_file)
        tree = tree_table_content_by_gpt_civic(text_file)
    display_tree(tree)
    text = read_text(text_file)
    tree = create_fine_nodes(tree, text)
    tree = add_front_node(tree)
    return tree 

def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
    return files 

def clean_paper_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    #print(folder_path, paper_path)
    title = title.replace('.pdf', '')
    title = title[1:] 
    title = title 
    return title 

def clean_civic_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf.txt', '')
    title = title[1:] 
    title = title.rsplit('.txt', 1)[0]
    return title 

def add_node_size(tree, text):
    #find sentence level 
    sentence_level = 0
    for node in tree.values():
        level = node['level']
        if(level > sentence_level):
            sentence_level = level
    
    #update node sizes for sentence level
    #print('sentence_level: ', sentence_level)
    for id, node in tree.items():
        if(node['level'] == sentence_level):
            sz = len(word_tokenize(node['content']))
            node['size'] = sz

    paragraph_level = sentence_level - 1
    #update all paragraph_level
    paras = extract_paragraph_nodes(text)
    for id, node in tree.items():
        if(node['level'] == paragraph_level):
            pid = node['pid']
            sz = len(word_tokenize(paras[pid]))
            node['size'] = sz

    level = paragraph_level - 1
    #iteratively update node sizes for more coarse levels  
    while(level >= 1):
        for id, node in tree.items():
            if(node['level'] == level):
                sz = 0
                children = node['child_edge']
                for child in children:
                    child = str(child)
                    if('size' in tree[child]):
                        sz = sz + tree[child]['size']
                node['size'] = sz
        level = level - 1
    return tree 

def all_alpha_caps(string):
    # Filter out non-alphabetic characters and check if they are all uppercase
    alpha_chars = [char for char in string if char.isalpha()]
    return all(char.isupper() for char in alpha_chars)


# gets textual patterns for all words in pdf
def get_patterns(pdf_path):
    res = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=True, extra_attrs=["fontname", "size"])
            for word in words:
                bbox = word['x0'], word['top'], word['x1'], word['bottom']
                # font name usually includes whether italics or bold
                attributes = (word['text'], {"font": word["fontname"], "size": round(word["size"], 3), "alpha_caps_bool": all_alpha_caps(word["text"]), "bbox": bbox})
                #print(bbox)
                res.append(attributes)
    return res


def extract_pattern_phrases(headers, words_pattern):
    #extract textual patterns for phrases 
    loc = 0
    patterns = {}
    for header in headers:
        print(header['level'])
        print(header['name'])
        while(loc < len(words_pattern)):
            pattern, new_loc = extract_pattern_phrase(header['name'], loc, words_pattern)
            patterns[header] = pattern
            loc = new_loc
    return patterns 

def extract_pattern_phrase(header, loc, words_pattern):
    #extract textual patterns for one phrase 
    pattern = {}
    while(loc < len(words_pattern)):
        words = header.split('')
        flag = 1
        for i in range(len(words)):
            word = words[i]
            if(word != words_pattern[loc+i][0]):
                flag = 0
                break
        if(flag == 0):
            loc += 1

    


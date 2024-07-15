import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
import numpy as np
import json 
import llama_index_openai
import UDF_registration
import model_build
import llama_index_openai
import summarization
from nltk.tokenize import word_tokenize
import os 
import sys
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
model_name = 'gpt4o'

def context_size(context):
    return len(word_tokenize(context))

def extract_paragraph_nodes(text):
    can_paras = text.split('\n\n')
    paras = []
    for p in can_paras:
        if(p == ''):
            continue
        paras.append(p)
    return paras

def extract_blocks(tree, text):

    paras = extract_paragraph_nodes(text)
    sentence_level = 0
    for node in tree.values():
        if('level' in node and node['level'] > sentence_level):
            sentence_level = node['level']
    
    para_level = sentence_level - 1

    sentences = []
    #pick sentences 
    sec_map = {}
    para_map = {}
    for id, node in tree.items():
        if(node['level'] == sentence_level):
            sentence = node['content']
            sentences.append(sentence)
            sec_map[sentence] = id
        if(node['level'] == para_level):
            pid = node['pid']
            para = paras[pid]
            para_map[para] = id
    
    return sentences, sec_map, paras, para_map

def get_metadata(block_map, tree):
    #get metadata (name of coarse node) for each block (sentence/paragraph)
    #block_map: map to tree id
    #block_map: {block: node_id}
    meta = {}#for each node, return its all parent node in coarse level  
    for block, id in block_map.items():
        parent_node = tree[str(id)]['parent_edge']
        while(parent_node != -1):
            if(parent_node == 0):
                val = {}
                val['name'] = ['others']
                meta[block] = val
                break
            else:
                if('name' in tree[str(parent_node)]):
                    name = tree[str(parent_node)]['name']
                    if(block not in meta):
                        val = {}
                        val['name'] = [name]
                        meta[block] = val
                    else:
                        meta[block]['name'].append(name)
                    parent_node = tree[str(parent_node)]['parent_edge']
                else:
                    parent_node = tree[str(parent_node)]['parent_edge']

    return meta

def get_metadata_refined(block_map, tree):
    #get metadata (name of coarse node) for each block (sentence/paragraph)
    #block_map: map to tree id
    #block_map: {block: node_id}
    meta = {}#for each node, return its all parent node in coarse level  
    for block, id in block_map.items():
        parent_node = tree[str(id)]['parent_edge']
        while(parent_node != -1):
            if(parent_node == 0):
                val = {}
                val[1] = 'others'
                meta[block] = val
                break
            else:
                if('name' in tree[str(parent_node)]):
                    name = tree[str(parent_node)]['name']
                    level = tree[str(parent_node)]['level']
                    if(block not in meta):
                        val = {}
                        val[level] = name
                        meta[block] = val
                    else:
                        meta[block][level] = name
                    parent_node = tree[str(parent_node)]['parent_edge']
                else:
                    parent_node = tree[str(parent_node)]['parent_edge']

    return meta

def window_adaption(tree, units):
    #taking a set of candidate nodes filtered by either keyword search or embeddings 
    #decide a set of window/context to cover all candidate nodes  
    answer_nodes = []

    level = 0 #level of units 
    for id in units:
        if(id in tree and 'level' in tree[id]):
            level = tree[id]['level']
            answer_nodes.append(id)#answer node should be STR! 
    #print(level)

    #MAKE SURE the TYPE is consistent to all INT 
    while(level >= 1):
        #print('level:',level)
        parent_map = {}
        for id, node in tree.items():
            if(node['level'] == level and id in answer_nodes):
                if('parent_edge' in node):
                    parent = str(node['parent_edge'])
                    if(parent == '-1' or parent == '0'):
                        continue
                else:
                    continue
                
                if(parent in parent_map):#there exist sibling node 
                    #pick parent nodes 
                    if(parent not in answer_nodes):#add parent 
                        answer_nodes.append(parent)
                    if(parent_map[parent] in answer_nodes):#remove sibing node
                        answer_nodes.remove(parent_map[parent])
                    if(id in answer_nodes):#remove sibing node
                        answer_nodes.remove(id)
                else:
                    parent_map[parent] = id

                # print(answer_nodes)
                # print('---------------')
        level -= 1

    return answer_nodes
    

def display_tree(tree, nodes):
    for node in nodes:
        print(tree[node])

def semantic_search_llamaindex(query, blocks_nodes, index, k):#block is a text block, such as parapragh, block_node is the corresponding node id in the tree 

    chunks = llama_index_openai.context_retrieve(index, query, k)#context is a set of text chunks
    nodes = find_tree_nodes_from_text_chunks(chunks, blocks_nodes)
    return nodes 

def find_tree_nodes_from_text_chunks(chunks, block_nodes):
    #blocks are text block in tree representation
    #block nodes are the corresponding node ids
    #by default: map to sentence node 
    sz = 0
    context_nodes = []
    for chunk in chunks:
        #print(chunk)
        if(chunk in block_nodes):
            context_nodes.append(block_nodes[chunk])
            sz += context_size(chunk)
        else:
            print('do not match!')
    #print('context size before:', sz)
    return context_nodes

def read_text(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def read_tree_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def find_para_chilren(node, tree):
    #return the children of a given node in paragraph level 
    children = []
    
    childs = tree[node]['child_edge']
    if(childs[0] != -1 and 'pid' in tree[str(childs[0])]):#it is a subsection whose child is already paragraph
        return childs
    else:#it is a section
        for child in childs:#child is a subsection
            children.extend(tree[str(child)]['child_edge'])
    return children

def search_parent(tree, level):#by default, level = 1: section 
    pa = {}#for each node, return its parent node in the given level 
    for id, node in tree.items():
        if(node['level'] == level):
            #print(id)
            pa[id] = id
        elif(node['level'] == level+1):
            pa[id] = node['parent_edge']
        elif(node['level'] == level+2):
            parent = node['parent_edge']
            if(parent in pa):
                pa[id] = pa[parent]
            elif(parent == 0):
                pa[id] = 0
            else:
                if(tree[str(parent)]['level'] == level):
                    pa[id] = parent
                else:
                    pa[id] = tree[str(parent)]['parent_edge']
        else:
            parent = node['parent_edge']
            if(parent in pa):
                pa[id] = pa[parent]
            else:
                if(parent == 0):
                    pa[id] = 0
                else:
                    parent = tree[str(parent)]['parent_edge']
                    
                    if(parent == 0):
                        pa[id] = 0
                    elif(tree[str(parent)]['level'] == level):
                        pa[id] = parent
                    else:
                        pa[id] = tree[str(parent)]['parent_edge']

    #print(pa["1"])
    return pa

def return_context(query, para_map, index, text, tree, k):
    nodes = semantic_search_llamaindex(query, para_map, index, k)
    answers = window_adaption(tree, nodes)

    context = ''
    pids = []

    paras = extract_paragraph_nodes(text)
    for node in answers:
        if('pid' in tree[node]):#it is paragraph
            pids.append(tree[node]['pid'])
        else:#it is coarse nodes above paras
            child_pids = []
            children = find_para_chilren(node, tree)
            for child in children:
                child_pids.append(tree[str(child)]['pid'])
            pids.extend(child_pids)

    #collect context 
    pids.sort() #make sure the order of paras is correct 
    for pid in pids:
        context += paras[pid]
    return context

def get_context_for_coarse_node(node_name, level, tree, paras):
    #return context for coarse node in the tree 
    target = ''
    for id, node in tree.items():
        if(node['name'] == node_name and node['level'] == level):
            target = id
            break
    context = ''
    pids = []

    children = find_para_chilren(target, tree)
    for child in children:
        pids.append(tree[str(child)]['pid'])

    #collect context 
    pids.sort() #make sure the order of paras is correct 
    #print(pids)
    for pid in pids:
        context += paras[pid]
    return context


def get_node_by_level(tree, level):
    ans = []
    for id, node in tree.items():
        if(node['level'] == level):
            ans.append(id)
    return ans

def filter_by_human_label(label, level, tree, nodes):
    #nodes are the candidates filtered by upstream techniques 
    #label is the name of coarse node, level is the corresponding level of the label
    #pa is the parent map 
    ans = []
    pa = search_parent(tree, level)
    level_nodes = get_node_by_level(tree, level)

    label_id = 0
    for node in level_nodes:
        name = tree[str(node)]['name']
        if(name.lower() == label.lower()):
            label_id = node
            break

    for node in nodes:
        parent = pa[str(node)]
        #print(node, parent, label_id, type(parent), type(label_id))
        if(str(parent) == str(label_id)):
            ans.append(node)
    return ans 

def get_context_metadata(index, question, k, keyword):
    response, sz, rag_sentence = llama_index_openai.text_retriever(index, k, question, keyword)
    print(rag_sentence)

def search_ancestor_names(tree, node, pa):
    #pa: str -> int
    names = []
    names.append(tree[str(node)]['name'])
    f = True
    while(f):
        parent = pa[str(node)]
        if(parent == node or str(parent) not in pa):#reach the root node
            break
        names.append(tree[str(parent)]['name'])
        node = parent
    #print('------')
    #print(names)
    return names

def get_context_by_node_ID(node, tree, paras):
    #return context for coarse node in the tree 
    target = node
    context = ''
    pids = []

    children = find_para_chilren(target, tree)
    #print(children)
    for child in children:
        pids.append(tree[str(child)]['pid'])

    #collect context 
    pids.sort() #make sure the order of paras is correct 
    #print(pids)
    for pid in pids:
        context += paras[pid]
    return context

def summary_construct_per_node(tree, node, index, k, question, parent, paras):
    level = tree[str(node)]['level']
    name = tree[str(node)]['name']
    #print(name)
    keyword = (level, name)

    summary = ''

    #names of current node and its ancestors
    summary += ','.join(search_ancestor_names(tree, node, parent))
    summary += '. \n' 
    #print(summary)

    #append extrasive summary 
    #context = get_context_by_node_ID(node, tree, paras)
    #summary += summarization.spacy_summary(context, k = 3)

    #sentences that are related with question
    response, sz, rag_sentence = llama_index_openai.text_retriever(index, k, question, keyword)

    #expand the rag_sentences to its neighbors 
    summary += rag_sentence
    summary += '. \n\n'

    return summary

def tree_search_with_summary(tree, text, stop_level, index, question, parent, paras, k):
    nodes = get_node_by_level(tree, stop_level)
    # print(stop_level)
    #print(nodes)
    instruction = 'The following is a list of texts describing each section in a paper document. Each text starts with a ID number. ' + question + '. ' 
    context = ''
    id = 1
    mp = {}
    response = ''
    #paras = extract_paragraph_nodes(text)
    for node in nodes:
        name = tree[str(node)]['name']
        context += str(id) + ': '
        context += 'Section name is ' + name + '. '
        context += 'Section summary is: '

        summary = summary_construct_per_node(tree, node, index, k, question, parent, paras)
        context +=  summary
        context += '\n\n'
        id += 1

        
    #print(instruction, context)
    prompt = (instruction,context)
    response = model(model_name,prompt)
    #print(response)
    return response, context_size(context)

def tree_search_with_metadata_summary(tree, paras, sql_id):
    #tree search guided by the extracted metadata and summary associated with each node 
    
    top_nodes = get_node_by_level(tree, 1)
    sqls = UDF_registration.civic_SQLs()
    filters = sqls[sql_id]['filters']
    #print(filters)

    target_nodes = []

    for node in top_nodes:
        name = tree[str(node)]['name']
        is_path = 0
        #check filters to identify those related nodes 
        is_topic = 0
        for n,f in filters.items():
            key = f[1]
            if(key in name.lower()):
                is_path += 1
            if(n == 'topic'):
                is_topic = 1
        if(is_path == 2):
            target_nodes.append(node)
        elif(is_path == 1 and is_topic == 1):
            target_nodes.append(node)
            #print(name)

    context = {}
    #return a list of context for each project 
    for node in target_nodes:
        #print(tree[str(node)]['name'])
        children = tree[str(node)]['child_edge']#its children can also be paragraphs 
        if('pid' in tree[str(children[0])]):#it is a paragraph
            context[name] = get_context_for_coarse_node(name,2,tree,paras)
        else:
            for child in children:
                name = tree[str(child)]['name']
                context[name] = get_context_for_coarse_node(name,2,tree,paras)

    return context 





    



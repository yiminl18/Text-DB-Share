#This script implements the complete query execution by combining different components together 
# Get the directory of the current file
import evaluation
import filtering
import model_build
import query_interface 
import os 
import sys
import UDF_registration
import time 
import nltk
import graph_rag
import argparse
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
import pandas as pd
import execution.llama_index_openai as llama_index_openai

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
model_name = 'gpt4o'

def construct_target(pred, udfs):
    #contruct target for embedding search 
    target = udfs[pred[0]] + ' ' + pred[2]
    return target

def context_size(context):
    return len(word_tokenize(context))


def evaluate_SQL_civic(strategy,data,text_folder,tree_folder,index_folder,out_folder):
    text_files = model_build.scan_files(text_folder)
    entity_mention = 'project' #natural language description of an entity 
    desp = UDF_registration.civic_attr_desp()
    sqls = UDF_registration.civic_SQLs()#readl sqls
    
    for sql_id in range(1,len(sqls)):
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)

        #for each sql, store the following values 
        result = {}#{document_name: ans_list}
        times = {}#{document_name: total_time}
        sizes = {}#{document_name: total_size}
        i=0
        for text_file in text_files:#iterate all document 
            #print(text_file)
            ans = []
            if('DS_Store' in text_file):
                continue
            text = model_build.read_text(text_file)
            title = model_build.clean_paper_title(text_file, text_folder)
            print(i,title)

            st = time.time()
            size = 0

            response = [] 

            if(strategy == 'GPT_single'):
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals',data)
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                    response.append(str(res))
                    print(res.lower(), sz)
                    size += sz
                
            elif(strategy == 'GPT_merge'):
                prompt = UDF_registration.get_combined_prompt(sql, desp, data)
                print(prompt)
                res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                if('none' not in str(res).lower()):
                    response.append(str(res))
                size += sz

            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'paragraph')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals',data)
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index, k=15)
                    response.append(str(res))
                    print(str(res).lower())
                    print(sz)
                    size += sz
            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals',data)
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index)
                    response.append(str(res))
                    print(str(res).lower(), sz)
                    size += sz

            elif(strategy == 'textdb_summary'):
                text_val = filtering.read_text(text_file)
                paras = filtering.extract_paragraph_nodes(text_val)
                tree_path = tree_folder + '/tree_' + title
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'sentence')
                #print('tree path:')
                #print(tree_path)
                if(llama_index_openai.file_exist(tree_path) == False):#check tree existence
                    #print('yes')
                    continue
                tree_val = filtering.read_tree_json(tree_path)
                parent = filtering.search_parent(tree_val, 1)
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    #print('yes')
                    continue
                index_val = llama_index_openai.load_index(index_path)
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals', 'civic')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index_val, text = text_val, tree = tree_val, tuple_level = 2, parent = parent, paras = paras, k=3)#sz: number of tokens used 
                    print(res.lower(), sz)
                    size += sz
                    response.append(res)
                    
                
            et = time.time()
            print(et-st)
            print(size)
            result[title] = response
            times[title] = et-st
            sizes[title] = size
            
            i+=1
            #break

       
        
        sql_version = 'sql' + str(sql_id+1) +'.txt'

        path2 = out_folder + '/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = out_folder + '/ans_' + strategy + '_' + sql_version
        query_interface.write_2_json(result, path3)
        #break

def evaluate_SQL_notice(strategy,data,text_folder,tree_folder,index_folder,out_folder):
    text_files = model_build.scan_files(text_folder)
    entity_mention = 'violation document' #natural language description of an entity 
    
    sqls = UDF_registration.notice_SQLs()#readl sqls
    desp = UDF_registration.notice_attr_desp()
    
    for sql_id in range(0, len(sqls)):#scan each query 
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)
        

        #for each sql, store the following values 
        result = {}#{document_name: ans_list}
        times = {}#{document_name: total_time}
        sizes = {}#{document_name: total_size}
        i=0
        for text_file in text_files:#iterate all document 
            #print(text_file)
            ans = []
            if('DS_Store' in text_file):
                continue
            text = model_build.read_text(text_file)
            title = model_build.clean_paper_title(text_file, text_folder)
            print(i,title)

            #read index 
            index = None
            index_path = ''

            st = time.time()
            size = 0

            response = [] 
            ans_flag = 1
            if(strategy == 'GPT_single'):
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'NoticeViolation')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                    print(res.lower(), sz)
                    size += sz
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        #print('determined false')
                        break
                    
            elif(strategy == 'GPT_merge'):
                #translate sql to a prompt 
                #print(sql, desp, data)
                prompt = UDF_registration.get_combined_prompt(sql, desp, data)
                print(prompt)
                res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                size += sz
                if(res.lower() == 'false' or 'none' in res.lower()):
                    ans_flag = 0
                    #print('determined false')
            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'block')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'NoticeViolation')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index, k=1)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break

            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'NoticeViolation')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break

            elif(strategy == 'textdb_summary'):
                text_val = filtering.read_text(text_file)
                tree_path = tree_folder + '/tree_' + title
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'sentence')
                #print('tree path:')
                #print(tree_path)
                if(llama_index_openai.file_exist(tree_path) == False):#check index existence
                    #print('yes')
                    continue
                tree_val = filtering.read_tree_json(tree_path)
                parent = filtering.search_parent(tree_val, 1)
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    #print('yes')
                    continue
                index_val = llama_index_openai.load_index(index_path)
                paras = filtering.extract_paragraph_nodes(text_val)
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', 'NoticeViolation')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index_val, text = text_val, tree = tree_val, parent = parent, paras = paras,k=3)#sz: number of tokens used 
                    print(res.lower(), sz)
                    size += sz
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        #print('determined false')
                        break

            et = time.time()
            i+=1
            if(ans_flag == 1):
                print('true')
                response.append('true')#project = paper name (title)
            else:
                response.append('false')
                print('false')

            result[title] = response
            sizes[title] = size
            times[title] = et-st

            #break
        
        sql_version = 'sql' + str(sql_id+1) +'.txt'

        path2 = out_folder + '/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = out_folder + '/ans_' + strategy + '_' + sql_version
        query_interface.write_2_json(result, path3)

        #break

#seperate for different datasets since the projection is a little bit different 
def evaluate_SQL_paper(strategy,data,text_folder,tree_folder,index_folder,out_folder):
    text_files = model_build.scan_files(text_folder)

    entity_mention = 'paper' #natural language description of an entity 
    
    sqls = UDF_registration.paper_SQLs()#readl sqls

    if(data == 'paper'):
        desp = UDF_registration.paper_attr_desp()
    elif(data == 'civic'):
        desp = UDF_registration.civic_attr_desp()
    elif(data == 'NoticeViolation'):
        desp = UDF_registration.notice_attr_desp()
    
    for sql_id in range(0, len(sqls)):#scan each query 
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)

        result = {}#{document_name: ans_list}
        times = {}#{document_name: total_time}
        sizes = {}#{document_name: total_size}
        i=0
        for text_file in text_files:#iterate all document 
            #print(text_file)
            ans = []
            if('DS_Store' in text_file):
                continue
            text = model_build.read_text(text_file)
            title = model_build.clean_paper_title(text_file, text_folder)
            print(i,title)

            #read index 
            index = None
            index_path = ''

            st = time.time()
            size = 0

            response = [] 
            ans_flag = 1

            if(strategy == 'GPT_single'):
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', data)
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                    print(res.lower(), sz)
                    size += sz
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        #print('determined false')
                        break
                    
            elif(strategy == 'GPT_merge'):
                #translate sql to a prompt 
                prompt = UDF_registration.get_combined_prompt(sql, desp, data)
                print(prompt)
                res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                size += sz
                if(res.lower() == 'false' or 'none' in res.lower()):
                    ans_flag = 0
                    #print('determined false')
            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'block')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool',data)
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index, k=5)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break
            
            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_openai.load_index(index_path)
                

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', data)
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break


            elif(strategy == 'textdb_summary'):
                text_val = filtering.read_text(text_file)
                paras = filtering.extract_paragraph_nodes(text_val)
                tree_path = tree_folder + '/tree_' + title
                index_path = llama_index_openai.construct_index_path(text_file, text_folder, index_folder, 'sentence')
                #print('tree path:')
                #print(tree_path)
                if(llama_index_openai.file_exist(tree_path) == False):#check index existence
                    #print('yes')
                    continue
                tree_val = filtering.read_tree_json(tree_path)
                parent = filtering.search_parent(tree_val, 1)
                #print(index_path)
                if(llama_index_openai.file_exist(index_path) == False):#check index existence
                    #print('yes')
                    continue
                index_val = llama_index_openai.load_index(index_path)
                parent = filtering.search_parent(tree_val, 1)
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', 'paper')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, model_name, prompt, index = index_val, text = text_val, tree = tree_val, parent = parent, paras = paras, k=3)#sz: number of tokens used 
                    print(res.lower(), sz)
                    size += sz
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        break

            et = time.time()
            i+=1
            if(ans_flag == 1):
                print('true')
                response.append(title)#project = paper name (title)
            else:
                print('false')

            result[title] = response
            sizes[title] = size
            times[title] = et-st

            break
        
        sql_version = 'sql' + str(sql_id+1) +'.txt'

        path2 = out_folder + '/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = out_folder + '/ans_' + strategy + '_' + sql_version
        query_interface.write_2_json(result, path3)

        #break
    
def evaluate_graph_rag(data, text_folder,out_folder):
    text_files = model_build.scan_files(text_folder)
    model = 'gpt-4o'

    

    if(data == 'paper'):
        desp = UDF_registration.paper_attr_desp()
        entity_mention = 'paper' #natural language description of an entity 
        sqls = UDF_registration.paper_SQLs()#readl sqls
    elif(data == 'civic'):
        desp = UDF_registration.civic_attr_desp()
        entity_mention = 'project'
        sqls = UDF_registration.civic_SQLs()#readl sqls
    elif(data == 'NoticeViolation'):
        desp = UDF_registration.notice_attr_desp()
        entity_mention = 'violation document'
        sqls = UDF_registration.notice_SQLs()#readl sqls

    #print(len(sqls))

    for text_file in text_files:#iterate all document 
        
        if('DS_Store' in text_file):
            continue
        text = model_build.read_text(text_file)
        title = model_build.clean_paper_title(text_file, text_folder)

        path1 = out_folder + '/times_' + 'graph_rag' + '_' + title + '.txt'
        #check if exists
        if os.path.exists(path1):
            continue

        result = {}#{sql_id: ans_list}
        times = {}#{sql_id: total_time}
        sizes = {}#{sql_id: total_size}

        st = time.time()
        #for each document, build graph 
        try:
            query_engine, build_tokens, token_counter = graph_rag.build_graph(text, model)
        except Exception as e:
            continue
        et = time.time()

        print("Currently evaluate " + title + '...')

        print('Build graph time: ', et-st)
        print('Build graph tokens:', build_tokens)

        times['build'] = et-st
        sizes['build'] = build_tokens


        #scan the query workload for current document 
        for sql_id in range(0, len(sqls)):#scan each query 
            sql = sqls[sql_id]
            st = time.time()
            print('sql id:', sql_id)

            #for current SQL, scan all filters 
            ans_flag = 0
            size = 0
            response = []
            instruction = 'Do not add explanations. '

            if(data == 'paper' or data == 'NoticeViolation'):
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', data)
                    print(prompt)
                    #evaluate a predicate 
                    res, sz = graph_rag.graph_rag_api(query_engine, prompt+instruction, token_counter)
                    print(res.lower(), sz)
                    size += sz
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        break
                if(ans_flag == 1):
                    result[sql_id] = 'true'
                else:
                    result[sql_id] = 'false'
            else:
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals', data)
                    print(prompt)
                    #evaluate a predicate 
                    res, sz = graph_rag.graph_rag_api(query_engine, prompt+instruction, token_counter)
                    print(res.lower(), sz)
                    response.append(str(res))
                    size += sz
                    
                    if('false' in res.lower() or 'none' in res.lower()):
                        ans_flag = 0
                        break
                result[sql_id] = response

                    
            et = time.time()
            times[sql_id] = et-st
            sizes[sql_id] = size 
            # if(sql_id > 5):
            #     break

        path1 = out_folder + '/times_' + 'graph_rag' + '_' + title + '.txt'
        query_interface.write_2_json(times, path1)

        path2 = out_folder + '/sizes_' + 'graph_rag' + '_' + title + '.txt'
        query_interface.write_2_json(sizes, path2)

        path3 = out_folder + '/ans_' + 'graph_rag' + '_' + title + '.txt'
        query_interface.write_2_json(result, path3)

        #break

        
    

def merge_response(response):
    #response is a list of strings, where a string contains a list of vals seperate by ','
    if(len(response) == 0):
        return response
    ans = response[0].split(',')
    if(len(response) == 1):
        return ans
    for i in range(1, len(response)):
        val1 = set(response[i].split(','))
        val2 = set(ans)
        ans = list(val1.intersection(val2))
    return ans 

def parse_response(response):
    responses = response.split('\n')
    print(len(responses))
    
    ans = []
    for res in responses:
        print(res)
        vals = res.split(',')
        new_vals = []
        for val in vals:
            if('A1.' in val):
                val = val.replace('A1.','')
            if('A2.' in val):
                val = val.replace('A2.','')
            if('A3.' in val):
                val = val.replace('A3.','')
            new_vals.append(val.strip().lower()) 
        ans.append(new_vals)
    # print(ans[0])
    # print(ans[1])
    # print(ans[2])
    common_ans = set(ans[0]).intersection(ans[1], ans[2])
    print(common_ans)
    return list(common_ans)

def get_root_path():
    current_path = os.path.abspath(os.path.dirname(__file__))
    parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
    #print("Parent path:", parent_path)
    return parent_path


def run(args):
    data = args.data
    strategy = args.strategy
    model = args.model
    root_path = get_root_path()

    text_folder = root_path + '/data/' + data + '/extracted_data'
    tree_folder = root_path + '/data/' + data + '/runtime_data'
    index_folder = root_path + '/index/' + data + '/index/'
    out_folder = root_path + '/out/' + data

    if(strategy == 'Graph_RAG'):
        evaluate_graph_rag(data, text_folder,out_folder)
    else:
        if(data == 'paper'):
            evaluate_SQL_paper(strategy,data,text_folder,tree_folder,index_folder,out_folder)
        elif(data == 'civic'):
            evaluate_SQL_civic(strategy,data,text_folder,tree_folder,index_folder,out_folder)
        elif(data == 'NoticeViolation'):
            evaluate_SQL_notice(strategy,data,text_folder,tree_folder,index_folder,out_folder)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="A script that accepts command-line parameters.")
    parser.add_argument('--data', type=str, required=True, help='The type of data can be one of [paper, civic, NoticeViolation].')
    parser.add_argument('--strategy', type=str, required=True, help='The type of strategy can be one of [GPT_single, GPT_merge, LlamaIndex_seq, LlamaIndex_tree, textdb_summary].')
    parser.add_argument('--model', type=str, required=True, help='The type of supported model can be one of [gpt4o,gpt4omini,llama3.2, deepseekR1-1.5b].')

    args = parser.parse_args()
    run(args)

    
    





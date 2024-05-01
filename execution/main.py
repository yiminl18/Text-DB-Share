#This script implements the complete query execution by combining different components together 
# Get the directory of the current file
import evaluation
import filtering
import model_build
import query_interface 
import os 
import sys
import UDF_registration
import GPT_baseline
import time 
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
import pandas as pd
import llama_index_azure

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
#model_name = 'gpt4_long'
model_name = 'gpt35_azure'

def construct_target(pred, udfs):
    #contruct target for embedding search 
    target = udfs[pred[0]] + ' ' + pred[2]
    return target

def context_size(context):
    return len(word_tokenize(context))

def query_execution(selected_attrs, udfs, file_index, text, tree, selectivity, cached):#evaluate query in one data block unit 
    #parse query 
    

    #order the predicates based on the runtime selectivities 
    if(len(selectivity) > 0):
        preds_ordered = dict(sorted(selectivity.items(), key=lambda item: item[1][0] / item[1][1]))

    for pred, selectivity in preds_ordered.items():
        if(pred[0]!='publication_date'):
            continue
        #compute context 
        target = construct_target(pred, udfs)
        print('Starting a new predicate...')
        print(pred)
        print(target)
        context = filtering.return_context(text, tree, target, 10)
        print('context length', context_size(context))
        #print('context:', context)
        # flag, response = evaluation.evaluate_single_predicate(context, model, pred, udfs)

        # print(flag, response)

        # #update cached: {udf: {file_index: value}}
        # value = {}
        # value[file_index] = response
        # udf = pred[0]
        # cached[udf] = value

        # if(flag == 0):#query fails current predicate
        #     #update selectivity
        #     selectivity[pred][1] += 1
        #     return {}, preds_ordered, cached
        # else:
        #     #update selectivity
        #     selectivity[pred][1] += 1
        #     selectivity[pred][0] += 1

    #current data block satisfies all predicates, compute projections
    # answers = {}
    # for project in selected_attrs:
    #     context = context = filtering.return_context(text, tree, udfs[project],20)
    #     answers[project] = evaluation.evaluate_single_project(context, model, project, udfs)
        
    #return answers, preds_ordered, cached



def evaluate_predicate_paper(udfs, text_files, text_folder_paper):
    strategy = 'textdb'
    answers = []
    i = 0
    answer_col = []
    answer_col.append('title')
    times = {}
    sizes = {}
    
    for udf_name, instruction in udfs.items():
        answer_col.append(udf_name)
    for file in text_files:
        index = ''
        
        if(strategy == 'LlamaIndex' or strategy == 'textdb'):
            index_path = llama_index_azure.construct_index_path(file, text_folder_paper, 'paragraph')
            if(llama_index_azure.file_exist(index_path) == False):
                continue
            index = llama_index_azure.load_index(index_path)

            text = filtering.read_text(file)
            tree_path = llama_index_azure.construct_tree_path(file, text_folder_paper)
            #print(tree_path)
            tree = filtering.read_tree_json(tree_path)
            sentences, sec_map, paras, para_map = filtering.extract_blocks(tree, text)

        answer = []
        
        title = model_build.clean_paper_title(file, text_folder_paper)
        print(i, title)
        answer.append(file)
        context = model_build.read_text(file)
        size = context_size(context)

        total_time = 0
        for udf_name, instruction in udfs.items():
            st = time.time()
            response, sz = evaluation.evaluate_udf(strategy, model, instruction, context, index, para_map, text, tree, 10)
            answer.append(response)
            print(udf_name, response, sz)
            et = time.time()
            if(strategy == 'LlamaIndex' or strategy == 'textdb'):
                key = title + '|' + udf_name
                sizes[key] = sz
                times[key] = (et-st)
            total_time += (et-st)


        print('time:', total_time)
        
        if(strategy == 'GPT'):
            sizes[title] = size
            times[title] = (et-st)
        answers.append(answer)
        i += 1
        # if(i>=1):
        #     break
    
    df = pd.DataFrame(answers, columns=answer_col)
    path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_textdb_window_10paragraph.csv'
    df.to_csv(path)

    path1 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/times_textdb_window_10paragraph.txt'
    query_interface.write_2_json(times, path1)

    path2 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/sizes_textdb_window_10paragraph.txt'
    query_interface.write_2_json(sizes, path2)
    return answers



def evaluate_SQL_civic(text_files):
    strategy = 'LlamaIndex_tree' #GPT_single, GPT_merge, LlamaIndex_seq, LlamaIndex_tree 
    data = 'civic' #paper,civic,NoticeViolation
    entity_mention = 'paper' #natural language description of an entity 
    desp = UDF_registration.civic_attr_desp()
    sqls = UDF_registration.civic_SQLs()#readl sqls
    
    for sql_id in range(1,len(sqls)):
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)
        

        index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/civic/index/'
        text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/extracted_data'
        tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/runtime_data'

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

            # index = None
            # if(strategy == 'LlamaIndex' or strategy == 'textdb' or strategy == 'LlamaIndex-long'):
            #     index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'paragraph')
            # if(strategy == 'LlamaIndex-tree'):
            #     index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'tree')

            # if(llama_index_azure.file_exist(index_path) == False):
            #     continue
            # index = llama_index_azure.load_index(index_path)
            # paras = filtering.extract_paragraph_nodes(text)
            # tree_path = llama_index_azure.construct_tree_path(text_file, text_folder, tree_folder)
            # tree = filtering.read_tree_json(tree_path)

            st = time.time()
            size = 0

            response = [] 

            if(strategy == 'GPT_single'):
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
                    response.append(str(res))
                    print(res.lower(), sz)
                    size += sz
                
            elif(strategy == 'GPT_merge'):
                prompt = UDF_registration.get_combined_prompt(sql, desp, data)
                print(prompt)
                res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                if('none' not in str(res).lower()):
                    response.append(str(res))
                size += sz

            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'paragraph')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index, k=15)
                    response.append(str(res))
                    print(str(res).lower())
                    print(sz)
                    size += sz
            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'vals')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index)
                    response.append(str(res))
                    print(str(res).lower(), sz)
                    size += sz

            elif(strategy == 'textdb'):
                bool_filters = sql['bool_filters']
                #print(bool_filters)
                context = filtering.tree_search_with_metadata_summary(tree, paras, sql_id)
                ans = ''
                for name, cons in context.items():#iterate each project
                    ssz = 0
                    yc = 0
                    for key, prompt in bool_filters.items():#check each filter 
                        res, sz = evaluation.evaluate_udf('GPT', model, prompt, context = cons)
                        ssz += sz
                        if('yes' in res.lower()):
                            yc += 1
                    size += ssz
                    if(yc == 2):
                        ans = ans + name + ','
                response.append(ans[:-1])#remove last ','
                    
                
            et = time.time()
            print(et-st)
            print(size)
            result[title] = merge_response(response)
            times[title] = et-st
            sizes[title] = size
            
            i+=1
            #break

       
        
        sql_version = 'sql' + str(sql_id+1) +'.txt'
        
        #write result, time and size into local files
        path1 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/civic/times_' + strategy + '_' + sql_version
        query_interface.write_2_json(times, path1)

        path2 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/civic/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/civic/ans_' + strategy + '_' + sql_version
        query_interface.write_2_json(result, path3)
        #break

def evaluate_SQL_notice(text_files):
    strategy = 'textdb_summary' #GPT_single, GPT_merge, LlamaIndex_seq, LlamaIndex_tree, textdb_summary 
    data = 'notice' #paper,civic,NoticeViolation
    entity_mention = 'violation document' #natural language description of an entity 
    
    sqls = UDF_registration.notice_SQLs()#readl sqls

    if(data == 'paper'):
        desp = UDF_registration.paper_attr_desp()
    elif(data == 'civic'):
        desp = UDF_registration.civic_attr_desp()
    elif(data == 'notice'):
        desp = UDF_registration.notice_attr_desp()
    
    for sql_id in range(0, len(sqls)):#scan each query 
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)
        

        index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/' + 'NoticeViolation' + '/index/'
        text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + 'NoticeViolation' +  '/extracted_data'
        tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + 'NoticeViolation' +  '/runtime_data'

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
            # if(strategy == 'LlamaIndex'):
            #     index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'paragraph')
            # if(strategy == 'LlamaIndex-tree'):
            #     index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'tree')

            # if(llama_index_azure.file_exist(index_path) == False):#check index existence
            #     continue

            #index = llama_index_azure.load_index(index_path)

            #read metadata
            #paras = filtering.extract_paragraph_nodes(text)
            #tree_path = llama_index_azure.construct_tree_path(text_file, text_folder, tree_folder)
            #tree = filtering.read_tree_json(tree_path)

            st = time.time()
            size = 0

            response = [] 
            ans_flag = 1
            if(strategy == 'GPT_single'):
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'notice')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
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
                res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                size += sz
                if(res.lower() == 'false' or 'none' in res.lower()):
                    ans_flag = 0
                    #print('determined false')
            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'block')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'notice')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index, k=1)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break

            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, '', 'bool', 'notice')
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break

            elif(strategy == 'textdb_summary'):
                text_val = filtering.read_text(text_file)
                tree_path = tree_folder + '/tree_' + title
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'sentence')
                #print('tree path:')
                #print(tree_path)
                if(llama_index_azure.file_exist(tree_path) == False):#check index existence
                    #print('yes')
                    continue
                tree_val = filtering.read_tree_json(tree_path)
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    #print('yes')
                    continue
                index_val = llama_index_azure.load_index(index_path)
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', 'notice')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index_val, text = text_val, tree = tree_val, k=3)#sz: number of tokens used 
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
        
        #sql_version = 'sql' + str(sql_id+1) +'.txt'
        sql_version = 'sql' + str(sql_id+1) +'_gpt35.txt'
        
        #write result, time and size into local files
        path1 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/notice/times_' + strategy + '_' + sql_version
        query_interface.write_2_json(times, path1)

        path2 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/notice/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/notice/ans_' + strategy + '_' + sql_version
        query_interface.write_2_json(result, path3)

        #break

#seperate for different datasets since the projection is a little bit different 
def evaluate_SQL_paper(text_files):
    strategy = 'textdb_summary' #GPT_single, GPT_merge, LlamaIndex_seq, LlamaIndex_tree, textdb_summary 
    data = 'paper' #paper,civic,NoticeViolation
    entity_mention = 'paper' #natural language description of an entity 
    
    sqls = UDF_registration.paper_SQLs()#readl sqls

    if(data == 'paper'):
        desp = UDF_registration.paper_attr_desp()
    elif(data == 'civic'):
        desp = UDF_registration.civic_attr_desp()
    elif(data == 'NoticeViolation'):
        desp = UDF_registration.notice_attr_desp()
    
    for sql_id in range(4, len(sqls)):#scan each query 
        sql = sqls[sql_id]
        print('sql id:', sql_id+1)
        

        index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/' + data + '/index/'
        text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + data +  '/extracted_data'
        tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + data +  '/runtime_data'

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
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention)
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
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
                res, sz = evaluation.evaluate_udf(strategy, model, prompt, context = text)#sz: number of tokens used 
                print(res.lower(), sz)
                size += sz
                if(res.lower() == 'false' or 'none' in res.lower()):
                    ans_flag = 0
                    #print('determined false')
            elif(strategy == 'LlamaIndex_seq'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'block')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention)
                    print(left, right, prompt)

                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index, k=5)
                    print(str(res).lower(), sz)
                    size += sz
                    if('false' in str(res).lower() or 'none' in str(res).lower()):
                        ans_flag = 0
                        break

            elif(strategy == 'LlamaIndex_tree'):
                #read index 
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'tree')
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    continue
                index = llama_index_azure.load_index(index_path)

                filters = sql['filters']
                for key, prompt in filters.items():
                    #print(prompt)
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index)
                    #print(str(res).lower(), sz)
                    response.append(str(res))
                    size += sz
                    if(res.lower() == 'false'):
                        ans_flag = 0
                        break

            elif(strategy == 'textdb_summary'):
                index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper/paper_index_with_metadata_refined/'
                text_val = filtering.read_text(text_file)
                tree_path = tree_folder + '/tree_' + title
                index_path = llama_index_azure.construct_index_path(text_file, text_folder, index_folder, 'sentence')
                #print('tree path:')
                #print(tree_path)
                if(llama_index_azure.file_exist(tree_path) == False):#check index existence
                    #print('yes')
                    continue
                tree_val = filtering.read_tree_json(tree_path)
                #print(index_path)
                if(llama_index_azure.file_exist(index_path) == False):#check index existence
                    #print('yes')
                    continue
                index_val = llama_index_azure.load_index(index_path)
                
                for left, right in sql['filters'].items():#for each filter 
                    prompt = UDF_registration.get_predicate_prompt(left, right[0], right[1], desp, entity_mention, 'bool', 'paper')
                    print(left, right, prompt)
                    
                    res, sz = evaluation.evaluate_udf(strategy, model, prompt, index = index_val, text = text_val, tree = tree_val, k=3)#sz: number of tokens used 
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
                response.append(title)#project = paper name (title)
            else:
                print('false')

            result[title] = response
            sizes[title] = size
            times[title] = et-st

            #break
        
        sql_version = 'sql' + str(sql_id+1) +'.txt'
        
        #write result, time and size into local files
        path1 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/times_' + strategy + '_' + sql_version
        query_interface.write_2_json(times, path1)

        path2 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/sizes_' + strategy + '_' + sql_version
        query_interface.write_2_json(sizes, path2)

        path3 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/ans_' + strategy + '_' + sql_version
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


if __name__ == "__main__":
    data = 'NoticeViolation'
    text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + data + '/extracted_data'
    tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/' + data + '/runtime_data'

    text_files = model_build.scan_files(text_folder)
    evaluate_SQL_notice(text_files)
    #evaluate_SQL_paper(text_files)
    





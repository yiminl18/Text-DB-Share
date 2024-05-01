#this script evaluates per predicate and query
import sys
import os
import Levenshtein
import spacy
import llama_index_azure
import filtering
import json 
import pandas as pd
import UDF_registration
from nltk.tokenize import word_tokenize


# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
model_name = 'gpt4_long'

def evaluate_single_project(context, model, selected_attr, udfs):
    instruction = udfs[selected_attr]
    prompt = (instruction,context)
    response = model(model_name,prompt)
    return response

def context_size(context):
    return len(word_tokenize(context))

def evaluate_udf(strategy, model, question, context = None, index = None, block_map = None, text = None, tree = None, k = 5):
    if(strategy == 'GPT_single'):
        prompt = (question,context)
        response = model(model_name,prompt)
        return response, context_size(context)
    if(strategy == 'GPT_merge'):
        prompt = (question,context)
        response = model(model_name,prompt)
        return response, context_size(context)
    if(strategy == 'textdb'):
        context = filtering.return_context(question, block_map, index, text, tree, k)
        prompt = (question,context)
        response = model(model_name,prompt)
        return response, context_size(context)
    if(strategy == 'textdb_summary'):
        return filtering.tree_search_with_summary(tree, text,1,index,question,k)
    if(strategy == 'LlamaIndex_seq'):
        response, sz = llama_index_azure.semantic_search(index, question, k)
        return response, sz
    if(strategy == 'LlamaIndex_tree'):
        response, sz = llama_index_azure.tree_index_retrieve(index, question)
        return response, sz
    if(strategy == 'LlamaIndex_long'):
        context, sz = llama_index_azure.context_retrieve(index, k, question)
        long_context = llama_index_azure.get_llamaindex_long_context(context, text)
        prompt = (question,long_context)
        response = model(model_name,prompt)
        return response, context_size(long_context)
    

def evaluate_single_predicate(context, model, pred, udfs):
    udf = pred[0]
    operand = pred[2]
    instruction = udfs[udf]
    hint = ''#hint is used to control the format of response 
    if(operand.isdigit()):
        hint = 'Make sure the answer contains only a single number. '
    else:
        hint = 'Make sure the answer contains only a string. '
    instruction += hint
    prompt = (instruction,context)
    response = model(model_name,prompt)

    if(operand.isdigit()):
        left = convert_to_number(response)
        op = pred[1]
        if(op == '>' and left > operand):
            return 1, response
        if(op == '<' and left < operand):
            return 1, response
        if(op == '>=' and left >= operand):
            return 1, response
        if(op == '<=' and left <= operand):
            return 1, response
        if(op == '!=' and left != operand):
            return 1, response
        if(op == '<' and left < operand):
            return 1, response
        return 0, response
    else:
        left = response
        op = pred[1]
        if(op == 'approx'):#need to improve the robustness 
            if(operand.lower() in response.lower()):
                return 1, response
        return 0, response

def levenshtein_similarity(str1, str2):
    return Levenshtein.ratio(str1, str2)

def convert_to_number(s):
    try:
        # Try converting to integer
        return int(s)
    except ValueError:
        # If integer conversion fails, try converting to float
        try:
            return float(s)
        except ValueError:
            # If both conversions fail, return the original string
            return s



def read_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict



def read_csv(path):
    # Read the CSV file
    df = pd.read_csv(path) 
    return df

def find_truth(df, title, tag):
    for i in range(len(df)):
        if(df['title'][i] == title):
            return df[tag][i]
        
def evaluate_SQL_predicted(results, truths, SQL):
    #evaluate the SQL, the result is true or false
    accuracy = 0 
    precision = 0
    recall = 0
    F1 = 0
    recall_num = 0
    precision_num = 0
    udfs, tag_map, cols, keywords = UDF_registration.paper_udfs()
    evaluated_udf = 0

    for i in range(len(results)):#scan each file 
        title = results['title'][i]
        title = title.replace('/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data/', '', 1)
        title = title.replace('.txt', '')
        #print(title)

        predicated_result = 1
        truth_result = 1

        #get predicated_result
        for udf in SQL:
            evaluated_udf += 1
            udf_value = str(results[udf][i]).strip()
            
            tag = tag_map[udf][0]
            value = tag_map[udf][1]
            
            truth = find_truth(truths, title, tag) #truth is a list which consists of a set of labels 
            #print(udf, udf_value, value, tag, truth)
            if(udf_value == 'False'):
                predicated_result = 0
                break
            if(tag == 'year'):#year is special and need to be compared 
                if(str(udf_value) not in truth):
                    predicated_result = 0
                    break

        #get truth_result
        for udf in SQL:
            tag = tag_map[udf][0]
            value = tag_map[udf][1]
            truth = find_truth(truths, title, tag)
            if(value == 'yes'):
                if('none' in truth.lower() or 'neither' in truth.lower()):
                    truth_result = 0
                    break
            else:
                if(str(value) not in truth):
                    truth_result = 0
                    break
                # if(tag == 'year'):
                #     if(str(value) not in str(truth)):
                #         truth_result = 0
                #         break

        #print(predicated_result, truth_result)

        if(predicated_result == truth_result):
            accuracy += 1
            
        if(truth_result == 1 and predicated_result == 1):
            recall += 1
            precision += 1
            
        if(truth_result == 1):
            recall_num += 1

        if(predicated_result == 1):
            precision_num += 1

    if(precision_num == 0):
        precision = 0
    else:
        precision = precision/precision_num
    if(recall_num == 0):
        recall = 0
    else:
        recall = recall/recall_num
    accuracy /= len(results) 
    if(precision + recall == 0):
        F1=0
    else:
        F1 = 2*(precision*recall)/(precision+recall)
    return accuracy, precision, recall, F1, precision_num, recall_num, len(results), evaluated_udf

def get_results(result_path):
    results = read_csv(result_path)
    return results

def get_truths(truth_path):
    truths = read_csv(truth_path)
    return truths

if __name__ == "__main__":
    result_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_single.csv'
    truth_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/truth_tags.csv'
    SQL_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/SQLs.txt'
    results = get_results(result_path)
    truths = get_truths(truth_path)
    SQLs = read_json(SQL_path)
    
    print('accuracy, precision, recall, F1, number of positive results, number of truth results, total documents, average number of evaluated predicates')

    ans = []
    for id, sql in SQLs.items():
        accuracy, precision, recall, F1, precision_num, recall_num, size, evaluated_udf = evaluate_SQL_predicted(results, truths, sql)
        #print('SQL'+id, accuracy, precision, recall, F1, precision_num, recall_num, size, evaluated_udf)
        row = ['SQL'+id, precision, recall, F1, precision_num, recall_num, size, evaluated_udf]
        ans.append(row)
    
    cols = ['SQLID', 'precision', 'recall', 'F1', 'number of positive results', 'number of truth results', 'total documents', 'average number of evaluated predicates']

    df = pd.DataFrame(ans, columns = cols)
    df.to_csv('/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/plot/paper/GPT4_single_SQL_accuracy.csv')
    print(df)
        
#this script evaluates per predicate and query
import sys
import os
import Levenshtein
import spacy
import llama_index_openai
import filtering
import json 
import pandas as pd
import UDF_registration
from nltk.tokenize import word_tokenize


def context_size(context):
    return len(word_tokenize(context))

def evaluate_udf(strategy, model, model_name, question, context = None, index = None, block_map = None, text = None, tree = None, tuple_level = 1, parent = None, paras = None, k = 5):
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
        return filtering.tree_search_with_summary(tree,text,tuple_level,index,question,parent,paras, k)
    if(strategy == 'LlamaIndex_seq'):
        response, sz = llama_index_openai.semantic_search(index, question, k)
        return response, sz
    if(strategy == 'LlamaIndex_tree'):
        response, sz = llama_index_openai.tree_index_retrieve(index, question)
        return response, sz
    if(strategy == 'LlamaIndex_long'):
        context, sz = llama_index_openai.context_retrieve(index, k, question)
        long_context = llama_index_openai.get_llamaindex_long_context(context, text)
        prompt = (question,long_context)
        response = model(model_name,prompt)
        return response, context_size(long_context)
    

def evaluate_single_predicate(context, model, model_name, pred, udfs):
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
        

def get_results(result_path):
    results = read_csv(result_path)
    return results

def get_truths(truth_path):
    truths = read_csv(truth_path)
    return truths


        
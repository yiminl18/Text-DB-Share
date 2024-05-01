#this script is used to conduct pipeline to quickly test a candidate dataset 

from pdfminer.high_level import extract_text
import time
import os 
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar,LTLine,LAParams

import pdfreader
from pdfreader import PDFDocument, SimplePDFViewer
import time 
import sys 
import os
from nltk.tokenize import word_tokenize
# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def store_string_to_file(s, filename):
    with open(filename, 'w') as file:
        file.write(s)

def context_size(context):
    return len(word_tokenize(context))

def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
    return files 

def clean_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf', '')
    title = title.rsplit('.txt', 1)[0]
    return title 

#extract text data from pdf pipeline 
def pdf_2_text_pipeline(in_relative_path, out_relative_path):
    text_files = scan_files(in_relative_path)
    for i in range(len(text_files)): 
        print(i)
        #print(text_files[i])
        title = clean_title(text_files[i], in_relative_path)
        #print(paper_title)
        print(title)
        if('DS_Store' in title):
            continue

        text = extract_text_from_pdf(text_files[i])

        pdf_path = out_relative_path + title + '.txt'
        store_string_to_file(text, pdf_path)

def read_text(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
    return text

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def tree_table_content_by_gpt(read_path, write_path):
    tree = {}
    text = read_text(read_path)
    instruction = 'Give me table of content for the following document, which includes the header of each section and sub-section. Make sure the name of header are the original phrases in the document. Make sure the order of section are in the same order in the given document. Example: 1. Section1, 1.1 Section 1.1. '
    prompt = (instruction,text)
    response = model('gpt4_long',prompt)
    #print(response)
    write_file(write_path, response)

def sht_pipeline(text_path, run_time_path):
    text_files = scan_files(text_path)
    for i in range(len(text_files)): 
        
        if('DS_Store' in text_files[i]):
            continue
        #print(text_files[i])
        title = clean_title(text_files[i], text_path)
        print(i,title)
        #print(run_time_path)
        tree_table_content_by_gpt(text_files[i], run_time_path+title+'.txt')

def query_pipeline():
    #HR udfs 
    udf = {}
    # udf['master_degree'] = 'Does this position require master degree? Return yes or no. If the answer is not found, return no. '
    # udf['knowledge_software'] = 'Does this position require the knowledge of software? Return yes or no. If the answer is not found, return no.' 
    # udf['knowledge_Educational_Code'] = 'Does this position require the knowledge of educational code? Return yes or no. If the answer is not found, return no.' 
    # udf['ability_work'] = 'Does this position require to work with private agencies? Return yes or no. If the answer is not found, return no.' 
    # udf['work_place'] = 'Is this position\' working position in office? Return yes or no. If the answer is not found, return no.'
    
    #notice of violation udfs 
    udf['company'] = 'What is the name of company having the probable violations? Return name.'
    udf['date'] = 'What is the date when this notice is addressed? Return date.'
    udf['response_requirement_date'] = 'how many days are given to respond to the notice? Return the number of days.'
    udf['penalty_date'] = 'What is the maximum number of penalty if the violatons happened in 2023? Return the number.'
    udf['recommend_penalty'] = 'What is the recommend penalty in this notice? Return only the penalty number.'
    udf['violation_type'] = 'What are the violation types in this notice?'
    udf['violation_type_1'] = 'Does the violation relate with emergency response training? Return yes or no.'
    udf['violation_type_2'] = 'Does the violation relate with electrical isolation? Return yes or no.'
    udf['violation_type_3'] = 'Does the violation relate with corrosion control? Return yes or no.'
    udf['violation_order_1'] = 'Does the violations contain the violation order §195.403(b)(1)? Return yes or no.'
    udf['violation_order_2'] = 'Does the violations contain the violation order §195.452(f)? Return yes or no.'
    udf['violation_code'] = 'What is violation code in this notice? Return code.' 

    return udf 

def gpt(instruction,text,model_name):
    prompt = (instruction,text)
    start_time = time.time()
    response = model(model_name,prompt)
    end_time = time.time()
    print(response, context_size(text))

def construct_index_path(text_path, folder_path, index_folder_path, level):
    title = clean_title(text_path, folder_path)
    index_folder_path = index_folder_path + level + '_'
    return index_folder_path + title

def gpt_pipeline(query, text_path, model_name):
    text_files = scan_files(text_path)
    for i in range(len(text_files)): 
        
        if('DS_Store' in text_files[i]):
            continue
        print(i, text_files[i])
        text = read_text(text_files[i])
        for label, instruction in query.items():
            print(label)
            gpt(instruction, text, model_name)



if __name__ == "__main__":
    pdf_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/NoiceViolation/raw_data/'
    text_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoiceViolation/extracted_data/'
    run_time_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoiceViolation/runtime_data/'
    #pdf_2_text_pipeline(pdf_path, text_path)
    #sht_pipeline(text_path, run_time_path)
    query = query_pipeline()
    gpt_pipeline(query, text_path, 'gpt4_long')
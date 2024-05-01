#this script implements GPT-4 baseline


import model_build
from collections import OrderedDict
import os 
import sys
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize


# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 
model_name = 'gpt4_long'

def query_engine(text, question):
    prompt = (question,text)
    response = model(model_name,prompt)
    #print(response)
    return response

if __name__ == "__main__":
    pdf_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/raw_data'
    text_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data'
    tree_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/runtime_data'

    #generate paper data 
    text_files = model_build.scan_files(text_folder_paper)
    text_files[0] = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data/Expense Control: A Gamified, Semi-Automated, Crowd-Based Approach For Receipt Capturing.txt'
    print(text_files[0])
    #print(len(text))
    question = "What is the publication date of paper? Return the original sentences or paragraph in the document where you find the answer."
    text = model_build.read_text(text_files[0])
    query_engine(text, question)
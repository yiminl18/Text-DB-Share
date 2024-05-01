from llama_index import VectorStoreIndex
from llama_index import SimpleDirectoryReader
import model_build
import openai
import os
from llama_index import (
    VectorStoreIndex,
    get_response_synthesizer,
)
from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor
from nltk.tokenize import word_tokenize

path = '/Users/yiminglin/Documents/Codebase/config/openai/config_azure.txt'

# def read_key(path):
#     with open(path, 'r') as file:
#     # Iterate over each line in the file
#         content = file.read()
#         lines = content.split('\n')
#     return lines[0], lines[1], lines[2], lines[3]

# openai.api_type, openai.api_base, openai.api_version, openai.api_key = read_key(path)

#os.environ["OPENAI_API_KEY"] = ""

def load_data(text_file):
    reader = SimpleDirectoryReader(input_files=[text_file])
    return reader.load_data()

def build_index(text_file):
    data = SimpleDirectoryReader(input_files=[text_file]).load_data()
    return VectorStoreIndex.from_documents(data)

def text_retriever(index, question):
    retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=5,
    )
    nodes = retriever.retrieve(question)
    sz = 0
    for node in nodes:
        sz += len(word_tokenize(node.get_text()))
    #print(sz)
    return retriever, sz

def query(retriever, question):
    query_engine = RetrieverQueryEngine(
        retriever=retriever,)
    response = query_engine.query(question)
    return response


def semantic_search(question, index):
    #data = load_data(file)
    #index = build_index(data)
    retriever, sz = text_retriever(index, question)
    response = query(retriever, question)
    return response, sz



if __name__ == "__main__":
    pdf_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/raw_data'
    text_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data'
    tree_folder_paper = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/runtime_data'

    #generate paper data 
    text_files = model_build.scan_files(text_folder_paper)
    text_files[0] = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data/Steps, Choices and Moral Accounting: Observations from a Step-Counting Campaign in the Workplace.txt'
    print(text_files[0])
    #print(len(text))
    question = 'What is the publication year of this paper? Only return a single number.'
    response, sz = semantic_search(question, text_files[0])
    print(response, sz)


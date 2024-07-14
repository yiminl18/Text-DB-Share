from llama_index.legacy import GPTVectorStoreIndex, SimpleDirectoryReader, LLMPredictor
import model_build
from llama_index.legacy.retrievers import VectorIndexRetriever
from llama_index.legacy.query_engine import RetrieverQueryEngine
from nltk.tokenize import word_tokenize
from llama_index.legacy import Document
from llama_index.legacy import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.legacy.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.legacy import VectorStoreIndex, Document
from llama_index.legacy import get_response_synthesizer
from llama_index.legacy import TreeIndex
from llama_index.legacy.indices.tree import TreeSelectLeafEmbeddingRetriever
from llama_index.legacy import GPTTreeIndex,OpenAIEmbedding
import os
import os.path
import filtering
from llama_index.legacy.schema import TextNode, IndexNode
from llama_index.legacy import StorageContext, load_index_from_storage
from llama_index.legacy.llms import OpenAI

from llama_index.legacy import set_global_service_context

llm = OpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=256)
embed_model = OpenAIEmbedding()

service_context = ServiceContext.from_defaults(
    chunk_size=256, chunk_overlap=20,
    llm=llm,
    embed_model=embed_model
)

set_global_service_context(service_context)

def load_data(text_file):
    reader = SimpleDirectoryReader(input_files=[text_file])
    return reader.load_data()

def load_data_from_content(content):
    return Document(text=content) 

def build_index(text_file):
    data = SimpleDirectoryReader(input_files=[text_file]).load_data()
    return VectorStoreIndex.from_documents(data)

def build_index_from_document_tree(text_file):
    data = SimpleDirectoryReader(input_files=[text_file]).load_data()
    return TreeIndex.from_documents(data, show_progress = True)

def build_index_from_content(data):
    return VectorStoreIndex.from_documents(data)

def store_index(index, path):
    index.storage_context.persist(persist_dir=path)

def load_index(path):
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=path)

    # load index
    index = load_index_from_storage(storage_context)
    return index

def text_retriever(index, k, question, keyword = None):
    if(keyword is not None):
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=keyword[0], value=keyword[1])]
        )
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
            vector_store_query_mode="default",
            filters=filters,
            alpha=None,
            doc_ids=None,
        )
    else:
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
            vector_store_query_mode="default",
            alpha=None,
            doc_ids=None,
        )
    nodes = retriever.retrieve(question)
    sz = 0
    context_ans = ''
    #print('In llama_index, printing relevant context:')
    for node in nodes:
        context = node.get_text()
        sz += len(word_tokenize(context))
        #print(context)
        context_ans += context
    #print(sz)
    return retriever, sz, context_ans

def context_retrieve(index, k, question, keyword = None):
    if(keyword is not None):
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=keyword[0], value=keyword[1])]
        )
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
            vector_store_query_mode="default",
            filters=filters,
            alpha=None,
            doc_ids=None,
        )
    else:
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
            vector_store_query_mode="default",
            alpha=None,
            doc_ids=None,
        )
    nodes = retriever.retrieve(question)
    sz = 0
    context = []
    for node in nodes:
        text = node.get_text()
        sz += len(word_tokenize(text))
        context.append(text)
        #print(context)
    #print(sz)
    return context, sz

def get_llamaindex_long_context(context, text):
    paras = filtering.extract_paragraph_nodes(text)
    #return all the content starting from the first paragraph as the context 
    #print(len(context))
    if(len(context) == 0):
        return text
    start_para = context[0]
    id = -1
    for i in range(len(paras)):
        para = paras[i]
        if(para_sim(start_para, para) > 0.95):
            id = i
            break
    #print(start_para)
    #print('id=',id)
    if(id == -1):
        return text
    context = ''
    for i in range(id, len(paras)):
        context += paras[i]
    print('In llamaindex azure: get effective context!', len(word_tokenize(context)))
    return context

def para_sim(para1,para2):
    #print('-------',para1, para2)
    p1 = set(para1.split())
    p2 = set(para2.split())

    intersection = p1.intersection(p2)
    union = p1.union(p2)

    # Compute the Jaccard similarity
    if(len(union) == 0):
        return 0
    jaccard_similarity = len(intersection) / len(union)
    return jaccard_similarity

def query(retriever, question):
    query_engine = RetrieverQueryEngine(
        retriever=retriever, response_synthesizer=get_response_synthesizer())
    response = query_engine.query(question)
    return response

def query_keyword(index, question, keyword = None):
    if(keyword is not None):
        key = keyword[0]
        value = keyword[1]
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key=key, value=value)]
        )
        query_engine = index.as_query_engine(filters=filters)
    else:
        query_engine = index.as_query_engine()
    response = query_engine.query(question)
    return response

def semantic_search(index, question, k, keyword = None):
    retriever, sz, context = text_retriever(index, k, question, keyword)
    if(keyword is not None):
        response = query(retriever, question)
    else: 
        response = query(retriever, question)
    return response, sz

def read_text(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def construct_nodes_without_metadata(text): #blocks are a set of text blocks with same granularity (sentences or paragraphs)
    paras = filtering.extract_paragraph_nodes(text)
    return paras 

def construct_nodes_with_metadata(tree, text, level='sentence'):#blocks are a dict: {block, metadata dict}
    sentences, sec_map, paras, para_map = filtering.extract_blocks(tree, text)
    if(level == 'paragraph'):
        blocks = filtering.get_metadata_refined(para_map, tree)
    else:
        blocks = filtering.get_metadata_refined(sec_map, tree)
    nodes = []
    for block, meta in blocks.items():
        node = TextNode(
            text = block, 
            metadata = meta, #meta: {node_level: node_name}, e.g.,"metadata": {"2": "Phone Probes and Social Media Logs", "1": "Method"}
        )
        nodes.append(node)
    return nodes 

def build_index_from_nodes(nodes):
    index = VectorStoreIndex(nodes)
    return index 

def build_index_from_nodes_tree(nodes):
    index = TreeIndex(nodes)
    return index 

def clean_paper_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf.txt', '')
    title = title[1:] 
    title = title.replace('.txt', '')
    return title 

def construct_index_path(text_path, folder_path, index_folder_path, level):
    title = clean_paper_title(text_path, folder_path)
    index_folder_path = index_folder_path + level + '_'
    return index_folder_path + title

def construct_tree_path(text_path, folder_path, tree_folder):
    title = clean_paper_title(text_path, folder_path)
    title = title + '.txt'
    #print(title)
    tree_path = tree_folder + '/tree_' + title
    return tree_path

def index_exist(index_path):
    if os.path.exists(index_path) and os.path.isdir(index_path):
        return True
    return False

def file_exist(tree_path):
    if os.path.exists(tree_path):
        return True
    return False



def tree_index_retrieve(tree_index, question):
    retriever = TreeSelectLeafEmbeddingRetriever(tree_index)#This class traverses the index graph using the embedding similarity between the query and the node text.
    nodes = retriever.retrieve(question)
    sz = 0
    #print('In llama_index, printing relevant context:')
    for node in nodes:
        context = node.get_text()
        #print(context)
        sz += len(word_tokenize(context))
    response = query(retriever, question)
    return response, sz

def tree_retriever(text_file):
    data = SimpleDirectoryReader(input_files=[text_file]).load_data()
    index_light = GPTTreeIndex.from_documents(data, build_tree=False) #build_tree=False
    query_engine = index_light.as_query_engine(
        retriever_mode="all_leaf",
        response_mode='tree_summarize',
    )
    response = query_engine.query('What is the publication year of this paper? Only return a single number. If cannot find, return "None" .')
    print(response)

def udf_gen():
    #HR udfs 
    udf = {}
    # udf['master_degree'] = 'Does this position require master degree? Return yes or no. If the answer is not found, return no. '
    # udf['knowledge_software'] = 'Does this position require the knowledge of software? Return yes or no. If the answer is not found, return no.' 
    # udf['knowledge_Educational_Code'] = 'Does this position require the knowledge of educational code? Return yes or no. If the answer is not found, return no.' 
    # udf['ability_work'] = 'Does this position require to work with private agencies? Return yes or no. If the answer is not found, return no.' 
    # udf['work_place'] = 'Is this position\' working position in office? Return yes or no. If the answer is not found, return no.'
    
    #notice of violation udfs 
    # udf['company'] = 'What is the name of company having the probable violations? Return name.'
    # udf['date'] = 'What is the date when this notice is addressed? Return date.'
    # udf['response_requirement_date'] = 'how many days are given to respond to the notice? Return the number of days.'
    # udf['penalty_date'] = 'What is the maximum number of penalty if the violatons happened in 2023? Return the number.'
    # udf['recommend_penalty'] = 'What is the recommend penalty in this notice? Return only the penalty number.'
    # udf['violation_type'] = 'What are the violation types in this notice?'
    # udf['violation_type_1'] = 'Does the violation relate with emergency response training? Return yes or no.'
    # udf['violation_type_2'] = 'Does the violation relate with electrical isolation? Return yes or no.'
    # udf['violation_type_3'] = 'Does the violation relate with corrosion control? Return yes or no.'
    # udf['violation_order_1'] = 'Does the violations contain the violation order §195.403(b)(1)? Return yes or no.'
    # udf['violation_order_2'] = 'Does the violations contain the violation order §195.452(f)? Return yes or no.'
    # udf['violation_code'] = 'What is violation code in this notice? Return code.' 
    udf['publication_date'] = 'What is the publication year of this paper? Only return a single number. If cannot find, return "None" .'

    return udf 

def query_pipeline(udf, text_folder, index_folder, type):#run query for a set of files 
    text_files = model_build.scan_files(text_folder)
    i = 0
    for text_file in text_files:
        print(i, text_file)
        
        index_path = construct_index_path(text_file, text_folder, index_folder, type)
        i+=1
        print(index_path)
        index = load_index(index_path)
        for label, instruction in udf.items():
            print(label)
            if(type == 'block'):
                response, sz = semantic_search(index, instruction, 5)
            elif(type == 'tree'):
                response, sz = tree_index_retrieve(index, instruction)
            print(response, sz)
        break

def index_pipeline(text_folder, index_folder, tree_folder, type):#build index for a set of files 
    text_files = model_build.scan_files(text_folder)
    i = 0
    for text_file in text_files:
        print(i, text_file)
        #tree_retriever(text_file)
        index_path = ''
        
        if(type == 'block'):
            index_path = construct_index_path(text_file, text_folder, index_folder, type)
            index = build_index(text_file)
        elif(type == 'tree'):
            index_path = construct_index_path(text_file, text_folder, index_folder, type)
            index = build_index_from_document_tree(text_file)
        elif(type == 'meta'):
            index_path = construct_index_path(text_file, text_folder, index_folder, 'sentence')
            tree_path = construct_tree_path(text_file, text_folder, tree_folder)
            #print(index_path)
            if(file_exist(index_path)):
                #print('yes')
                continue
            text = read_text(text_file)
            tree = filtering.read_tree_json(tree_path)
            nodes = construct_nodes_with_metadata(tree, text, 'sentence')
            index = build_index_from_nodes(nodes)
        store_index(index, index_path)
        i+=1
        #break



def get_root_path():
    current_path = os.path.abspath(os.path.dirname(__file__))
    parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
    #print("Parent path:", parent_path)
    return parent_path

if __name__ == "__main__":

    root_path = get_root_path()
    text_folder = root_path + '/data/paper/extracted_data'
    tree_folder = root_path + '/data/paper/runtime_data'
    index_folder = root_path + '/index/paper/index/'


    # #for civic data 
    # text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/extracted_data'
    # tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/runtime_data'
    # index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/civic/index/'

    # #for NoiceViolation data 
    # text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/extracted_data'
    # tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/runtime_data'
    # index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/NoticeViolation/index/'


    


from llama_index import ServiceContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index import VectorStoreIndex
from llama_index.retrievers import VectorIndexRetriever
from nltk.tokenize import word_tokenize

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
        print(node.get_text())
        sz += len(word_tokenize(node.get_text()))
    #print(sz)
    return retriever, sz

def run_embed(embed_model, file_path):
    

    service_context = ServiceContext.from_defaults(embed_model=embed_model, llm=None)
    # Optionally set a global service context to avoid passing it into other objects every time
    from llama_index import set_global_service_context

    set_global_service_context(service_context)

    # index = build_index('data/sys review/extracted_data/A Lived Informatics Model of Personal Informatics.txt')
    index = build_index(file_path)
        
    question = 'What is the publication year of this paper? Only return a single number. If cannot find, return "None" .'

    return text_retriever(index, question)


def embedding(model_name, file_path):
    if(model_name is 'langchain'): # requires pip install sentence_transformers
        from langchain.embeddings.huggingface import HuggingFaceBgeEmbeddings
        embed_model = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en")
        return run_embed(embed_model, file_path)
    if(model_name is 'hugging'):
        from langchain.embeddings import HuggingFaceEmbeddings
        embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        return run_embed(embed_model, file_path)
    if(model_name is 'fastembed'): # requires pip install fastembed
        from llama_index.embeddings import FastEmbedEmbedding
        embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return run_embed(embed_model, file_path)
    return 'input model does not exist'

# file_path = 'data/sys review/extracted_data/A Lived Informatics Model of Personal Informatics.txt'
# model_name = 'fastembed'
# embedding(model_name, file_path)
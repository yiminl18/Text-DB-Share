import json
import requests
import os 
import pandas as pd
def write_2_json(tree, dict_path):
    with open(dict_path, 'w') as file:
        json.dump(tree, file)


def download_pdf(url, path, name):
    response = requests.get(url)
    filename = path + name
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded '{filename}' successfully.")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

def get_clusters():
    # Path to the JSON file
    file_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/cluster_map.json'

    # Load and parse the JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)

    clusters = {}

    for cluster in data:
        title = cluster['title']
        tags = cluster['clusters']
        clusters[title] = tags

    return clusters


def get_label(paper, clusters, question_tag):#question_tag: "domain", "contribution",...
    tags = paper["tags"]
    labels = clusters[question_tag]

    ans = []
    for tag in tags:
        if(tag in labels):
            ans.append(tag)
    return ans
    #return "NULL"

def get_paper_data(): 
    # Path to the JSON file
    file_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/all_papers.json'

    # Load and parse the JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Extracting column names and values for each paper
    extracted_data = []
    for doi, details in data.items():
        paper_data = {"DOI": doi}
        paper_data.update(details)
        extracted_data.append(paper_data)

    return extracted_data

def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
        # # Check if it's a file or directory
        # if os.path.isfile(full_path):
        #     print(f"File: {full_path}")
        # elif os.path.isdir(full_path):
        #     print(f"Directory: {full_path}")
    return files

def dowaload_all_papers(papers):
    write_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper/paper/'

    extracted_data = get_paper_data()

    for i in range(len(extracted_data)):
        if("true_link" in extracted_data[i]):
            true_link = extracted_data[i]["true_link"]
            title = extracted_data[i]["title"]
            title = title + '.pdf'
            print(i,title, true_link)
            if(title in papers or 'Toward Health Information Technology That Supports Overweight' in title):
                print(i)
                continue
            download_pdf(true_link, write_path, title)

def read_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def get_truths():
    extracted_data = get_paper_data()
    clusters = get_clusters()
    question_tag = ['venue','source','domain','health_wellness','li','motivation','lived_informatics','privacy&ethics','privacy_ethics_depth','contribution','study','artifact_kind','recruitment','participant_count','study_duration','involved','demographics','expert','expert_description','theory','theory_depth']
    truths = {}
    for i in range(len(extracted_data)):
        if("true_link" in extracted_data[i]):
            title = extracted_data[i]["title"]
            year = extracted_data[i]["year"]
            author = extracted_data[i]["author"]
            venue = extracted_data[i]["venue"]
            source = extracted_data[i]["source"]
            truth = {}
            truth['title'] = [str(title)]
            truth['year'] = [str(year)]
            truth['author'] = [str(author)]
            author_number = str(author).count(',')+1
            truth['author_number'] = [author_number]
            truth['venue'] = [str(venue)]
            truth['source'] = [str(source)]
            for tag in question_tag:
                label = get_label(extracted_data[i], clusters, tag)
                # if(len(label) > 1):
                #     print('more than one labels', title, tag, label)
                truth[tag] = label
                
            truths[title] = truth
    out_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/truths.csv'
    write_2_json(truths, out_path)

    return truths

def truth_2_df(truths):
    question_tag = ['venue','author_number','source','theory','year','contribution','privacy&ethics','study','health_wellness','domain','artifact_kind','demographics']
    i = 0
    rows = []
    for paper in papers:
        row = []
        paper = paper.replace('.pdf', '',1)
        print(paper)
        
        if(paper not in truths):
            continue
        i+=1
        #print(i)
        row.append(paper)
        for tag in question_tag:
            print(truths[paper][tag])
            row.append(truths[paper][tag])
        rows.append(row)
        #if(i>=50):


    cols = ['title']
    cols.extend(question_tag)
    #print(cols)
    df = pd.DataFrame(rows, columns=cols)

    # Print the DataFrame to see the result
    #print(df)
    df.to_csv('/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/truth_tags.csv')


downloaded_pdfs = scan_files('/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper/paper/')
papers = [] #these are papers that have been already downloaded 
for paper in downloaded_pdfs:
    paper = paper.replace('/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper/paper/', '', 1)
    papers.append(paper)
#print(papers)

#try to download all the papers except for those already downloaded papers
#dowaload_all_papers(papers)
truths = get_truths()

#generate ground truth for the downloaded papers 
truth_2_df(truths)


#this script is to generate ground truth for civic data set by using LLM and to be verified by humans 
import os 
import sys 
# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
sys.path.append(parent_directory+'/execution')
#print(parent_directory)
import filtering 
import UDF_registration
from model import model 
import json 
from datetime import datetime
import pandas as pd

def write_2_json(dict, dict_path):
    with open(dict_path, 'w') as file:
        json.dump(dict, file)

def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
    return files 

def read_text(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
    return text

def get_truth(tree, text, title):
    truth = {}
    #meeting_date_instruction = 'Return the meeting date of this document in the given format. Example: 2021-04-28.'
    type = '' #disaster or capitol improvement
    status = '' #complete, not started, design, construction
    labels = {}
    for id, node in tree.items():
        if(node['level'] > 2):
            continue

        if(node['level'] == 1):
            name = node['name']
            #set up status 
            if('(Design)'.lower() in name.lower()):
                status = 'design'
            elif('(Construction)'.lower() in name.lower()):
                status = 'construction'
            elif('(Not Started)'.lower() in name.lower()):
                status = 'not started'
            elif('(Completed)'.lower() in name.lower()):
                status = 'completed'
            else:
                status = 'none' 
            #set up type 
            if('Capital'.lower() in name.lower()):
                type = 'capital'
            elif('Disaster'.lower() in name.lower()):
                type = 'disaster'
            else:
                type = 'none'
            labels = {}
            labels['type'] = type
            labels['status'] = status
        else:
            name = node['name']
            #labels from LLMs
            st_instruction = 'Return the begin construction time of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
            et_instruction = 'Return the complete design time or completion of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
            ad_instruction = 'Return the advertise time of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
            topic_instruction = 'Return several words to describe the related topics of this project. Example: health, road, water, park, vehicle, storm'

            begin = 'Based on the given description of a project, answer the following 4 questions in order. The answer of each question is in a new line. '
            instruction = begin + st_instruction + et_instruction + ad_instruction + topic_instruction
            context = filtering.get_context_for_coarse_node(name,2,tree,text)
            #print(context)
            #print('')
            prompt = (instruction,context)
            response = model('gpt4_azure',prompt)
            new_labels = parse_response(response, {})
            new_labels['type'] = labels['type']
            new_labels['status'] = labels['status']
            print(name)
            print(response)
            truth[name] = new_labels
    write_2_json(truth, '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/labeled_data/' + title)
            #break
        
def parse_response(response, labels):
    lines = response.split('\n')
    if(len(lines) != 4):
        labels['value'] = 'error'
        return labels
    st = lines[0]
    et = lines[1]
    ad = lines[2]
    topic = lines[3]
    labels['st'] = st
    labels['et'] = et
    labels['ad'] = ad
    labels['topic'] = topic
    return labels

def read_tree_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def clean_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf', '')
    #title = title[1:] 
    title = title 
    return title 

def file_exist(tree_path):
    if os.path.exists(tree_path):
        return True
    return False

def truth_gen_for_query_Civic():
    sqls = UDF_registration.civic_SQLs()
    label_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/labeled_data/'
    text_files = scan_files(label_folder)
    i=0
    for sql in sqls: 
        filters = sql['filters']
        print(i)
        print(filters)
        result = {}
        ans = []
        
        for text_file in text_files:#iterate all document 
            #print(text_file)
            title = clean_title(text_file, label_folder)
            print(title)
            ans = []
            if('DS_Store' in text_file):
                continue

            labels = read_tree_json(text_file)
            for name, label in labels.items():#iterate all project 
                is_ans = 1
                for udf, val in filters.items():#check all predicates 
                    left_val = label[udf]
                    right_val = val[1]
                    op = val[0]
                    if(predicate_eval_civic(left_val, op, right_val) == False):#if it is false
                        is_ans = 0
                        break
                if(is_ans == 1):
                    #print('ans is:', name, label['et'], label['type'], label['status'])
                    ans.append(name)
            result[title] = ans
        i+=1
        file_name = 'truth_sql_ver1' + str(i) + '.txt'
        write_2_json(result, '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/civic/' + file_name)
        #break

        

def truth_gen_for_udfs():
    #generate truths for all udfs 
    sqls = UDF_registration.civic_SQLs()
    label_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/labeled_data/'
    text_files = scan_files(label_folder)
    sql = sqls[0]
    filters = sql['filters']
    print(filters)
    result = {}
    ans = []
    
    for text_file in text_files:#iterate all document 
        print(text_file)
        ans = []
        if('DS_Store' in text_file or 'truth_sql1' in text_file):
            continue

        labels = read_tree_json(text_file)
        ans = []
        for udf, val in filters.items():#check all predicates 
            res = ''
            for name, label in labels.items():#iterate all project 
                left_val = label[udf]
                right_val = val[1]
                op = val[0]
                if(predicate_eval_civic(left_val, op, right_val) == True):#if it is false
                    res += name + ','
            ans.append(res[:-1])
        result[text_file] = ans
        #break

    # print(ans)
    # print(len(ans))
    
    write_2_json(result, '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/civic/truth_sql1_udfs.txt')

def truth_gen_for_query_paper():
    sqls = UDF_registration.paper_SQLs()
    label_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/truths.csv'
    labels = read_tree_json(label_path)
    i = 0

    for sql in sqls:
        filters = sql['filters']
        result = {}

        for title, label in labels.items():#scan all documents 
            ans = 0
            for label_name, condition in filters.items():#check each filter 
                op = condition[0]
                right = condition[1]#a single value 
                left = label[label_name]#a list of values 
                if(predicate_eval_paper(left,op,right) == False):
                    ans = 1
                    break
            file_name = title + '.txt'
            if(ans == 1):
                result[file_name] = []
            else:
                result[file_name] = [file_name]

        i+=1
        file_name = 'truth_sql_ver' + str(i) + '.txt'
        write_2_json(result, '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/paper/labeled_data/' + file_name)

def compare_times(time1, time2):
    # Dictionary to map seasons to months, assuming the start month of the season
    seasons_to_months = {
        "winter": "12",  # Assuming winter starts in December
        "spring": "03",  # Spring starts in March
        "summer": "06",  # Summer starts in June
        "fall": "09"     # Fall starts in September
    }

    # Function to convert season to its starting month
    def season_to_month(time):
        year, part = time.split("-")
        if part in seasons_to_months:
            part = seasons_to_months[part]
        return f"{year}-{part}"

    # Convert seasons to months for comparison
    #print(time1,time2)
    converted_time1 = season_to_month(time1)
    converted_time2 = season_to_month(time2)

    # Compare and return the later time
    return time2 if converted_time2 > converted_time1 else time1
    
def predicate_eval_paper(left, op, right):
    #left: a list of values 
    #right: a single value 
    #print(left, op ,right)
    if(op == '='):
        for val in left:
            if(val.lower() in right.lower()):
                #print('true')
                return True
        #print('false')
        return False
    if(op == '>'):
        val = int(left[0])
        right = int(right)
        if(val > right):
            #print('true')
            return True
        #print('false')
        return False
    if(op == '<'):
        val = int(left[0])
        right = int(right)
        if(val < right):
            #print('true')
            return True
        #print('false')
        return False
    
    #print('false')
    return False

def predicate_eval_notice(left, op, right):
    #left: a list of values 
    #right: a single value 
    #print(left, op ,right)
    if(op == '='):
        for val in left:
            
            if(type(val) == bool):
                if(val == True and right.lower == 'true'):
                    return True
            else:
                val = val.lower()
                right = right.lower()
                if('or' in right): 
                    l = right.split('or')[0].strip()
                    r = right.split('or')[1].strip()
                    if(l in val or r in val):
                        #print(l,r,val)
                        return True
                    return False
                else:
                    if(right in val):
                        return True
        #print('false')
        return False
    if('/' not in right): #not a date
        if(op == '>'):
            val = int(left[0])
            right = int(right)
            if(val > right):
                #print('true')
                return True
            #print('false')
            return False
        if(op == '<'):
            val = int(left[0])
            right = int(right)
            if(val < right):
                #print('true')
                return True
            #print('false')
            return False
    else: #date
        val = str(left[0])
        if(op == '>'):
            if(compare_date(val, right) == True):
                return True
            return False
        if(op == '<'):
            #print(val, right, compare_date(val, right))
            if(compare_date(val, right) == False):
                return True
            return False

    
    #print('false')
    return False

def compare_date(date1, date2):
    # Date strings
    # date_str1 = '01/01/2021'  # Assuming 'yy' means two-digit year
    # date_str2 = '08/01/2023'

    # Convert to datetime objects
    date1 = datetime.strptime(date1, '%m/%d/%Y')
    date2 = datetime.strptime(date2, '%m/%d/%Y')

    if(date1 > date2):
        return True
    return False

def predicate_eval_civic(left, op, right):
    #print(left,op,right)
    if(op == '='):
        if(left.lower() == right.lower()):
            #print('true')
            return True
        if('road' in left.lower()):
            #print('road')
            return True
        #print('false')
        return False
    if('-' not in left or '-' not in right or 'none' in left.lower() or 'unknown' in left.lower()):
        #print(left, right) 
        #print('false')
        return False
    val = compare_times(left, right)
    
    if(op == '<' and val == right):
        #print('true')
        return True

    if(op == '>' and val == left):
        #print('true')
        return True
    
    #print('false')
    return False

def truth_gen_for_notice():
    #output format: {file_name: {labels}}, labels: {label_name: [vals]}
    #read truth 
    violation_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/NoticeViolation/ground_truth/violation.csv'
    item_truths = pd.read_csv(violation_path)
    global_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/NoticeViolation/ground_truth/global.csv'
    doc_truths = pd.read_csv(global_path)

    #doc_id,file_name,company,date,region,state,proposed_civil_penalty,num_proposed_items,has_proposed_compliance_order,has_proposed_civil_penalty,has_warning

    #doc_id,item_id,code_id,name,subject

    #below is target labels to extract
    labels = {}
    labels['doc_id'] = 'doc_id'
    labels['region'] = 'region'
    labels['state'] = 'state'
    labels['proposed_civil_penalty'] = 'penalty'
    labels['subject'] = 'type'
    labels['num_proposed_items'] = 'item_num'
    labels['date'] = 'date'
    labels['has_proposed_compliance_order'] = 'compliance_order'

    truths = {}

    #process violation truth
    
    #merge subject for each doc
    # Group by 'doc_id' and aggregate the unique 'subject' for each 'doc_id'
    distinct_subjects = item_truths.groupby('doc_id')['subject'].unique().reset_index()

    # Convert the array of subjects to a comma-separated string
    distinct_subjects['subject'] = distinct_subjects['subject'].apply(lambda x: ', '.join(x))

    # Rename the column to match the specified header (if necessary, but it was already correct in this case)
    new_items = distinct_subjects.rename(columns={'subject': 'subject'})

    #print(new_items[new_items['doc_id'] == 1]['subject'])

    #process doc truth
    for index, row in doc_truths.iterrows():#scan each row in doc truth
        file_name = row['file_name']
        doc_id = row['doc_id']
        subject = str(new_items[new_items['doc_id'] == doc_id].iloc[0]['subject'])
        #print(file_name, doc_id, subject)
        #print(file_name)
        vals = {}
        vals['type'] = [subject]
        
        for label, target_label in labels.items():
            if label in doc_truths.columns:
                vals[target_label] = [row[label]]
        #print(file_name)
        truths[file_name] = vals
    #print(truths)
    write_2_json(truths,'/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/labeled_data/truths.txt')
    
    
def truth_gen_for_notice_query():
    sqls = UDF_registration.notice_SQLs()
    label_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/labeled_data/truths.txt'
    labels = read_tree_json(label_path)
    i = 0

    for sql in sqls:
        filters = sql['filters']
        result = {}

        for title, label in labels.items():#scan all documents 
            ans = 0
            for label_name, condition in filters.items():#check each filter 
                op = condition[0]
                right = condition[1]#a single value 
                left = label[label_name]#a list of values 
                print(left, op, right)
                print(predicate_eval_notice(left,op,right))
                if(predicate_eval_notice(left,op,right) == False):
                    ans = 1
                    break
            file_name = title + '.txt'
            if(ans == 1):#no answer
                result[file_name] = ["false"]
            else:
                result[file_name] = ["true"]

        i+=1
        file_name = 'truth_sql' + str(i) + '.txt'
        write_2_json(result, '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/labeled_data/' + file_name)
    



if __name__ == "__main__":

    #for civic data 
    text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/extracted_data'
    tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/runtime_data'
    index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/civic/index/'
    label_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/labeled_data/'

    text_files = scan_files(text_folder)
    

    # i = 0
    # for text_file in text_files:
        
    #     if('DS_Store' in text_file):
    #         continue
    #     tree_path = llama_index_azure.construct_tree_path(text_file, text_folder, tree_folder)
    #     tree = filtering.read_tree_json(tree_path)
    #     text = read_text(text_file)
    #     paper_title = clean_title(text_file, text_folder)

        
    #     label_path = label_folder + paper_title
    #     print(i, paper_title)
    #     if(file_exist(label_path)):
    #         #print('path exist:', label_path)
    #         continue
    #     print('new path:', paper_title)
    #     #generate truth for each document 
    #     #get_truth(tree,text,paper_title)
    #     i += 1
        #break

    #generate the ground truth for civic SQLs
    #truth_gen_for_notice()
    truth_gen_for_notice_query()

    #generate the ground truth for paper SQLs
    #truth_gen_for_query_paper()
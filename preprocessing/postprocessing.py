#this script implements several postprocessing 
import os 
import json 
def reduce_extra_white_space(str):
    corrected_string = ' '.join(str.split())
    return corrected_string

def read_tree_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def reduce_white_space_file(text, path):
    new_text = ''
    with open(text, 'r') as file:
        # Read each line in the file
        for line in file:
            # Process the line
            if(line == '\n'):
                #print('**',line)
                new_text += line
                continue
            line = line.strip()
            line = reduce_extra_white_space(line)
            line += '\n'
            new_text += line
    #file_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/extracted_data/test.txt'
    with open(path, 'w') as file:
        file.write(new_text)

def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
    return files 

def clean_civic_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf.txt', '')
    #title = title[1:] 
    title = title.rsplit('.txt', 1)[0]
    return title 

def write_2_json(tree, dict_path):
    with open(dict_path, 'w') as file:
        json.dump(tree, file)

def transform(val, part):
    # Splitting the string into two parts
    parts = val.split()
    # Reformatting as 'Year-Season'
    return parts[1] + '-' + part


def format_single_value(val):
    seasons = ['spring','summer','fall','winter']
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    months_id = ['01','02','03','04','05','06','07','08','09','10','11','12']
    for season in seasons:
        if(season.lower() in val.lower() and '-' not in val):
            new_val = transform(val, season)
            return new_val
    
    for i in range(len(months)):
        month = months[i]
        id = months_id[i]
        if(month.lower() in val.lower() and '-' not in val):
            new_val = transform(val, id)
            return new_val
    return val 

def format_truth(truth_path, out_path):
    #format ground truths 
    truth = read_tree_json(truth_path)

    for name, labels in truth.items():
        for key, value in labels.items():
            #print(name, key, value) 
            truth[name][key] = format_single_value(value)

    write_2_json(truth, out_path)


if __name__ == "__main__":

    #for civic data 
    text_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/extracted_data'
    tree_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/runtime_data'
    index_folder = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/civic/index/'
    label_folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/civic/labeled_data/'
    new_folder = '/Users/yiminglin/Desktop/refined_text/'

    text_files = scan_files(label_folder)
    

    i = 0
    for text_file in text_files:
        
        if('DS_Store' in text_file):
            continue

        title = clean_civic_title(text_file, label_folder)
        title += '.txt'
        out_path = '/Users/yiminglin/Desktop/backup/labels/' + title
        print(title)
        print(text_file)
        print(out_path)
        format_truth(text_file,out_path)
        #break


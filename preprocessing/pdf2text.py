from pdfminer.high_level import extract_text
import time
import os 
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar,LTLine,LAParams

import pdfreader
from pdfreader import PDFDocument, SimplePDFViewer


def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def store_string_to_file(s, filename):
    with open(filename, 'w') as file:
        file.write(s)

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

def customize(original_string):
    return  'malibucity_agenda_' + original_string.split(':')[-1].replace('(dragged)','').strip()


#file_name = '/Users/yiminglin/Desktop/test/raw_pdf/malibu03222023-2060 (dragged).pdf'
in_relative_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/NoticeViolation/raw_data/'
out_relative_path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/NoticeViolation/extracted_data/'

text_files = scan_files(in_relative_path)

for i in range(len(text_files)): 
    print(i)
    #print(text_files[i])
    paper_title = clean_title(text_files[i], in_relative_path)
    
    if('DS_Store' in paper_title):
        continue
    print(paper_title)
    #break 

    text = extract_text_from_pdf(text_files[i])

    pdf_path = out_relative_path + paper_title + '.txt'
    store_string_to_file(text, pdf_path)
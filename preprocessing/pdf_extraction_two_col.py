import fitz  # Import PyMuPDF
import os 


def clean_paper_title(paper_path, folder_path):
    # Remove the substring
    title = paper_path.replace(folder_path, '', 1)
    title = title.replace('.pdf.txt', '')
    title = title.replace('.pdf', '')
    return title 

def extract_pdf(pdf_path):
    out = ''
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text('blocks') 
            for block in text:
                out += block[4] + '\n'
    return out 
        
def scan_files(folder_path):
    # List all files and directories in the given folder
    files = []
    for entry in os.listdir(folder_path):
        # Create the full path
        full_path = os.path.join(folder_path, entry)
        files.append(full_path)
    return files 

pdf_folder_paper = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper/'
text_folder_paper = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/paper_extracted/'

#generate paper data 
pdf_files = scan_files(pdf_folder_paper)

for i in range(len(pdf_files)):
    print(i)
    if(i == 7 or i == 67):
        continue

    paper_title = clean_paper_title(pdf_files[i], pdf_folder_paper)
    print(paper_title)

    out_path = text_folder_paper + '/' + paper_title + '.txt'

    out = extract_pdf(pdf_files[i])
    with open(out_path, 'w') as file:
        file.write(out)

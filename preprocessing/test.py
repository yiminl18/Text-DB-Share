
import time 
import sys 
import os

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_directory = os.path.dirname(current_file_directory)
sys.path.append(parent_directory)
from model import model 

instruction  = """If following document provide description about one CONSENT CALENDAR? Return yes. If following document provide description about multiple CONSENT CALENDAR return no.  

A.  Resolution to approve travel/education expenses for Councilwoman
     Henry – Mayor Marks

B.  Resolution to approve travel/education expenses for personnel of the
     Cemetery, Parks and Recreation Department – Bert Bradford, CPR
     Director

C.  Resolution to approve travel/education expenses for personnel of the
     Gas Department – Braxton Guinn, Gas Department Manager
D.  Resolution to approve travel/education expenses for personnel of the

     Water Services Department – Jimmy Junkin, Director of Water Services

E.  Resolution to approve the purchase of a 2024 International Flatbed
     Truck MV607 for the Gas Services Department – Braxton Guinn, Gas
     Department Manager

F.  Resolution to approve the purchase of a tractor mower boom brush
     with winch capacity and rotary boom mounted cutter for the
     Sanitation Department – Bernard Hammonds, Sanitation Department
     Director """ 

def read_text(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text
text = """Capital Improvement Projects (Design)

Marie Canyon Green Streets
(cid:190) Updates:

(cid:131) A hydrology report was prepared and will be used to size the pre-
manufactured biofilters. City staff is reviewing multiple biofilter
manufacturers for filters that will work in the proposed project area. It is
anticipated to have a final design by March 2022. The project will be
advertised for construction bids shortly after this date.

"""
#text = read_text('/Users/yiminglin/Desktop/test/sample_extracted_data/https:www.opelika-al.gov:AgendaCenter:ViewFile:Agenda:_05252021-147.txt')
model_name = 'gpt35_azure'


prompt = (instruction,text)
start_time = time.time()
response = model(model_name,prompt)
end_time = time.time()
print(response, end_time-start_time)
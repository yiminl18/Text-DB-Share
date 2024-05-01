import requests

pdf_url = 'https://dl.acm.org/doi/pdf/10.1145/3292147.3292193'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

response = requests.get(pdf_url, headers=headers)

write_path = '/Users/yiminglin/Documents/Codebase/Dataset/textdb/test.pdf'

if response.status_code == 200:
    with open(write_path, 'wb') as file:
        file.write(response.content)
else:
    print(f"Failed to retrieve the PDF: Status code {response.status_code}")

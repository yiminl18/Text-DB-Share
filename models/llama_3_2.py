import ollama


def llama_3_2_api(message_content):
    response = ollama.chat(
    model="llama3.2", 
    messages=[{"role": "user", "content": message_content}])

    return response['message']['content']

def llama_3_2(prompt):
    message_content = prompt[0] + prompt[1]
    return llama_3_2_api(message_content)


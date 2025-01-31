import ollama


def deepseek_api(message_content,temperature=0):
    response = ollama.chat(
    model="deepseek-r1:1.5b", 
    messages=[{"role": "user", "content": message_content}],
    temperature = temperature)

    return response['message']['content']

def deepseek_1_5(prompt):
    message_content = prompt[0] + prompt[1]
    return deepseek_api(message_content)


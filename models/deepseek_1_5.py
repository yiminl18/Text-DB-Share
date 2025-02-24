import ollama
import re

def deepseek_api(message_content):
    response = ollama.chat(
    model="deepseek-r1:1.5b", 
    messages=[{"role": "user", "content": message_content}])
    out = response['message']['content']
    return drop_think_from_deepseek(out)

def drop_think_from_deepseek(response):
    cleaned_response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
    return cleaned_response

def deepseek_1_5(prompt):
    message_content = prompt[0] + prompt[1]
    return deepseek_api(message_content)


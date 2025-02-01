from flask import Flask, request, jsonify
import ollama
from flask_cors import CORS  
import argparse
import logging

app = Flask(__name__)
CORS(app)  
model_name = 'llama3.2'

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message', '')
    elif request.method == 'GET':
        user_message = request.args.get('message', '')

    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    #llama3.2
    #deepseek-r1:1.5b
    logging.info(f"Model {model_name} is being used!")
    try:
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": user_message}])
        return jsonify({'response': response['message']['content']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A script that accepts command-line parameters.")
    parser.add_argument('--model', type=str, required=True, help='The type of supported local model can be one of [llama3.2, deepseekR1-1.5b].')
    args = parser.parse_args()
    model_name = args.model

    app.run(host='0.0.0.0', port=9000, debug=True)
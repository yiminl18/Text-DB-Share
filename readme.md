### Load OpenAI API 

Store your OpenAI API in by using 'export OPENAI_API_KEY="your-api-key-here"' or set the OpenAI API key as an environment variable in your system log. 

### Execute the following command line to run the code. 

Command: "python execution/main.py --data [data] --strategy [strategy] --model [model]"

[data] is one of [paper, civic, NoticeViolation]

[strategy] is one of [GPT_single, GPT_merge, Graph_RAG, LlamaIndex_seq, LlamaIndex_tree, textdb_summary]

[model] is one of [gpt4o, gpt4omini, deepseekR1-1.5b]

If you want to run deepseekR1-1.5b, first run "flask_server.py" locally, and then execute the above command. 
### Load OpenAI API 

Store your OpenAI API in by using 'export OPENAI_API_KEY="your-api-key-here"' or set the OpenAI API key as an environment variable in your system log. 

### Execute the following command line to run the code. 

Command: "python execution/main.py --data [data] --strategy [strategy]"

[data] is one of [paper, civic, NoticeViolation]

[strategy] is one of [GPT_single, GPT_merge, LlamaIndex_seq, LlamaIndex_tree, textdb_summary]


#this is the models API. You pass the model (name of the model) and prompt, the API will return the response out 
def model(model_name, prompt):
    if(model_name is 'gpt35'):
        from models.gpt_35_model import gpt_35
        return gpt_35(prompt)
    if(model_name is 'gpt4'):
        from models.gpt_4_model import gpt_4
        return gpt_4(prompt)
    if(model_name == 'gpt4o'):
        from models.gpt_4o import gpt_4o
        return gpt_4o(prompt)
    return 'input model does not exist'



#This scipt implements various sketches of text block in tree model 

import spacy
from heapq import nlargest
# Load the small English model
#nlp = spacy.load("en_core_web_trf")
from collections import Counter
from string import punctuation
from transformers import T5Tokenizer, T5ForConditionalGeneration
from nltk.tokenize import word_tokenize 
from bert_score import score
from rouge import Rouge 

def context_size(text):
    return len(word_tokenize(text))

# def spacy_summary(text,k=0,percent=0.1): #space is extrasive, k is the number of sentences   
#     #if use percent, then k is set to be 0; otherwise, percent is set to be 0
#     # Process the text
#     doc = nlp(text)
#     # Count word frequencies
#     word_frequencies = Counter()
#     for word in doc:
#         if word.text.lower() not in punctuation:
#             word_frequencies[word.text.lower()] += 1

#     # Normalize frequencies
#     max_frequency = max(word_frequencies.values())
#     for word in word_frequencies.keys():
#         word_frequencies[word] /= max_frequency

#     # Score sentences based on word frequencies
#     sentence_scores = {}
#     for sent in doc.sents:
#         for word in sent:
#             if word.text.lower() in word_frequencies.keys():
#                 if sent not in sentence_scores.keys():
#                     sentence_scores[sent] = word_frequencies[word.text.lower()]
#                 else:
#                     sentence_scores[sent] += word_frequencies[word.text.lower()]

#     # Extract top N sentences as the summary
#     if(k > 0):
#         summary_length = k
#     else: 
#         summary_length = int(len(sentence_scores) * percent)  # For example, 30% of original text
#     summary = nlargest(summary_length, sentence_scores, key=sentence_scores.get)

#     # Combine sentences
#     final_summary = ' '.join([sent.text for sent in summary])
#     return final_summary

def t5_summary(text, k):#t5 is abstractive summary 
    # Load the T5 model and tokenizer
    model = T5ForConditionalGeneration.from_pretrained('t5-small')
    tokenizer = T5Tokenizer.from_pretrained('t5-small')

    # Preprocess the text
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)

    # Generate the summary
    summary_ids = model.generate(inputs, max_length=k, min_length=0, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary


def evaluate_abstractive_summary(reference, summary, model_type='bert-base-uncased'):
    # Calculate BERTScore
    P, R, F1 = score([summary], [reference], lang='en', model_type=model_type)

    # Convert to standard Python floats for easy interpretation
    precision = P.item()
    recall = R.item()
    f1 = F1.item()

    return precision, recall, f1

def evaluate_extractive_summary(reference_summaries, generated_summary, mode = 'rouge-1'):#mode can be: rouge-1, rouge-2, rouge-l
    rouge = Rouge()
    scores = rouge.get_scores(generated_summary, reference_summaries, avg=True)

    rouge_1_scores = scores[mode]

    precision = rouge_1_scores['p']
    recall = rouge_1_scores['r']
    f1 = rouge_1_scores['f']

    return precision, recall, f1


    


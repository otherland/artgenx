import os
from flask import Flask, request, jsonify
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from fastapi.encoders import jsonable_encoder

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

openai.api_key = os.environ.get('OPENAI_KEY')

@app.route('/query', methods=['POST'])
def query_endpoint():
    persist_directory = request.json.get('directory')
    query = request.json.get('query')

    embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = vectordb.as_retriever()
    docs = retriever.get_relevant_documents(query)
    if docs:
        return jsonify(docs[0].page_content.replace('\n',' '))

if __name__ == '__main__':
    app.run(debug=True)
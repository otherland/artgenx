from django.conf import settings
import os
from flask import Flask, request, jsonify
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables using os.getenv()
openai.api_key = os.getenv('OPENAI_KEY')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/query', methods=['POST'])
def query_endpoint():
    persist_directory = request.json.get('directory')
    query = request.json.get('query')

    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = vectordb.as_retriever()
    docs = retriever.get_relevant_documents(query)
    if docs:
        return jsonify(docs[0].page_content.replace('\n',' '))
    else:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
from langchain.document_loaders import JSONLoader
import sys
import openai
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import uuid
import json

# Define the metadata extraction function.
def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["title"] = json.dumps(record.get("title", ""))
    metadata["url"] = json.dumps(record.get("url", ""))
    metadata["description"] = json.dumps(record.get("description", ""))
    metadata["header_outline"] = json.dumps(record.get("header_outline", ""))
    metadata["word_count"] = json.dumps(record.get("word_count", ""))
    metadata["sample_words"] = json.dumps(record.get("sample_words", ""))
    metadata["p_count"] = json.dumps(record.get("p_count", ""))
    metadata["ol_count"] = json.dumps(record.get("ol_count", ""))
    metadata["ul_count"] = json.dumps(record.get("ul_count", ""))
    metadata["shorthand"] = json.dumps(record.get("shorthand", ""))
    metadata["general"] = json.dumps(record.get("general", ""))
    metadata["internal"] = json.dumps(record.get("internal", ""))
    metadata["external"] = json.dumps(record.get("external", ""))
    metadata["internal_links"] = json.dumps(record.get("internal_links", ""))
    metadata["external_links"] = json.dumps(record.get("external_links", ""))

    return metadata

def json_to_vectorstore(filepath):
    persist_directory = os.path.join(os.path.dirname(filepath), 'vector_store')

    if os.path.exists(persist_directory):
        print("Chroma persisted database already exists. Loading existing collection.")
        db2 = Chroma.load(persist_directory)
    else:
        db2 = Chroma(persist_directory)

    loader = JSONLoader(
        filepath,
        jq_schema='.[]',
        content_key="sample_words",
        metadata_func=metadata_func,
        text_content=False
    )
    data = loader.load()

    embedding_function = OpenAIEmbeddings(openai_api_key=os.environ.get('OPENAI_KEY'))
    db2.add_documents(data, embedding_function)

    # Persist the updated collection
    db2.persist()
    print("Chroma persisted database updated.")

    return os.path.abspath(persist_directory)

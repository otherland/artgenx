from django.conf import settings
from langchain.document_loaders import JSONLoader
import sys
import openai
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import uuid
import json

import re

def generate_collection_name(input_string):
    # Remove leading and trailing whitespaces from the input
    input_string = input_string.strip()

    # Replace spaces with underscores and convert to lowercase
    collection_name = input_string.replace(' ', '_').lower()

    # Remove any characters that are not alphanumeric, underscores, or hyphens
    collection_name = re.sub(r'[^a-zA-Z0-9_-]', '', collection_name)

    # Remove consecutive underscores and hyphens
    collection_name = re.sub(r'[-_]{2,}', '', collection_name)

    # Ensure the collection name starts and ends with an alphanumeric character
    collection_name = collection_name.strip('_-')
    
    # Ensure the collection name is between 3 and 63 characters in length
    collection_name = collection_name[:63]

    return collection_name


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

def json_to_vectorstore(collection_name, filepath):
    persist_directory = os.path.join(os.path.dirname(filepath), 'vector_store')
    collection_name = generate_collection_name(collection_name)
    if os.path.exists(persist_directory):
        print("Chroma persisted database already exists. Loading existing collection.")
        db2 = Chroma(collection_name=collection_name, persist_directory=persist_directory)
    else:
        db2 = Chroma(collection_name=collection_name, persist_directory=persist_directory)

    loader = JSONLoader(
        filepath,
        jq_schema='.[]',
        content_key="sample_words",
        metadata_func=metadata_func,
        text_content=False
    )
    data = loader.load()

    embedding_function = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    db2.add_documents(data, embedding_function)

    # Persist the updated collection
    db2.persist()
    print("Chroma persisted database updated.")

    return os.path.abspath(persist_directory)

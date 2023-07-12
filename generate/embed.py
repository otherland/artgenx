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
    loader = JSONLoader(
        filepath,
        jq_schema='.[]',
        content_key="sample_words",
        metadata_func=metadata_func,
        text_content=False
    )
    persist_directory = os.path.join(os.path.dirname(filepath), 'vector_store')
    data = loader.load()
    embedding_function = OpenAIEmbeddings(openai_api_key='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')
    db2 = Chroma.from_documents(data, embedding_function, persist_directory=persist_directory)
    db2.persist()
    return persist_directory

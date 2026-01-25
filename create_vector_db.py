from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
import os

final_documents = []
# First we parse the markdown documents.


# For this cookbook, we have each recipe as a header with ####
with open("cookbooks_md/RealChef-obooko-fd0013/RealChef-obooko-fd0013.md", "r", encoding="utf-8") as f:
    text = f.read()

headers_to_split_on = [("####", "recipe_name")]

text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
chunks = text_splitter.split_text(text)
for chunk in chunks:
    chunk.metadata["type"] = "professional"
    chunk.metadata["source"] = "RealChef-obooko-fd0013.md"
final_documents.extend(chunks)

# manually inspect some of the chunks
print(chunks[5:15])


with open("cookbooks_md/dudes-kitchen-cookbook-for-men-obooko/dudes-kitchen-cookbook-for-men-obooko.md", "r", encoding="utf-8") as f:
    text = f.read()

# This book separates recipes by ##
headers_to_split_on = [("##", "recipe_name")]

text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
chunks = text_splitter.split_text(text)
for chunk in chunks:
    chunk.metadata["type"] = "casual"
    chunk.metadata["source"] = "dudes-kitchen-cookbook-for-men-obooko"

# manually inspect some of the chunks
print(chunks[5:15])

final_documents.extend(chunks)

# Now do pdfs, fortunately they are separated by pages

for f in os.listdir("cookbooks"):
    file_path = os.path.join("cookbooks", f)

    loader = PyMuPDFLoader(file_path)
    chunks = loader.load()
    for chunk in chunks:
        chunk.metadata["type"] = f.replace(".pdf", "")

    print(chunks[5:15])
    final_documents.extend(chunks)

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma.from_documents(
    documents=final_documents,
    embedding=embedding_model,
    persist_directory="./cookbook_db",
    collection_name="recipes"
)

print("Ingestion complete")
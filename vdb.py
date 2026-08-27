import chromadb


def save_on_vector_database():
    #i need to extract information from pdf and documents first before i can save them in vectorised DB
    #i need datatype for these guys documents/images
    #i need then to save them together in chunk
    client = chromadb.PersistentClient(path="./databases")
    collection = client.get_or_create_collection(name="my_documents")
    
import os

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_huggingface import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import FAISS


DOCUMENTS_DIR = "documents"
VECTORSTORE_DIR = "vectorstore"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# =========================================================
# LOAD ALL DOCUMENTS
# =========================================================

def load_documents():

    all_documents = []

    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)

    files = os.listdir(DOCUMENTS_DIR)

    print("\nDocuments found:")

    for filename in files:

        filepath = os.path.join(
            DOCUMENTS_DIR,
            filename
        )

        if not os.path.isfile(filepath):
            continue

        extension = os.path.splitext(
            filename
        )[1].lower()

        try:

            if extension == ".pdf":

                loader = PyPDFLoader(filepath)

            elif extension == ".txt":

                loader = TextLoader(
                    filepath,
                    encoding="utf-8"
                )

            elif extension == ".docx":

                loader = Docx2txtLoader(filepath)

            elif extension == ".csv":

                loader = CSVLoader(filepath)

            else:

                print(
                    f"SKIP: {filename}"
                )

                continue

            documents = loader.load()

            # Add our own filename metadata
            for document in documents:

                document.metadata["source_file"] = filename

            all_documents.extend(documents)

            print(
                f"OK: {filename} -> "
                f"{len(documents)} document/page(s)"
            )

        except Exception as e:

            print(
                f"ERROR: {filename}"
            )

            print(e)

    print(
        f"\nTotal loaded documents/pages: "
        f"{len(all_documents)}"
    )

    return all_documents


# =========================================================
# CREATE VECTOR STORE FROM ALL DOCUMENTS
# =========================================================

def create_vectorstore():

    print("\nCreating vector store...")

    documents = load_documents()

    if not documents:

        raise ValueError(
            "No supported documents found."
        )

    # -----------------------------------------------------
    # Split ALL documents
    # -----------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Total chunks created: {len(chunks)}"
    )

    # -----------------------------------------------------
    # Embeddings
    # -----------------------------------------------------

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    # -----------------------------------------------------
    # Create FAISS
    # -----------------------------------------------------

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    os.makedirs(
        VECTORSTORE_DIR,
        exist_ok=True
    )

    vectorstore.save_local(
        VECTORSTORE_DIR
    )

    print(
        "Vector store created successfully."
    )

    return vectorstore


# =========================================================
# LOAD VECTOR STORE
# =========================================================

def get_vectorstore():

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    index_file = os.path.join(
        VECTORSTORE_DIR,
        "index.faiss"
    )

    if not os.path.exists(index_file):

        return create_vectorstore()

    print(
        "Loading existing vector store..."
    )

    vectorstore = FAISS.load_local(
        VECTORSTORE_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# =========================================================
# REBUILD VECTOR STORE
# =========================================================

def rebuild_vectorstore():

    print("\nRebuilding vector store...")

    if os.path.exists(VECTORSTORE_DIR):

        for filename in os.listdir(
            VECTORSTORE_DIR
        ):

            filepath = os.path.join(
                VECTORSTORE_DIR,
                filename
            )

            if os.path.isfile(filepath):

                os.remove(filepath)

    return create_vectorstore()


# =========================================================
# SEARCH ALL DOCUMENTS
# =========================================================

def search_documents(
    query: str,
    k: int = 6
):

    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search(
        query,
        k=k
    )

    return results
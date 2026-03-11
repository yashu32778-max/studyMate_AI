from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai

genai.configure(api_key="GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")
def process_pdf(file):
    loader = PyPDFLoader(file)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    docs = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings()
    vector_db = FAISS.from_documents(docs, embeddings)
    
    # This saves the index as a .faiss and .pkl file
    vector_db.save_local("vectorstore")

def ask_question(question):
    # --- Part 1: Retrieval (Finding the data) ---
    embeddings = HuggingFaceEmbeddings()
    db = FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)
    
    # Get the top 3 most relevant snippets instead of just 1
    docs = db.similarity_search(question, k=3)
    context_text = "\n".join([d.page_content for d in docs])

    # --- Part 2: Generation (Asking Gemini to explain) ---
    prompt = f"""
    You are a helpful assistant. Use the following PDF context to answer the question.
    If the answer isn't in the context, use your own knowledge but mention that 
    it wasn't in the document.
    
    Context: {context_text}
    Question: {question}
    """

    response = model.generate_content(prompt)
    
    # Return Gemini's smart explanation instead of raw text
    return response.text
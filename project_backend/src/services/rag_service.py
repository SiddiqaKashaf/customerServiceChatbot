import os
import re
import json
import pickle
import nltk
import warnings
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
import numpy as np
from datetime import datetime
from src.services.groq_service import GroqService
import logging
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import centralized warning suppression
from src.config.warnings_config import suppress_warnings

# Suppress warnings
suppress_warnings()
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

class RAGService:
    def __init__(self):
        self.documents = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False,
        )
        self.knowledge_base_path = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.ensure_data_directory()
        
        # Initialize LLM service
        self.llm_service = GroqService()
        
        # Initialize embeddings with warning suppression
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize TF-IDF vectorizer for legacy fallback
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.document_vectors = None
        
        # Load FAISS index if available, else fallback to legacy
        self.load_faiss_index()
        if not hasattr(self, 'faiss_index') or self.faiss_index is None:
            logger.info("No FAISS index found, attempting to process PDF and build index...")
            self.load_knowledge_base()
            self.load_sample_documents()
            # If still no documents, try to force process the PDF
            if len(self.documents) == 0:
                logger.info("No documents loaded, attempting to force process PDF...")
                self.force_process_pdf()
        # If FAISS index is loaded, do NOT call load_sample_documents or force_process_pdf
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.knowledge_base_path):
            os.makedirs(self.knowledge_base_path)
    
    def load_sample_documents(self):
        """Load documents from PDF files only. Do not use hardcoded FAQ or company info."""
        if len(self.documents) == 0:
            pdf_info = self.get_pdf_info()
            if pdf_info.get('available', False):
                pdf_files = pdf_info.get('files', [])
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(pdf_info['directory'], pdf_file)
                    # Use FAISS pipeline for new PDFs
                    self.process_pdf_and_index(pdf_path)
                    logger.info(f"Loaded and indexed company information from PDF: {pdf_file}")
                    return
            # No PDF available, do not add any hardcoded FAQ
            logger.warning("No company information PDF found. Please upload the latest company information PDF.")
    
    def load_pdf_document(self, pdf_path: str) -> bool:
        """Load company information from a PDF document"""
        try:
            import PyPDF2
            import pdfplumber
            
            documents = []
            
            # Try with PyPDF2 first
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():
                            documents.append({
                                "title": f"Page {page_num + 1}",
                                "content": text
                            })
            except Exception as e:
                logger.warning(f"PyPDF2 failed, trying pdfplumber: {str(e)}")
                
                # Try with pdfplumber as fallback
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            text = page.extract_text()
                            if text.strip():
                                documents.append({
                                    "title": f"Page {page_num + 1}",
                                    "content": text
                                })
                except Exception as e2:
                    logger.error(f"pdfplumber also failed: {str(e2)}")
                    return False
            
            # Add documents to knowledge base
            for doc in documents:
                self.add_document_content(doc["title"], doc["content"])
            
            logger.info(f"Successfully loaded {len(documents)} pages from PDF: {pdf_path}")
            return True
            
        except ImportError:
            logger.error("PDF processing libraries not installed. Install with: pip install PyPDF2 pdfplumber")
            return False
        except Exception as e:
            logger.error(f"Error loading PDF document: {str(e)}")
            return False
    
    def get_pdf_info(self) -> dict:
        """Get information about available PDF documents"""
        # Look in the current directory (project_backend root) for PDFs
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project_backend root
        logger.info(f"Looking for PDFs in directory: {current_dir}")
        
        pdf_files = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]
        logger.info(f"Found PDF files in root directory: {pdf_files}")
        
        if pdf_files:
            return {
                "available": True,
                "files": pdf_files,
                "directory": current_dir,
                "message": f"Company information is available in {len(pdf_files)} PDF document(s). You can download these for offline reference."
            }
        
        # Also check if there's a company_documents subdirectory
        pdf_dir = os.path.join(current_dir, "company_documents")
        logger.info(f"Looking for PDFs in subdirectory: {pdf_dir}")
        
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            logger.info(f"Found PDF files in subdirectory: {pdf_files}")
            if pdf_files:
                return {
                    "available": True,
                    "files": pdf_files,
                    "directory": pdf_dir,
                    "message": f"Company information is available in {len(pdf_files)} PDF document(s). You can download these for offline reference."
                }
        
        logger.warning("No PDF files found in any directory")
        return {
            "available": False,
            "message": "No PDF documents found. Run generate_company_pdf.py to create one."
        }
    
    def preprocess_text(self, text: str) -> str:
        """Enhanced text preprocessing for better matching"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\?\:\,\.\-\(\)]', '', text)  # retain some punctuation
        # Normalize numbers and currency
        text = re.sub(r'\$\d+', 'price', text)
        text = re.sub(r'\d+%', 'percentage', text)
        return text.strip()
    
    def is_greeting(self, text: str) -> bool:
        """Check if text is a greeting using LLM"""
        intent = self.llm_service.analyze_query_intent(text)
        return intent == 'greeting'
    
    def is_farewell(self, text: str) -> bool:
        """Check if text is a farewell using LLM"""
        intent = self.llm_service.analyze_query_intent(text)
        return intent == 'farewell'
    
    def is_relevant_to_company(self, text: str) -> bool:
        """Check if the query is relevant to company using LLM"""
        return self.llm_service.check_relevance(text)
    
    def add_document_content(self, title: str, content: str):
        """Add document content to knowledge base with chunking"""
        # Split content into smaller chunks for better retrieval
        chunks = self.text_splitter.split_text(content)
        
        for i, chunk in enumerate(chunks):
            doc = {
                "title": f"{title} - Part {i+1}",
                "content": chunk,
                "full_title": title,
                "processed_content": self.preprocess_text(chunk)
            }
            self.documents.append(doc)
        
        self.build_vectors()
    
    def add_document(self, file) -> Dict[str, Any]:
        """Add document file to knowledge base"""
        try:
            # Read file content
            content = file.read().decode('utf-8')
            title = file.filename
            
            # Add to knowledge base
            self.add_document_content(title, content)
            
            return {
                "filename": title,
                "status": "success",
                "size": len(content)
            }
        except Exception as e:
            return {
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            }
    
    def build_vectors(self):
        """Build TF-IDF vectors for document search"""
        if not self.documents:
            return
        
        # Extract processed content
        texts = [doc["processed_content"] for doc in self.documents]
        
        # Build TF-IDF vectors
        self.document_vectors = self.vectorizer.fit_transform(texts)
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Enhanced document search with better relevance scoring and error handling"""
        if not self.documents or self.document_vectors is None:
            return []
        
        try:
            # Preprocess query
            processed_query = self.preprocess_text(query)
            
            # Transform query
            query_vector = self.vectorizer.transform([processed_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
            
            # Get top matches with lower threshold for better coverage
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            max_sim = 0
            for idx in top_indices:
                if similarities[idx] > 0.2:  # lowered threshold
                    max_sim = max(max_sim, similarities[idx])
                    try:
                        doc = self.documents[idx]
                        logger.info(f"Query: {query} | Match: {doc.get('title')} | Score: {similarities[idx]:.4f}")
                        # Ensure document has required fields
                        if isinstance(doc, dict) and 'title' in doc and 'content' in doc:
                            results.append({
                                "title": doc.get("title", "Unknown"),
                                "full_title": doc.get("full_title", doc.get("title", "Unknown")),
                                "content": doc.get("content", ""),
                                "similarity": float(similarities[idx])
                            })
                    except (IndexError, KeyError, TypeError) as e:
                        logger.error(f"Error accessing document at index {idx}: {str(e)}")
                        continue
            # If the best similarity is below 0.4, treat as no relevant docs
            if max_sim < 0.4:
                return []
            return results
            
        except Exception as e:
            logger.error(f"Error in document search: {str(e)}")
            return []
    
    def generate_response_with_context(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate precise response using context documents with LLM"""
        # Group context by service type for better organization
        service_contexts = {}
        for doc in context_docs:
            service_type = doc["full_title"]
            if service_type not in service_contexts:
                service_contexts[service_type] = []
            service_contexts[service_type].append(doc["content"])
        
        # Create organized context
        organized_context = ""
        for service_type, contents in service_contexts.items():
            organized_context += f"\n\n{service_type}:\n" + "\n".join(contents)
        
        # Create a more specific prompt for precise answers
        enhanced_prompt = f"""
        Based on the following information about TechCorp Solutions, provide a precise and professional answer to the user's question.
        
        User Question: {query}
        
        Available Information:{organized_context}
        
        Instructions:
        1. Answer the specific question asked, not general information
        2. If asking about pricing, provide exact prices for the specific service mentioned
        3. If asking about a specific service, focus on that service only
        4. Be professional, concise, and accurate
        5. Include relevant details but avoid unnecessary information
        6. If the information is not available, clearly state that
        """
        
        return self.llm_service.generate_response(enhanced_prompt, organized_context)
    
    def generate_greeting_response(self) -> str:
        """Generate a professional greeting response"""
        return "Hello! I'm your dedicated customer service assistant. I'm here to help you with information about our services, pricing, technical support, and any other questions you may have. How can I assist you today?"
    
    def generate_farewell_response(self) -> str:
        """Generate a professional farewell response"""
        return "Thank you for contacting us! I hope I was able to help you today. If you have any further questions or need assistance in the future, please don't hesitate to reach out. Have a great day!"
    
    def process_message(self, message: str, conversation_id: str) -> Dict[str, Any]:
        """Process user message using RAG approach - retrieve context and generate response"""
        message_lower = message.lower()
        pdf_info = self.get_pdf_info()
        pdf_available = pdf_info.get('available', False)
        
        # Check for greetings
        if self.is_greeting(message):
            greeting_response = self.generate_greeting_response()
            return {
                "response": greeting_response,
                "confidence": 0.95,
                "context_used": False,
                "sources": [],
                "suggested_responses": [
                    "Tell me about your tech services",
                    "What are your pricing plans?",
                    "I need technical support",
                    "How can I contact you?"
                ],
                "pdf_available": pdf_available
            }
        
        # Check for farewells
        if self.is_farewell(message):
            farewell_response = self.generate_farewell_response()
            return {
                "response": farewell_response,
                "confidence": 0.95,
                "context_used": False,
                "sources": [],
                "suggested_responses": [],
                "pdf_available": pdf_available
            }

        # Check for relevance before searching documents
        if not self.is_relevant_to_company(message):
            response = self.generate_fallback_response(message)
            return {
                "response": response,
                "confidence": 0.5,
                "context_used": False,
                "sources": [],
                "suggested_responses": [
                    "Tell me about your tech services",
                    "What are your pricing plans?",
                    "I need technical support",
                    "How can I contact you?"
                ],
                "pdf_available": pdf_available
            }

        # Use RAG approach for all other queries
        try:
            # Search for relevant documents using FAISS
            relevant_docs = self.search_documents_faiss(message, top_k=3)
            
            if relevant_docs and len(relevant_docs) > 0:
                # Generate response using RAG chain
                response = self.generate_rag_response(message, relevant_docs)
                avg_similarity = np.mean([doc.get("similarity", 0.5) for doc in relevant_docs])
                confidence = min(0.95, max(0.7, avg_similarity))
                
                return {
                    "response": response,
                    "confidence": confidence,
                    "context_used": True,
                    "sources": [{"title": doc.get("title", "Unknown"), "similarity": doc.get("similarity", 0.5)} for doc in relevant_docs],
                    "suggested_responses": self.generate_suggested_responses(message, relevant_docs),
                    "pdf_available": pdf_available
                }
            else:
                # No relevant documents found
                response = self.generate_fallback_response(message)
                return {
                    "response": response,
                    "confidence": 0.6,
                    "context_used": False,
                    "sources": [],
                    "suggested_responses": [
                        "Tell me about your tech services",
                        "What are your pricing plans?",
                        "I need technical support",
                        "How can I contact you?"
                    ],
                    "pdf_available": pdf_available
                }
                
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            response = self.generate_fallback_response(message)
            return {
                "response": response,
                "confidence": 0.5,
                "context_used": False,
                "sources": [],
                "suggested_responses": [
                    "Tell me about your tech services",
                    "What are your pricing plans?",
                    "I need technical support",
                    "How can I contact you?"
                ],
                "pdf_available": pdf_available
            }
    
    def generate_suggested_responses(self, query: str, relevant_docs: List[Dict[str, Any]] = None) -> List[str]:
        """Generate context-aware suggested responses"""
        query_lower = query.lower()
        # For each suggestion, ensure a direct, professional answer is available in process_message
        if any(word in query_lower for word in ['cloud', 'migration']):
            return [
                "What's the timeline for cloud migration?",
                "Do you support hybrid cloud solutions?",
                "What's included in the migration process?"
            ]
        elif any(word in query_lower for word in ['ai', 'machine learning', 'ml']):
            return [
                "What types of AI solutions do you offer?",
                "How long does AI development take?",
                "Do you provide AI consulting?"
            ]
        elif any(word in query_lower for word in ['security', 'cybersecurity']):
            return [
                "What security certifications do you have?",
                "Do you offer 24/7 security monitoring?",
                "What's your incident response time?"
            ]
        elif any(word in query_lower for word in ['web', 'website', 'application']):
            return [
                "What technologies do you use for web development?",
                "Do you provide ongoing maintenance?",
                "Can you help with e-commerce platforms?"
            ]
        elif any(word in query_lower for word in ['mobile', 'app']):
            return [
                "Do you develop for both iOS and Android?",
                "What's the cost of mobile app development?",
                "Do you provide app maintenance services?"
            ]
        elif any(word in query_lower for word in ['data', 'analytics']):
            return [
                "What BI tools do you work with?",
                "Can you help with data strategy?",
                "Do you provide custom dashboards?"
            ]
        elif any(word in query_lower for word in ['price', 'cost', 'pricing']):
            return [
                "What's included in your pricing?",
                "Do you offer custom pricing?",
                "What are your payment terms?"
            ]
        elif any(word in query_lower for word in ['support', 'help']):
            return [
                "What are your support response times?",
                "Do you offer 24/7 support?",
                "How can I contact technical support?"
            ]
        else:
            return [
                "Tell me about your tech services",
                "What are your pricing plans?",
                "I need technical support",
                "How can I contact you?"
            ]
    
    def save_knowledge_base(self):
        """Save knowledge base to file"""
        try:
            kb_data = {
                'documents': self.documents,
                'vectorizer': self.vectorizer,
                'document_vectors': self.document_vectors
            }
            
            kb_path = os.path.join(self.knowledge_base_path, 'knowledge_base.pkl')
            with open(kb_path, 'wb') as f:
                pickle.dump(kb_data, f)
        except Exception as e:
            logger.error(f"Error saving knowledge base: {str(e)}")
    
    def load_knowledge_base(self):
        """Load knowledge base from file with compatibility handling"""
        try:
            kb_path = os.path.join(self.knowledge_base_path, 'knowledge_base.pkl')
            if os.path.exists(kb_path):
                with open(kb_path, 'rb') as f:
                    kb_data = pickle.load(f)
                
                # Handle different document formats
                loaded_documents = kb_data.get('documents', [])
                self.documents = []
                
                for doc in loaded_documents:
                    if isinstance(doc, dict):
                        # Already in correct format
                        self.documents.append(doc)
                    else:
                        # Convert Document object to dictionary format
                        try:
                            doc_dict = {
                                "title": getattr(doc, 'metadata', {}).get('title', 'Unknown'),
                                "content": getattr(doc, 'page_content', str(doc)),
                                "full_title": getattr(doc, 'metadata', {}).get('title', 'Unknown'),
                                "processed_content": self.preprocess_text(getattr(doc, 'page_content', str(doc)))
                            }
                            self.documents.append(doc_dict)
                        except Exception as e:
                            logger.error(f"Error converting document: {str(e)}")
                            continue
                
                self.vectorizer = kb_data.get('vectorizer', self.vectorizer)
                self.document_vectors = kb_data.get('document_vectors', None)
                
                # Rebuild vectors if documents were converted
                if self.documents and self.document_vectors is None:
                    self.build_vectors()
                    
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            # If loading fails, start with empty documents
            self.documents = []
            self.document_vectors = None
    
    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Get status of the knowledge base with error handling"""
        try:
            document_titles = []
            for doc in self.documents:
                try:
                    if isinstance(doc, dict):
                        title = doc.get('full_title', doc.get('title', 'Unknown'))
                    else:
                        title = getattr(doc, 'metadata', {}).get('title', 'Unknown')
                    document_titles.append(title)
                except Exception as e:
                    logger.error(f"Error accessing document title: {str(e)}")
                    continue
            
            return {
                'total_documents': len(self.documents),
                'document_titles': list(set(document_titles)),
                'vectors_built': self.document_vectors is not None,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting knowledge base status: {str(e)}")
            return {
                'total_documents': 0,
                'document_titles': [],
                'vectors_built': False,
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            } 

    def process_pdf_and_index(self, pdf_path: str):
        """
        Extracts text from a PDF, preprocesses, chunks, and creates FAISS vectorstore using LangChain.
        """
        import pdfplumber

        # 1. Extract text from PDF
        documents = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    documents.append({
                        "title": f"Page {page_num + 1}",
                        "content": text.strip()
                    })

        # 2. Combine all text and create chunks
        all_text = "\n\n".join([doc["content"] for doc in documents])
        text_chunks = self.text_splitter.split_text(all_text)
        
        # 3. Create FAISS vectorstore using LangChain
        vectorstore = FAISS.from_texts(text_chunks, self.embeddings)
        
        # 4. Save the vectorstore
        vectorstore.save_local(os.path.join(self.knowledge_base_path, "faiss_index"))
        
        # 5. Store chunks and vectorstore
        self.documents = [{"title": f"Chunk {i+1}", "content": chunk, "full_title": f"Chunk {i+1}"} 
                         for i, chunk in enumerate(text_chunks)]
        self.faiss_index = vectorstore
        self.vector_dim = len(self.embeddings.embed_query("test"))

        logger.info(f"Processed and indexed {len(text_chunks)} chunks from {pdf_path}")

    def load_faiss_index(self):
        index_path = os.path.join(self.knowledge_base_path, "faiss_index")
        
        if os.path.exists(index_path):
            try:
                # Load the FAISS vectorstore
                self.faiss_index = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
                
                # Create documents list from the vectorstore
                docs = self.faiss_index.docstore._dict
                self.documents = []
                for doc_id, doc in docs.items():
                    if hasattr(doc, 'page_content'):
                        self.documents.append({
                            "title": f"Document {doc_id}",
                            "content": doc.page_content,
                            "full_title": f"Document {doc_id}"
                        })
                
                self.vector_dim = len(self.embeddings.embed_query("test"))
                
                logger.info(f"FAISS vectorstore loaded. {len(self.documents)} documents indexed.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                self.faiss_index = None
                self.documents = []
                self.vector_dim = None
        else:
            logger.info("No FAISS index found. Will use legacy TF-IDF search.")
            self.faiss_index = None
            self.documents = []
            self.vector_dim = None

    def search_documents_faiss(self, query: str, top_k: int = 5):
        if not hasattr(self, 'faiss_index') or self.faiss_index is None or not self.documents:
            logger.warning("FAISS index not available, falling back to legacy search")
            return self.search_documents(query, top_k)

        try:
            logger.info(f"Starting FAISS search for query: '{query}'")
            
            # Use LangChain's retriever with the new invoke method
            retriever = self.faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
            docs = retriever.invoke(query)
            
            results = []
            max_sim = 0
            for i, doc in enumerate(docs):
                sim = 0.8 - (i * 0.1)
                if sim > 0.2:
                    max_sim = max(max_sim, sim)
                    results.append({
                        "title": f"Document {i+1}",
                        "content": doc.page_content,
                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                        "similarity": sim
                    })
            # If the best similarity is below 0.4, treat as no relevant docs
            if max_sim < 0.4:
                return []
            logger.info(f"FAISS search returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in FAISS search: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.warning("Falling back to legacy search")
            try:
                return self.search_documents(query, top_k)
            except Exception as fallback_error:
                logger.error(f"Legacy search also failed: {str(fallback_error)}")
                return []

    def rebuild_faiss_index(self):
        """Force reprocess all PDFs and rebuild the FAISS index"""
        try:
            pdf_info = self.get_pdf_info()
            if pdf_info.get('available', False):
                pdf_files = pdf_info.get('files', [])
                if pdf_files:
                    # Process the first PDF (assuming it's the main company document)
                    pdf_path = os.path.join(pdf_info['directory'], pdf_files[0])
                    logger.info(f"Rebuilding FAISS index from PDF: {pdf_files[0]}")
                    self.process_pdf_and_index(pdf_path)
                    return True
                else:
                    logger.warning("No PDF files found to rebuild index")
                    return False
            else:
                logger.warning("No PDF directory found")
                return False
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {str(e)}")
            return False

    def get_index_status(self) -> Dict[str, Any]:
        """Get the current status of the FAISS index"""
        try:
            return {
                'faiss_available': hasattr(self, 'faiss_index') and self.faiss_index is not None,
                'documents_count': len(self.documents) if hasattr(self, 'documents') else 0,
                'vector_dim': self.vector_dim if hasattr(self, 'vector_dim') else None,
                'index_path': os.path.join(self.knowledge_base_path, "faiss_index"),
                'index_exists': os.path.exists(os.path.join(self.knowledge_base_path, "faiss_index")),
                'embeddings_model': getattr(self.embeddings, 'model_name', str(type(self.embeddings)))
            }
        except Exception as e:
            logger.error(f"Error getting index status: {str(e)}")
            return {'error': str(e)}

    def force_process_pdf(self):
        """Force process the PDF if it exists but hasn't been processed"""
        try:
            pdf_info = self.get_pdf_info()
            if pdf_info.get('available', False):
                pdf_files = pdf_info.get('files', [])
                if pdf_files:
                    pdf_path = os.path.join(pdf_info['directory'], pdf_files[0])
                    logger.info(f"Force processing PDF: {pdf_files[0]}")
                    self.process_pdf_and_index(pdf_path)
                    
                    # Verify the index was built
                    if hasattr(self, 'faiss_index') and self.faiss_index is not None:
                        logger.info(f"Successfully built FAISS index with {len(self.documents)} documents")
                    else:
                        logger.error("Failed to build FAISS index")
                else:
                    logger.warning("No PDF files found in company_documents directory")
            else:
                logger.warning("No PDF directory found")
        except Exception as e:
            logger.error(f"Error in force_process_pdf: {str(e)}")

    def generate_rag_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate concise and relevant response using RAG approach.
        """
        if not context_docs:
            return self.generate_fallback_response(query)
        
        # Prepare context from retrieved documents
        context_text = "\n\n".join([doc["content"] for doc in context_docs[:3]])
        
        # Create a focused prompt for professional, concise responses
        prompt = f"""You are TechCorp Solutions' AI assistant. Provide a direct, professional answer based on the context.

Context: {context_text}

User Question: {query}

Instructions:
- Answer the specific question asked (max 120 words)
- Use only information from the provided context
- If context doesn't contain the answer, say "I don't have specific information about that in our knowledge base"
- Be professional, clear, and actionable
- Focus on providing value, not general information
- NEVER start with a signature or greeting
- Start directly with the answer to the question

Response:"""
        
        try:
            # Let GroqService handle all signature management
            response = self.llm_service.generate_response(prompt)
            
            # Check if response is valid
            if not response or len(response.strip()) < 30 or re.match(r'^\*\*.*\*\*:?$', response.strip()): # Changed threshold to 30
                logger.warning(f"Generated response too short or header-like: '{response}'")
                return self.generate_fallback_response(query)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return self.generate_fallback_response(query)
    
    def generate_fallback_response(self, query: str) -> str:
        """Generate a concise fallback response when no context is available."""
        return f"""I don't have specific information about "{query}" in our knowledge base. 

For detailed assistance, please contact our support team at support@techcorpsolutions.com or call 1-800-TECHCORP.

Best regards,
TechCorp Solutions Customer Service"""


import os
import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# LangChain imports
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Google Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Local imports
from config import config

@dataclass
class QueryResult:
    """Data class for query results"""
    answer: str
    sources: List[Dict]
    verified_citations: List[str]
    cross_references: List[str]
    confidence: str
    raw_response: Optional[Dict] = None

class ConstitutionRAG:
    """Core RAG engine for constitutional queries"""
    
    def __init__(self):
        """Initialize the RAG engine with embeddings, LLM, and vector store"""
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.llm_type = config.LLM_PROVIDER
        self.article_index = {}  # Maps article numbers to content
        
        # Initialize components
        self._initialize_embeddings()
        self._initialize_llm()
        self._load_vector_store()
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'}
            )
            print(f"✅ Embeddings initialized: {config.EMBEDDING_MODEL}")
        except Exception as e:
            print(f"❌ Failed to initialize embeddings: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize language model based on configuration"""
        if self.llm_type == "google" and GEMINI_AVAILABLE and config.GOOGLE_API_KEY:
            try:
                genai.configure(api_key=config.GOOGLE_API_KEY)
                self.llm = genai.GenerativeModel(config.MODEL_NAME)
                print(f"✅ Google Gemini initialized: {config.MODEL_NAME}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
                self.llm = None
        else:
            print(f"⚠️ LLM provider '{self.llm_type}' not available or not configured")
            self.llm = None
    
    def _load_vector_store(self):
        """Load existing vector store if available"""
        if os.path.exists(config.VECTOR_DB_PATH):
            try:
                self.vectorstore = Chroma(
                    persist_directory=config.VECTOR_DB_PATH,
                    embedding_function=self.embeddings,
                    collection_name=config.COLLECTION_NAME
                )
                print(f"✅ Vector store loaded from {config.VECTOR_DB_PATH}")
            except Exception as e:
                print(f"❌ Failed to load vector store: {e}")
                self.vectorstore = None
        else:
            print("⚠️ No existing vector store found. Need to ingest constitution first.")
            self.vectorstore = None
    
    def _smart_split_constitution(self, text: str) -> List[Document]:
        """Smart splitting that preserves article boundaries"""
        documents = []
        
        # Pattern to match articles (e.g., "Article 1.", "Article 32A.")
        article_pattern = r'(Article\s+\d+[A-Z]*\.?)'
        
        # Split text into articles
        articles = re.split(article_pattern, text)
        
        current_article = ""
        article_number = "Preamble"
        
        for i, part in enumerate(articles):
            if i == 0:  # First part might be preamble
                if part.strip():
                    documents.append(Document(
                        page_content=part.strip(),
                        metadata={
                            "source": "Bangladesh Constitution",
                            "article": "Preamble",
                            "article_number": "Preamble",
                            "type": "constitutional_article"
                        }
                    ))
            elif i % 2 == 1:  # Article header
                article_number = part.strip()
                current_article = part
            else:  # Article content
                content = part.strip()
                if content:
                    full_article = current_article + " " + content
                    
                    # Split large articles into chunks
                    if len(full_article) > config.CHUNK_SIZE:
                        chunks = self._chunk_article(full_article, article_number)
                        documents.extend(chunks)
                    else:
                        documents.append(Document(
                            page_content=full_article,
                            metadata={
                                "source": "Bangladesh Constitution",
                                "article": article_number,
                                "article_number": self._extract_article_number(article_number),
                                "type": "constitutional_article"
                            }
                        ))
                    
                    # Update article index
                    self.article_index[self._extract_article_number(article_number)] = full_article
        
        return documents
    
    def _chunk_article(self, article_text: str, article_header: str) -> List[Document]:
        """Split large articles into manageable chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        chunks = text_splitter.split_text(article_text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "source": "Bangladesh Constitution",
                    "article": article_header,
                    "article_number": self._extract_article_number(article_header),
                    "type": "constitutional_article",
                    "chunk_id": i
                }
            ))
        
        return documents
    
    def _extract_article_number(self, article_header: str) -> str:
        """Extract article number from header"""
        match = re.search(r'Article\s+(\d+[A-Z]*)', article_header)
        return match.group(1) if match else article_header
    
    def ingest_constitution(self, file_path: str) -> bool:
        """Ingest constitution document into vector store"""
        try:
            # Read constitution file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Smart split into documents
            documents = self._smart_split_constitution(text)
            
            if not documents:
                print("❌ No documents created from constitution file")
                return False
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=config.VECTOR_DB_PATH,
                collection_name=config.COLLECTION_NAME
            )
            
            print(f"✅ Successfully ingested {len(documents)} documents from constitution")
            return True
            
        except Exception as e:
            print(f"❌ Failed to ingest constitution: {e}")
            return False
    
    def query(self, question: str) -> QueryResult:
        """Query the constitution and return answer with sources"""
        if not self.vectorstore:
            return QueryResult(
                answer="Vector store not initialized. Please ingest the constitution first.",
                sources=[],
                verified_citations=[],
                cross_references=[],
                confidence="low"
            )
        
        try:
            # 1. Retrieve relevant documents
            docs = self.vectorstore.similarity_search(question, k=config.TOP_K_RESULTS)
            
            if not docs:
                return QueryResult(
                    answer="No relevant information found in the constitution.",
                    sources=[],
                    verified_citations=[],
                    cross_references=[],
                    confidence="low"
                )
            
            # 2. Build context
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # 3. Find cross-references
            cross_refs = self._find_cross_references(context)
            
            # 4. Generate answer
            if self.llm and self.llm_type == "google":
                answer = self._query_gemini(question, context)
            else:
                answer = self._fallback_answer(question, docs)
            
            # 5. Verify citations
            verified_citations = self._verify_citations(answer, docs)
            
            # 6. Format sources
            sources = []
            for doc in docs:
                sources.append({
                    "article": doc.metadata.get("article", "Unknown"),
                    "article_number": doc.metadata.get("article_number", "Unknown"),
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            return QueryResult(
                answer=answer,
                sources=sources,
                verified_citations=verified_citations,
                cross_references=cross_refs,
                confidence="high" if verified_citations else "medium"
            )
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return QueryResult(
                answer=f"An error occurred while processing your query: {str(e)}",
                sources=[],
                verified_citations=[],
                cross_references=[],
                confidence="low"
            )
    
    def _find_cross_references(self, text: str) -> List[str]:
        """Find cross-references to other articles"""
        pattern = r'Article\s+(\d+[A-Z]*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))  # Remove duplicates
    
    def _verify_citations(self, answer: str, docs: List[Document]) -> List[str]:
        """Verify that cited articles exist in retrieved documents"""
        cited_articles = self._find_cross_references(answer)
        available_articles = [doc.metadata.get("article_number", "") for doc in docs]
        
        verified = []
        for cited in cited_articles:
            if any(cited in available for available in available_articles):
                verified.append(cited)
        
        return verified
    
    def _query_gemini(self, question: str, context: str) -> str:
        """Query Google Gemini for answer"""
        try:
            prompt = self._get_enhanced_prompt(question, context)
            
            response = self.llm.generate_content(
                prompt,
                generation_config={
                    "temperature": config.TEMPERATURE,
                    "max_output_tokens": config.MAX_TOKENS
                }
            )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini query failed: {e}")
            return f"Failed to generate answer using Gemini: {str(e)}"
    
    def _fallback_answer(self, question: str, docs: List[Document]) -> str:
        """Fallback answer when LLM is not available"""
        relevant_text = "\n\n".join([doc.page_content for doc in docs[:3]])
        
        return f"""Based on the constitution articles I found:

{relevant_text}

Note: This is a direct excerpt from the constitution. For a more detailed answer, please configure an LLM provider like Google Gemini."""
    
    def _get_enhanced_prompt(self, question: str, context: str) -> str:
        """Get enhanced prompt for constitutional queries"""
        return f"""You are a constitutional law expert specializing in the Bangladesh Constitution. 

Based on the following constitutional provisions, answer the user's question accurately and concisely.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer based ONLY on the provided constitutional text
2. Cite specific articles when referring to constitutional provisions
3. If the information is not in the provided context, state that clearly
4. Use clear, accessible language while maintaining legal accuracy
5. Format your answer with proper article citations (e.g., "According to Article 32...")

ANSWER:"""
    
    def search_articles(self, query: str, k: int = 5) -> List[Dict]:
        """Simple similarity search for articles"""
        if not self.vectorstore:
            return []
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                results.append({
                    "article": doc.metadata.get("article", "Unknown"),
                    "article_number": doc.metadata.get("article_number", "Unknown"),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def compare_with_chatgpt(self, question: str) -> Dict:
        """Compare our system with ChatGPT (placeholder)"""
        result = self.query(question)
        
        return {
            "our_answer": result.answer,
            "our_sources": result.sources,
            "competitive_advantages": [
                "Constitution-specific embeddings",
                "Article-aware chunking",
                "Citation verification",
                "Cross-reference detection",
                "Bangladesh Constitution specialization"
            ],
            "confidence": result.confidence
        }

# Singleton instance
_rag_instance = None

def get_rag_engine():
    """Get singleton RAG engine instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ConstitutionRAG()
    return _rag_instance

import os
import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Simple document class
@dataclass
class SimpleDocument:
    page_content: str
    metadata: Dict

@dataclass
class QueryResult:
    """Data class for query results"""
    answer: str
    sources: List[Dict]
    verified_citations: List[str]
    cross_references: List[str]
    confidence: str

class SimpleConstitutionRAG:
    """Simplified RAG engine for constitutional queries"""
    
    def __init__(self):
        """Initialize the RAG engine"""
        self.documents = []
        self.article_index = {}  # Maps article numbers to content
        self.llm_available = False
        
        # Try to initialize Google Gemini
        try:
            import google.generativeai as genai
            from config import config
            
            if config.GOOGLE_API_KEY and config.GOOGLE_API_KEY != "your_google_gemini_api_key_here":
                genai.configure(api_key=config.GOOGLE_API_KEY)
                self.llm = genai.GenerativeModel(config.MODEL_NAME)
                self.llm_available = True
                print(f"✅ Google Gemini initialized: {config.MODEL_NAME}")
            else:
                self.llm = None
                print("⚠️ Google Gemini API key not configured")
        except ImportError:
            self.llm = None
            print("⚠️ Google Generative AI not installed")
        except Exception as e:
            self.llm = None
            print(f"⚠️ Failed to initialize Gemini: {e}")
        
        # Load existing documents if available
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from storage if available"""
        storage_path = "./constitution_docs.json"
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = [SimpleDocument(**doc) for doc in data.get('documents', [])]
                    self.article_index = data.get('article_index', {})
                print(f"✅ Loaded {len(self.documents)} documents from storage")
            except Exception as e:
                print(f"⚠️ Failed to load documents: {e}")
    
    def _save_documents(self):
        """Save documents to storage"""
        storage_path = "./constitution_docs.json"
        try:
            data = {
                'documents': [
                    {
                        'page_content': doc.page_content,
                        'metadata': doc.metadata
                    } for doc in self.documents
                ],
                'article_index': self.article_index
            }
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(self.documents)} documents to storage")
        except Exception as e:
            print(f"⚠️ Failed to save documents: {e}")
    
    def _simple_split_constitution(self, text: str) -> List[SimpleDocument]:
        """Simple splitting that preserves article boundaries"""
        documents = []
        
        # Pattern to match articles
        article_pattern = r'(Article\s+\d+[A-Z]*\.?)'
        
        # Split text into articles
        articles = re.split(article_pattern, text)
        
        current_article = ""
        article_number = "Preamble"
        
        for i, part in enumerate(articles):
            if i == 0:  # First part might be preamble
                if part.strip():
                    documents.append(SimpleDocument(
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
                    
                    documents.append(SimpleDocument(
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
    
    def _extract_article_number(self, article_header: str) -> str:
        """Extract article number from header"""
        match = re.search(r'Article\s+(\d+[A-Z]*)', article_header)
        return match.group(1) if match else article_header
    
    def ingest_constitution(self, file_path: str) -> bool:
        """Ingest constitution document"""
        try:
            # Read constitution file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Split into documents
            self.documents = self._simple_split_constitution(text)
            
            if not self.documents:
                print("❌ No documents created from constitution file")
                return False
            
            # Save to storage
            self._save_documents()
            
            print(f"✅ Successfully ingested {len(self.documents)} documents from constitution")
            return True
            
        except Exception as e:
            print(f"❌ Failed to ingest constitution: {e}")
            return False
    
    def _simple_keyword_search(self, question: str, k: int = 5) -> List[SimpleDocument]:
        """Simple keyword-based search"""
        question_words = set(re.findall(r'\w+', question.lower()))
        scored_docs = []
        
        for doc in self.documents:
            doc_words = set(re.findall(r'\w+', doc.page_content.lower()))
            common_words = question_words.intersection(doc_words)
            score = len(common_words)
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:k]]
    
    def query(self, question: str) -> QueryResult:
        """Query the constitution"""
        if not self.documents:
            return QueryResult(
                answer="No constitution documents loaded. Please ingest the constitution first.",
                sources=[],
                verified_citations=[],
                cross_references=[],
                confidence="low"
            )
        
        try:
            # 1. Retrieve relevant documents
            docs = self._simple_keyword_search(question, k=5)
            
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
            if self.llm_available and self.llm:
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
    
    def _verify_citations(self, answer: str, docs: List[SimpleDocument]) -> List[str]:
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
            
            response = self.llm.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini query failed: {e}")
            return f"Failed to generate answer using Gemini: {str(e)}"
    
    def _fallback_answer(self, question: str, docs: List[SimpleDocument]) -> str:
        """Fallback answer when LLM is not available"""
        relevant_text = "\n\n".join([doc.page_content for doc in docs[:3]])
        
        return f"""Based on the constitution articles I found:

{relevant_text}

Note: This is a direct excerpt from the constitution. For a more detailed answer, please configure Google Gemini API key."""
    
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
        """Simple search for articles"""
        if not self.documents:
            return []
        
        try:
            docs = self._simple_keyword_search(query, k=k)
            
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

# Singleton instance
_simple_rag_instance = None

def get_simple_rag_engine():
    """Get singleton simple RAG engine instance"""
    global _simple_rag_instance
    if _simple_rag_instance is None:
        _simple_rag_instance = SimpleConstitutionRAG()
    return _simple_rag_instance

import os
import re
import logging
from typing import List, Dict, Any, Tuple
import chromadb
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")

class HybridRetriever:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        # Initialize ChromaDB persistent client
        logger.info(f"Initializing ChromaDB from {CHROMA_PERSIST_DIR}...")
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        # Create or load collection using cosine distance
        self.collection = self.chroma_client.get_or_create_collection(
            name="meridian_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Batch embeds and adds chunks to the ChromaDB collection."""
        if not chunks:
            logger.warning("No chunks to add to retriever.")
            return
            
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_model.embed_documents(texts)
        
        # Add to ChromaDB
        logger.info("Writing embeddings to ChromaDB...")
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Ingestion completed successfully in vector store.")

    def delete_all(self):
        """Clears all documents in the collection."""
        try:
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
                logger.info(f"Deleted {len(all_ids)} existing chunks from ChromaDB.")
        except Exception as e:
            logger.error(f"Error clearing ChromaDB: {e}")

    def get_indexed_documents(self) -> Dict[str, int]:
        """Returns a dict of document names and their indexed chunk counts."""
        try:
            data = self.collection.get(include=["metadatas"])
            metadatas = data.get("metadatas", [])
            doc_counts = {}
            for meta in metadatas:
                source = meta.get("source", "unknown")
                doc_counts[source] = doc_counts.get(source, 0) + 1
            return doc_counts
        except Exception as e:
            logger.error(f"Error getting document counts: {e}")
            return {}

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes hybrid search (semantic + keyword), merges and re-ranks results,
        and returns the top 3 final chunks.
        """
        if not query.strip():
            return []
            
        try:
            # 1. Fetch all documents in collection to build the BM25 index and verify count
            all_data = self.collection.get(include=["documents", "metadatas", "embeddings"])
            corpus_texts = all_data.get("documents", [])
            corpus_metadatas = all_data.get("metadatas", [])
            corpus_embeddings = all_data.get("embeddings", [])
            corpus_ids = all_data.get("ids", [])
            
            if not corpus_texts:
                logger.warning("No documents indexed. Hybrid search returned empty results.")
                return []
                
            # Tokenization for BM25 (lowercasing, alphanumeric tokens)
            def tokenize_text(text: str) -> List[str]:
                return re.findall(r'\w+', text.lower())
                
            tokenized_corpus = [tokenize_text(doc) for doc in corpus_texts]
            
            # Initialize BM25Okapi
            from rank_bm25 import BM25Okapi
            bm25 = BM25Okapi(tokenized_corpus)
            
            # 2. Semantic search (top 5 results)
            query_embedding = self.embedding_model.embed_query(query)
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(5, len(corpus_texts)),
                include=["documents", "metadatas", "distances"]
            )
            
            # Map semantic search results
            semantic_candidates = {}
            if semantic_results and semantic_results["ids"]:
                ids = semantic_results["ids"][0]
                docs = semantic_results["documents"][0]
                metadatas = semantic_results["metadatas"][0]
                distances = semantic_results["distances"][0]
                
                for idx, cid in enumerate(ids):
                    # ChromaDB distance is cosine distance (1 - cosine_similarity).
                    # We convert it back to cosine similarity.
                    similarity = 1.0 - distances[idx]
                    semantic_candidates[cid] = {
                        "id": cid,
                        "text": docs[idx],
                        "metadata": metadatas[idx],
                        "similarity": similarity
                    }
                    
            # 3. BM25 Search (top 5 results)
            query_tokens = tokenize_text(query)
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Sort corpus IDs by BM25 score
            bm25_ranked = sorted(
                list(zip(corpus_ids, bm25_scores, corpus_texts, corpus_metadatas, corpus_embeddings)),
                key=lambda x: x[1],
                reverse=True
            )
            
            bm25_candidates = {}
            for i in range(min(5, len(bm25_ranked))):
                cid, score, text, meta, emb = bm25_ranked[i]
                bm25_candidates[cid] = {
                    "id": cid,
                    "text": text,
                    "metadata": meta,
                    "bm25_score": float(score),
                    "embedding": emb
                }
                
            # 4. Combine and Re-rank unique candidates
            # Unique candidate IDs is the union of top 5 semantic and top 5 BM25
            candidate_ids = set(semantic_candidates.keys()).union(set(bm25_candidates.keys()))
            
            re_ranked_candidates = []
            
            # Helper to calculate cosine similarity
            def dot_product(v1, v2):
                return sum(x * y for x, y in zip(v1, v2))
                
            # If all BM25 scores are 0, we avoid division by zero
            bm25_vals = [bm25_candidates[cid]["bm25_score"] for cid in bm25_candidates]
            max_bm25 = max(bm25_vals) if bm25_vals else 0.0
            
            # Normalize BM25 score against the maximum score, but scale relative to
            # a significance threshold of 8.0 to prevent weak matches from inflating confidence.
            bm25_normalizer = max(max_bm25, 8.0)
            
            for cid in candidate_ids:
                # 4.1 Resolve Semantic Cosine Similarity
                if cid in semantic_candidates:
                    similarity = semantic_candidates[cid]["similarity"]
                    text = semantic_candidates[cid]["text"]
                    metadata = semantic_candidates[cid]["metadata"]
                else:
                    # BM25-only candidate: compute its similarity by fetching its embedding
                    idx_in_corpus = corpus_ids.index(cid)
                    candidate_emb = corpus_embeddings[idx_in_corpus]
                    # Compute dot product (since embedding models use unit normalized vectors)
                    similarity = dot_product(query_embedding, candidate_emb)
                    text = bm25_candidates[cid]["text"]
                    metadata = bm25_candidates[cid]["metadata"]
                    
                # 4.2 Resolve BM25 score
                if cid in bm25_candidates:
                    bm25_score = bm25_candidates[cid]["bm25_score"]
                else:
                    # Semantic-only candidate: calculate its BM25 score directly
                    idx_in_corpus = corpus_ids.index(cid)
                    bm25_score = float(bm25_scores[idx_in_corpus])
                    
                # Normalize BM25 score
                normalized_bm25 = bm25_score / bm25_normalizer if bm25_normalizer > 0 else 0.0
                
                # Combined Score formula: 0.6 * semantic + 0.4 * BM25
                combined_score = (0.6 * similarity) + (0.4 * normalized_bm25)
                
                re_ranked_candidates.append({
                    "text": text,
                    "metadata": metadata,
                    "similarity": similarity,
                    "bm25_score": bm25_score,
                    "normalized_bm25": normalized_bm25,
                    "combined_score": combined_score
                })
                
            # Sort by combined score descending
            re_ranked_candidates.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # Return top 3 chunks
            top_3 = re_ranked_candidates[:3]
            logger.info(f"Retrieved top {len(top_3)} candidates for query: '{query}'")
            for rank, item in enumerate(top_3):
                logger.info(f"Rank {rank+1}: {item['metadata']['chunk_id']} | Combined: {item['combined_score']:.4f} | Semantic: {item['similarity']:.4f} | BM25: {item['bm25_score']:.4f}")
                
            return top_3
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise e

import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Ensure we can import app modules when running from root or app/
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag_pipeline import RAGPipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TESTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "eval_questions.json"))
REPORT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "eval_report.json"))

def run_evaluation():
    logger.info("Initializing RAG Pipeline for evaluation...")
    try:
        pipeline = RAGPipeline()
    except Exception as e:
        logger.error(f"Failed to initialize RAG Pipeline: {e}")
        print("Please make sure you have ingested the documents first using python app/main.py or by running the ingestion command.")
        sys.exit(1)
        
    # Check if vectorstore is empty
    doc_counts = pipeline.get_documents()
    if not doc_counts:
        logger.warning("Vector database is empty! Please run ingestion first.")
        print("\n[WARNING] ChromaDB collection is empty. Running automatic ingestion of data/documents/ first...")
        pipeline.ingest()
        doc_counts = pipeline.get_documents()
        print(f"Indexed docs: {doc_counts}\n")

    logger.info(f"Loading test cases from {TESTS_FILE}...")
    if not os.path.exists(TESTS_FILE):
        logger.error(f"Test cases file not found at {TESTS_FILE}")
        sys.exit(1)
        
    with open(TESTS_FILE, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []
    total_in_domain = 0
    total_out_of_domain = 0
    
    correct_sources = 0
    total_relevance = 0.0
    hallucinations = 0

    print("\n" + "="*80)
    print("RUNNING RAG EVALUATION SUITE")
    print("="*80)
    print(f"{'QID':<4} | {'Question':<45} | {'Conf':<6} | {'Src Match':<9} | {'Rel %':<5} | {'Halluc':<6}")
    print("-"*80)

    for case in test_cases:
        qid = case["id"]
        question = case["question"]
        expected_src = case["source_document"]
        expected_keywords = case.get("expected_keywords", [])
        is_ood = case.get("is_out_of_domain", False)
        
        # Run through pipeline
        response = pipeline.ask(question)
        answer = response["answer"]
        sources = response["sources"]
        confidence = response["confidence"]
        conf_label = response["confidence_label"]
        
        # 1. Source Accuracy
        src_match = False
        if is_ood:
            # Out-of-domain should cite no document (sources list empty)
            src_match = len(sources) == 0
        else:
            # In-domain should cite the correct document in sources list
            src_match = any(src["document"].lower() == expected_src.lower() for src in sources)
            
        if src_match:
            correct_sources += 1
            
        # 2. Answer Relevance (keyword overlap)
        matched_kw = []
        for kw in expected_keywords:
            if kw.lower() in answer.lower():
                matched_kw.append(kw)
        
        relevance_score = len(matched_kw) / len(expected_keywords) if expected_keywords else 1.0
        
        # Only accumulate relevance for in-domain, or OOD that successfully returns "not found"
        # (if OOD returns not found, it matched the expected keywords like 'could not find')
        total_relevance += relevance_score
        
        # 3. Hallucination check
        hallucinated = False
        if is_ood:
            total_out_of_domain += 1
            # If the response doesn't say "could not find" or similar, or lists active sources, it hallucinated
            not_found_in_answer = "could not find" in answer.lower() or "not found" in answer.lower()
            if not not_found_in_answer or len(sources) > 0 or conf_label != "Low":
                hallucinated = True
                hallucinations += 1
        else:
            total_in_domain += 1
            # If in-domain returns 'could not find' but it WAS in the database, it's a false negative, not necessarily hallucination.
            # However, if it invents info, that's hallucination. But for keyword check, we focus on correctness.
            pass

        # Print line summary
        src_str = "PASS" if src_match else "FAIL"
        hall_str = "YES" if hallucinated else "NO"
        print(f"{qid:<4} | {question[:45]:<45} | {conf_label:<6} | {src_str:<9} | {relevance_score*100:>4.0f}% | {hall_str:<6}")
        
        results.append({
            "id": qid,
            "question": question,
            "expected_source": expected_src,
            "generated_answer": answer,
            "generated_sources": [s["document"] for s in sources],
            "confidence_label": conf_label,
            "confidence_score": confidence,
            "source_match": src_match,
            "relevance_score": relevance_score,
            "hallucinated": hallucinated,
            "expected_keywords": expected_keywords,
            "matched_keywords": matched_kw
        })

    # Calculations
    total_cases = len(test_cases)
    source_accuracy = correct_sources / total_cases if total_cases else 0.0
    avg_relevance = total_relevance / total_cases if total_cases else 0.0
    hallucination_rate = hallucinations / total_out_of_domain if total_out_of_domain else 0.0

    report = {
        "metrics": {
            "total_questions": total_cases,
            "in_domain_questions": total_in_domain,
            "out_of_domain_controls": total_out_of_domain,
            "source_accuracy": source_accuracy,
            "average_relevance": avg_relevance,
            "hallucination_rate": hallucination_rate
        },
        "details": results
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary table
    print("\n" + "="*80)
    print("EVALUATION METRICS SUMMARY")
    print("="*80)
    print(f"Total Questions Evaluated:  {total_cases}")
    print(f"In-Domain Questions:        {total_in_domain}")
    print(f"Out-of-Domain Control Qs:   {total_out_of_domain}")
    print("-"*80)
    print(f"Source Citation Accuracy:   {source_accuracy * 100:.1f}%")
    print(f"Answer Keyword Relevance:   {avg_relevance * 100:.1f}%")
    print(f"Hallucination Rate (OOD):   {hallucination_rate * 100:.1f}%")
    print("="*80)
    print(f"Detailed metrics report exported to {REPORT_FILE}\n")

if __name__ == "__main__":
    run_evaluation()

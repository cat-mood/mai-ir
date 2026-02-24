#!/usr/bin/env python3
import math
from typing import List, Dict

def precision_at_k(retrieved: List[int], relevant: Dict[int, int], k: int) -> float:
    if k == 0 or len(retrieved) == 0:
        return 0.0
    
    retrieved_at_k = retrieved[:k]
    relevant_count = sum(1 for doc_id in retrieved_at_k if doc_id in relevant)
    
    return relevant_count / k

def dcg_at_k(retrieved: List[int], relevant: Dict[int, int], k: int) -> float:
    dcg = 0.0
    retrieved_at_k = retrieved[:k]
    
    for i, doc_id in enumerate(retrieved_at_k, start=1):
        rel = relevant.get(doc_id, 0)
        dcg += (2 ** rel - 1) / math.log2(i + 1)
    
    return dcg

def ndcg_at_k(retrieved: List[int], relevant: Dict[int, int], k: int) -> float:
    dcg = dcg_at_k(retrieved, relevant, k)
    
    ideal_retrieved = sorted(relevant.keys(), key=lambda x: relevant[x], reverse=True)
    idcg = dcg_at_k(ideal_retrieved, relevant, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg

def err_at_k(retrieved: List[int], relevant: Dict[int, int], k: int, max_grade: int = 3) -> float:
    err = 0.0
    p = 1.0
    
    retrieved_at_k = retrieved[:k]
    
    for i, doc_id in enumerate(retrieved_at_k, start=1):
        rel = relevant.get(doc_id, 0)
        r_i = (2 ** rel - 1) / (2 ** max_grade)
        
        err += p * r_i / i
        p *= (1 - r_i)
    
    return err

def mean_average_precision(queries_results: List[tuple], queries_relevant: List[Dict[int, int]]) -> float:
    aps = []
    
    for retrieved, relevant in zip(queries_results, queries_relevant):
        if len(relevant) == 0:
            continue
        
        ap = 0.0
        relevant_count = 0
        
        for i, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                relevant_count += 1
                precision = relevant_count / i
                ap += precision
        
        if relevant_count > 0:
            ap /= len(relevant)
        
        aps.append(ap)
    
    return sum(aps) / len(aps) if aps else 0.0

def calculate_all_metrics(retrieved: List[int], relevant: Dict[int, int], k_values: List[int] = [5, 10, 20]) -> Dict:
    metrics = {}
    
    for k in k_values:
        metrics[f'P@{k}'] = precision_at_k(retrieved, relevant, k)
        metrics[f'DCG@{k}'] = dcg_at_k(retrieved, relevant, k)
        metrics[f'NDCG@{k}'] = ndcg_at_k(retrieved, relevant, k)
        metrics[f'ERR@{k}'] = err_at_k(retrieved, relevant, k)
    
    return metrics

if __name__ == '__main__':
    retrieved = [1, 3, 5, 2, 8, 10, 4]
    relevant = {1: 3, 2: 2, 3: 3, 4: 1, 5: 2}
    
    print("Example calculation:")
    print(f"Retrieved: {retrieved}")
    print(f"Relevant: {relevant}")
    print()
    
    metrics = calculate_all_metrics(retrieved, relevant)
    
    for metric_name, value in metrics.items():
        print(f"{metric_name}: {value:.4f}")

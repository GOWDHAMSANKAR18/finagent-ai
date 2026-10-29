# Empirical Evaluation & Comparative Benchmark Report

## Overview
Evaluated **8 standardized ground-truth financial test cases** comparing Single-Agent Baseline vs Multi-Agent System vs Ablated System (Without Validation).

## Benchmark Comparison Table

| Architecture Metric | Single-Agent Baseline | Multi-Agent System (Full) | Multi-Agent (No Validation) |
|---|---|---|---|
| **Calculation / Plan Accuracy** | 84.53% | **99.06%** | 94.38% |
| **Average Latency** | 0.2886s | 0.0714s | 0.0018s |
| **Average LLM Calls** | 1.0 | 5.8 | 5.0 |
| **Average Tool Calls** | 0.0 | **14.0** | 11.6 |
| **Delegation / Feedback Loops Triggered** | 0 | **3** | 0 |


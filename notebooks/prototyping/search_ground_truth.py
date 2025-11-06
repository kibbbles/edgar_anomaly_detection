"""
Ground Truth Test Questions for RAG Evaluation

Test questions with expected answers from Q1 2024 filings:
- Tesla 10-K (fiscal year 2023)
- Microsoft 10-Q (Q2 FY2024, ended Dec 31 2023)
- Apple 10-Q (Q1 FY2024, ended Dec 30 2023)

HOW SIMILARITY IS MEASURED:
-----------------------------
The RAG system uses dot-product similarity to measure how close a query is to each chunk:

1. Text -> Embeddings (768-dimensional vectors):
   - Both the user query and all document chunks are converted into 768-dimensional vectors
   - Model: multi-qa-mpnet-base-dot-v1 (trained specifically for question-answering tasks)
   - normalize_embeddings=True ensures all vectors have length 1 (unit vectors)

2. Dot-Product Similarity Calculation:
   - Formula: similarity = query_vector • chunk_vector (dot product)
   - Since vectors are normalized, dot-product equals cosine similarity
   - Range: -1.0 to 1.0 (but typically 0.0 to 1.0 for relevant content)
   - Higher score = more semantically similar

3. Example:
   Query: "What was Tesla's revenue?"

   Chunk A (revenue table):     similarity = 0.7052 (HIGH - semantically related)
   Chunk B (factory locations):  similarity = 0.4231 (LOW - different topic)
   Chunk C (random text):        similarity = 0.1234 (VERY LOW - unrelated)

4. Why Dot-Product Instead of Euclidean Distance:
   - Dot-product measures DIRECTION similarity (semantic meaning)
   - Euclidean distance measures spatial distance (less meaningful for embeddings)
   - For normalized vectors: dot_product = cosine_similarity
   - Faster to compute (no square root needed)

5. Interpretation Guidelines:
   - 0.70+  : Strong semantic match (typically correct retrieval)
   - 0.60-0.70: Moderate match (may be relevant)
   - 0.50-0.60: Weak match (likely tangentially related)
   - <0.50  : Poor match (probably not relevant)

See: src/pipeline/rag_query.py line 115
     similarities = np.dot(self.embeddings, query_embedding)
"""

GROUND_TRUTH_TESTS = [
    # Tesla 10-K (fiscal year 2023) - Very specific questions
    {
        "id": "tesla_vehicle_production_2023",
        "question": "How many consumer vehicles did Tesla produce in 2023?",
        "expected_answer": "1,845,985 vehicles",
        "expected_file": "20240129_10-K_edgar_data_1318605_0001628280-24-002390.json",
        "answer_location": "Item 7 - Management Discussion and Analysis",
        "difficulty": "easy",
        "category": "operations_data"
    },
    {
        "id": "tesla_vehicle_deliveries_2023",
        "question": "How many consumer vehicles did Tesla deliver in 2023?",
        "expected_answer": "1,808,581 vehicles",
        "expected_file": "20240129_10-K_edgar_data_1318605_0001628280-24-002390.json",
        "answer_location": "Item 7 - Management Discussion and Analysis",
        "difficulty": "easy",
        "category": "operations_data"
    },
    {
        "id": "tesla_headquarters_location",
        "question": "Where is Tesla's principal executive office located according to their 2023 10-K?",
        "expected_answer": "1 Tesla Road, Austin, Texas 78725",
        "expected_file": "20240129_10-K_edgar_data_1318605_0001628280-24-002390.json",
        "answer_location": "Cover page or Item 1 Business",
        "difficulty": "easy",
        "category": "company_info"
    },
    {
        "id": "tesla_total_revenue_2023",
        "question": "What was Tesla's total revenue in fiscal year 2023?",
        "expected_answer": "$96,773 million or $96.8 billion",
        "expected_file": "20240129_10-K_edgar_data_1318605_0001628280-24-002390.json",
        "answer_location": "Consolidated Statement of Operations",
        "difficulty": "easy",
        "category": "financial_data"
    },

    # Microsoft 10-Q (Q2 FY2024, ended Dec 31 2023) - Very specific questions
    {
        "id": "microsoft_cloud_revenue_q2fy24",
        "question": "What was Microsoft's Intelligent Cloud segment revenue for the three months ended December 31, 2023?",
        "expected_answer": "$25,881 million or $25.9 billion",
        "expected_file": "20240130_10-Q_edgar_data_789019_0000950170-24-008814.json",
        "answer_location": "Revenue by segment table",
        "difficulty": "easy",
        "category": "financial_data"
    },
    {
        "id": "microsoft_headquarters_location",
        "question": "Where is Microsoft's principal executive office located according to their December 31, 2023 10-Q?",
        "expected_answer": "One Microsoft Way, Redmond, Washington 98052-6399",
        "expected_file": "20240130_10-Q_edgar_data_789019_0000950170-24-008814.json",
        "answer_location": "Cover page",
        "difficulty": "easy",
        "category": "company_info"
    },
    {
        "id": "microsoft_total_revenue_q2fy24",
        "question": "What was Microsoft's total revenue for the three months ended December 31, 2023?",
        "expected_answer": "$62,020 million or $62.0 billion",
        "expected_file": "20240130_10-Q_edgar_data_789019_0000950170-24-008814.json",
        "answer_location": "Consolidated Statement of Income",
        "difficulty": "easy",
        "category": "financial_data"
    },

    # Apple 10-Q (Q1 FY2024, ended Dec 30 2023) - Very specific questions
    {
        "id": "apple_iphone_revenue_q1fy24",
        "question": "What was Apple's iPhone net sales for the quarter ended December 30, 2023?",
        "expected_answer": "$69,700 million or $69.7 billion",
        "expected_file": "20240202_10-Q_edgar_data_320193_0000320193-24-000006.json",
        "answer_location": "Condensed Consolidated Statements of Operations - Net Sales by Product",
        "difficulty": "easy",
        "category": "financial_data"
    },
    {
        "id": "apple_headquarters_location",
        "question": "Where is Apple's principal executive office located according to their Q1 FY2024 10-Q?",
        "expected_answer": "One Apple Park Way, Cupertino, California 95014",
        "expected_file": "20240202_10-Q_egar_data_320193_0000320193-24-000006.json",
        "answer_location": "Cover page",
        "difficulty": "easy",
        "category": "company_info"
    },
    {
        "id": "apple_europe_revenue_growth_q1fy24",
        "question": "How much did Apple's Europe segment net sales increase in the first quarter of fiscal 2024 compared to the prior year quarter?",
        "expected_answer": "$2,685 million or $2.7 billion (10% increase)",
        "expected_file": "20240202_10-Q_edgar_data_320193_0000320193-24-000006.json",
        "answer_location": "Segment Operating Performance - Europe",
        "difficulty": "medium",
        "category": "financial_analysis"
    }
]


def get_test_by_id(test_id: str):
    """Get a specific test by ID."""
    for test in GROUND_TRUTH_TESTS:
        if test['id'] == test_id:
            return test
    return None


def get_tests_by_difficulty(difficulty: str):
    """Get all tests of a specific difficulty."""
    return [t for t in GROUND_TRUTH_TESTS if t['difficulty'] == difficulty]


def get_tests_by_category(category: str):
    """Get all tests of a specific category."""
    return [t for t in GROUND_TRUTH_TESTS if t['category'] == category]


if __name__ == "__main__":
    print("Ground Truth Test Questions")
    print("=" * 80)
    print(f"Total tests: {len(GROUND_TRUTH_TESTS)}\n")

    for test in GROUND_TRUTH_TESTS:
        print(f"[{test['id']}] ({test['difficulty']}/{test['category']})")
        print(f"Q: {test['question']}")
        print(f"Expected: {test['expected_answer']}")
        print(f"Source: {test['expected_file']}")
        print()

"""
Demo prompts for testing the AI Prompt Toolkit optimization features.
These are intentionally suboptimal prompts that can be improved.
"""

from typing import List, Dict, Any

# Poor quality prompts that need optimization
DEMO_PROMPTS: List[Dict[str, Any]] = [
    {
        "name": "Verbose Summarization",
        "category": "summarization",
        "original_prompt": """
        I need you to please take the following text that I'm going to provide to you and then carefully read through it and understand what it's saying and then create a summary of it that captures the main points and key ideas but doesn't include all the unnecessary details and make sure the summary is concise but also comprehensive and informative and useful for someone who wants to understand the main content without reading the whole thing. Please make sure you don't miss any important points and also make sure the summary flows well and is easy to read and understand. The text I want you to summarize is: {text}
        """,
        "optimized_prompt": """
        Summarize the following text, focusing on the main points and key ideas. Keep it concise but comprehensive:

        {text}
        """,
        "improvement_notes": [
            "Reduced from 89 words to 16 words (82% reduction)",
            "Removed redundant instructions",
            "Clearer structure with direct instruction",
            "Maintained all essential requirements"
        ],
        "test_cases": [
            {
                "variables": {
                    "text": "Artificial intelligence (AI) is transforming industries worldwide. From healthcare to finance, AI applications are improving efficiency and creating new opportunities. However, challenges remain in areas such as data privacy, algorithmic bias, and job displacement. Organizations must carefully consider these factors when implementing AI solutions."
                },
                "expected_themes": ["AI transformation", "benefits", "challenges", "implementation considerations"]
            }
        ]
    },
    {
        "name": "Unclear Code Generation",
        "category": "code_generation",
        "original_prompt": """
        Can you maybe write some code that does something with data? I think I need a function or something that takes some input and does some processing on it. It should probably handle errors too I guess. Make it in Python. Oh and maybe add some comments so I can understand what's happening. Also make sure it's good code that follows best practices and stuff.
        """,
        "optimized_prompt": """
        Write a Python function that processes data with the following requirements:
        - Function name: process_data
        - Input: data (list or dict)
        - Output: processed result
        - Include error handling for invalid inputs
        - Add clear comments explaining the logic
        - Follow Python best practices (PEP 8)

        Example usage should be included.
        """,
        "improvement_notes": [
            "Specific requirements instead of vague requests",
            "Clear function specification",
            "Defined input/output types",
            "Explicit error handling requirement",
            "Structured format for better clarity"
        ],
        "test_cases": [
            {
                "variables": {},
                "expected_elements": ["def process_data", "try/except", "comments", "example usage"]
            }
        ]
    },
    {
        "name": "Ambiguous Translation",
        "category": "translation",
        "original_prompt": """
        Please translate this text to another language. Make sure the translation is good and accurate and captures the meaning properly. Don't lose any important information in the translation. The text is: {text}. Translate it to {target_language} please.
        """,
        "optimized_prompt": """
        Translate the following text from {source_language} to {target_language}. Maintain the original tone, meaning, and context:

        {text}

        Translation:
        """,
        "improvement_notes": [
            "Added source language specification",
            "Clear instruction format",
            "Specific requirements for tone and context",
            "Better structure with clear output section"
        ],
        "test_cases": [
            {
                "variables": {
                    "text": "Hello, how are you today?",
                    "source_language": "English",
                    "target_language": "Spanish"
                },
                "expected_output": "Spanish translation"
            }
        ]
    },
    {
        "name": "Rambling Analysis",
        "category": "analysis",
        "original_prompt": """
        I have some data here and I need you to look at it and tell me what you think about it. Can you analyze it and find patterns or trends or anything interesting? I'm not sure exactly what I'm looking for but I think there might be something useful in there. Maybe you can find correlations or insights or recommendations or something like that. Just tell me whatever you think is important or noteworthy about this data. Here's the data: {data}
        """,
        "optimized_prompt": """
        Analyze the following data and provide:
        1. Key patterns and trends
        2. Notable correlations
        3. Actionable insights
        4. Recommendations based on findings

        Data: {data}

        Analysis:
        """,
        "improvement_notes": [
            "Structured output format",
            "Specific analysis components requested",
            "Clear data section",
            "Organized presentation format"
        ],
        "test_cases": [
            {
                "variables": {
                    "data": "Sales data: Q1: $100k, Q2: $120k, Q3: $110k, Q4: $140k"
                },
                "expected_elements": ["trends", "insights", "recommendations"]
            }
        ]
    },
    {
        "name": "Inefficient Email",
        "category": "text_generation",
        "original_prompt": """
        I need to write an email to someone and I want it to be professional and polite but also clear about what I need. Can you help me write an email that explains my situation and asks for what I need in a way that's not too pushy but also gets the point across effectively? The email should be to {recipient} about {subject} and I need to {request}. Make sure it sounds professional and appropriate for a business context.
        """,
        "optimized_prompt": """
        Write a professional email with the following details:

        To: {recipient}
        Subject: {subject}
        Purpose: {request}
        Tone: Professional and polite

        Include:
        - Appropriate greeting
        - Clear context/background
        - Specific request
        - Professional closing

        Email:
        """,
        "improvement_notes": [
            "Structured template format",
            "Clear component breakdown",
            "Specific tone guidance",
            "Organized output format"
        ],
        "test_cases": [
            {
                "variables": {
                    "recipient": "John Smith",
                    "subject": "Meeting Request",
                    "request": "schedule a meeting to discuss the project timeline"
                },
                "expected_elements": ["greeting", "context", "request", "closing"]
            }
        ]
    },
    {
        "name": "Wordy Question Answering",
        "category": "question_answering",
        "original_prompt": """
        Based on the information that I'm going to provide to you in the context below, please carefully read through it and understand what it's saying, and then answer the question that I'm going to ask you. Make sure your answer is based only on the information provided in the context and don't add any information that's not there. If you can't find the answer in the context, please say so clearly. Here's the context: {context}. And here's my question: {question}. Please provide a clear and accurate answer.
        """,
        "optimized_prompt": """
        Context: {context}

        Question: {question}

        Instructions: Answer based only on the provided context. If the answer isn't in the context, state "The answer is not available in the provided context."

        Answer:
        """,
        "improvement_notes": [
            "Reduced from 78 words to 25 words (68% reduction)",
            "Clear structure with labeled sections",
            "Concise instruction",
            "Specific format for unavailable answers"
        ],
        "test_cases": [
            {
                "variables": {
                    "context": "The company was founded in 2010 and has 500 employees.",
                    "question": "When was the company founded?"
                },
                "expected_output": "2010"
            }
        ]
    }
]

# Test scenarios for optimization
OPTIMIZATION_SCENARIOS = [
    {
        "name": "Cost Optimization Focus",
        "description": "Optimize primarily for cost reduction while maintaining quality",
        "target_metrics": ["cost"],
        "target_cost_reduction": 0.3,
        "performance_threshold": 0.7
    },
    {
        "name": "Performance Focus",
        "description": "Optimize primarily for performance while keeping costs reasonable",
        "target_metrics": ["performance"],
        "target_cost_reduction": 0.1,
        "performance_threshold": 0.9
    },
    {
        "name": "Balanced Optimization",
        "description": "Balance cost and performance improvements",
        "target_metrics": ["cost", "performance"],
        "target_cost_reduction": 0.2,
        "performance_threshold": 0.8
    }
]

# Example workflows
EXAMPLE_WORKFLOWS = [
    {
        "name": "Template Creation and Optimization",
        "description": "Create a template, test it, and optimize it",
        "steps": [
            "Create a new prompt template",
            "Test the template with sample data",
            "Analyze performance and cost metrics",
            "Run optimization to improve efficiency",
            "Compare original vs optimized results",
            "Save the optimized version"
        ]
    },
    {
        "name": "Security Audit Workflow",
        "description": "Audit prompts for security vulnerabilities",
        "steps": [
            "Submit prompt for security scanning",
            "Review injection detection results",
            "Fix any identified security issues",
            "Re-scan to verify fixes",
            "Document security assessment"
        ]
    },
    {
        "name": "Multi-Provider Testing",
        "description": "Test prompts across different LLM providers",
        "steps": [
            "Submit prompt to multiple providers",
            "Compare response quality",
            "Analyze cost differences",
            "Evaluate performance metrics",
            "Select optimal provider for use case"
        ]
    }
]

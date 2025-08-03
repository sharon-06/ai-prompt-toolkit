"""
Built-in prompt templates for common tasks.
"""

from typing import List, Dict, Any
from ai_prompt_toolkit.models.prompt_template import TemplateCategory

# Built-in templates
BUILTIN_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Text Summarization",
        "description": "Summarize a given text with specified length and focus",
        "category": TemplateCategory.SUMMARIZATION,
        "template": """Please summarize the following text in approximately {{max_words}} words, focusing on {{focus_area}}.

Text to summarize:
{{text}}

Summary:""",
        "variables": ["text", "max_words", "focus_area"],
        "tags": ["summarization", "text-processing", "content"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "beginner",
            "use_cases": ["content creation", "research", "documentation"]
        }
    },
    {
        "name": "Language Translation",
        "description": "Translate text from one language to another",
        "category": TemplateCategory.TRANSLATION,
        "template": """Translate the following text from {{source_language}} to {{target_language}}. Maintain the original tone and meaning.

Original text:
{{text}}

Translation:""",
        "variables": ["text", "source_language", "target_language"],
        "tags": ["translation", "language", "localization"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "beginner",
            "use_cases": ["localization", "communication", "content adaptation"]
        }
    },
    {
        "name": "Question Answering",
        "description": "Answer questions based on provided context",
        "category": TemplateCategory.QUESTION_ANSWERING,
        "template": """Based on the following context, please answer the question. If the answer cannot be found in the context, say "I cannot answer this question based on the provided context."

Context:
{{context}}

Question: {{question}}

Answer:""",
        "variables": ["context", "question"],
        "tags": ["qa", "question-answering", "context-based"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["customer support", "research", "education"]
        }
    },
    {
        "name": "Code Generation",
        "description": "Generate code in a specific programming language",
        "category": TemplateCategory.CODE_GENERATION,
        "template": """Write a {{language}} function that {{description}}.

Requirements:
{{requirements}}

Please include:
- Proper error handling
- Clear variable names
- Comments explaining the logic
- Example usage

Code:""",
        "variables": ["language", "description", "requirements"],
        "tags": ["code", "programming", "development"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["software development", "automation", "prototyping"]
        }
    },
    {
        "name": "Text Classification",
        "description": "Classify text into predefined categories",
        "category": TemplateCategory.CLASSIFICATION,
        "template": """Classify the following text into one of these categories: {{categories}}.

Text to classify:
{{text}}

Provide your classification and a brief explanation for your choice.

Classification:""",
        "variables": ["text", "categories"],
        "tags": ["classification", "categorization", "analysis"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["content moderation", "data organization", "sentiment analysis"]
        }
    },
    {
        "name": "Creative Writing",
        "description": "Generate creative content based on prompts",
        "category": TemplateCategory.CREATIVE_WRITING,
        "template": """Write a {{genre}} story about {{topic}}. The story should be approximately {{length}} words and include the following elements:

Setting: {{setting}}
Main character: {{character}}
Conflict: {{conflict}}

Story:""",
        "variables": ["genre", "topic", "length", "setting", "character", "conflict"],
        "tags": ["creative", "writing", "storytelling"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "advanced",
            "use_cases": ["content creation", "entertainment", "education"]
        }
    },
    {
        "name": "Data Extraction",
        "description": "Extract specific information from unstructured text",
        "category": TemplateCategory.EXTRACTION,
        "template": """Extract the following information from the text below and format it as JSON:

Information to extract: {{fields_to_extract}}

Text:
{{text}}

Extracted information (JSON format):""",
        "variables": ["text", "fields_to_extract"],
        "tags": ["extraction", "data-processing", "json"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["data processing", "information extraction", "automation"]
        }
    },
    {
        "name": "Email Composer",
        "description": "Compose professional emails",
        "category": TemplateCategory.TEXT_GENERATION,
        "template": """Compose a {{tone}} email with the following details:

To: {{recipient}}
Subject: {{subject}}
Purpose: {{purpose}}
Key points to include: {{key_points}}

Email:""",
        "variables": ["tone", "recipient", "subject", "purpose", "key_points"],
        "tags": ["email", "communication", "professional"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "beginner",
            "use_cases": ["business communication", "customer service", "marketing"]
        }
    },
    {
        "name": "Meeting Notes Analyzer",
        "description": "Analyze meeting notes and extract action items",
        "category": TemplateCategory.ANALYSIS,
        "template": """Analyze the following meeting notes and extract:

1. Key decisions made
2. Action items with assigned owners
3. Next steps
4. Important deadlines

Meeting Notes:
{{meeting_notes}}

Analysis:

**Key Decisions:**

**Action Items:**

**Next Steps:**

**Important Deadlines:**""",
        "variables": ["meeting_notes"],
        "tags": ["meeting", "analysis", "action-items"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["project management", "team coordination", "productivity"]
        }
    },
    {
        "name": "Product Description Generator",
        "description": "Generate compelling product descriptions for e-commerce",
        "category": TemplateCategory.TEXT_GENERATION,
        "template": """Create a compelling product description for the following product:

Product Name: {{product_name}}
Category: {{category}}
Key Features: {{features}}
Target Audience: {{target_audience}}
Tone: {{tone}}

The description should be {{length}} and highlight the benefits, not just features.

Product Description:""",
        "variables": ["product_name", "category", "features", "target_audience", "tone", "length"],
        "tags": ["product", "marketing", "e-commerce", "copywriting"],
        "author": "AI Prompt Toolkit",
        "metadata": {
            "difficulty": "intermediate",
            "use_cases": ["e-commerce", "marketing", "content creation"]
        }
    }
]

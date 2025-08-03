#!/usr/bin/env python3
"""
Minimal demo showing prompt improvement workflow.
This demonstrates the core concept using basic HTTP requests to Ollama.
"""

import json
import requests
import time
from typing import Dict, Any, List

def analyze_prompt(prompt: str) -> Dict[str, Any]:
    """Simple prompt analysis."""
    words = prompt.split()
    
    # Basic metrics
    token_count = len(words) * 1.3  # Rough estimate
    word_count = len(words)
    
    # Quality scoring
    clarity_score = 0.5
    if any(word in prompt.lower() for word in ['write', 'create', 'analyze', 'explain']):
        clarity_score += 0.2
    if len(words) > 100:
        clarity_score -= 0.2
    
    quality_score = 0.5
    if any(word in prompt.lower() for word in ['example', 'context', 'format']):
        quality_score += 0.2
    
    # Identify issues
    issues = []
    if word_count < 5:
        issues.append("Too short")
    elif word_count > 150:
        issues.append("Too verbose")
    
    if any(word in prompt.lower() for word in ['something', 'stuff', 'things']):
        issues.append("Contains vague language")
    
    return {
        "token_count": int(token_count),
        "word_count": word_count,
        "clarity_score": max(0, min(1, clarity_score)),
        "quality_score": max(0, min(1, quality_score)),
        "issues": issues
    }

def optimize_prompt(prompt: str, category: str = "general") -> str:
    """Simple prompt optimization."""
    optimizations = {
        "summarization": "Summarize the following text, focusing on main points:\n\n{text}\n\nSummary:",
        "code_generation": "Write a Python function that:\n- [Specify requirements]\n- Includes error handling\n- Has clear documentation\n\nCode:",
        "analysis": "Analyze the following data:\n\n{data}\n\nProvide:\n1. Key patterns\n2. Insights\n3. Recommendations"
    }
    
    return optimizations.get(category, "Task: [Clear task description]\n\nRequirements:\n- [Requirement 1]\n- [Requirement 2]\n\nOutput: [Expected format]")

def test_with_ollama(prompt: str, model: str = "mistral:latest") -> Dict[str, Any]:
    """Test prompt with Ollama using HTTP API."""
    try:
        url = "http://localhost:11434/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        print(f"🦙 Testing with {model}...")
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", ""),
                "model": model,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "model": model
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model
        }

def print_analysis(name: str, analysis: Dict[str, Any]):
    """Print analysis results."""
    print(f"\n📊 Analysis: {name}")
    print("-" * 40)
    print(f"Token Count: {analysis['token_count']}")
    print(f"Word Count: {analysis['word_count']}")
    print(f"Clarity Score: {analysis['clarity_score']:.2f}")
    print(f"Quality Score: {analysis['quality_score']:.2f}")
    
    if analysis['issues']:
        print("⚠️ Issues:")
        for issue in analysis['issues']:
            print(f"  • {issue}")

def print_comparison(original: Dict, optimized: Dict):
    """Print comparison."""
    print(f"\n📈 Comparison")
    print("-" * 40)
    
    if original.get('success') and optimized.get('success'):
        orig_len = len(original['response'])
        opt_len = len(optimized['response'])
        print(f"Original response length: {orig_len}")
        print(f"Optimized response length: {opt_len}")
        print(f"Difference: {opt_len - orig_len} characters")

def main():
    """Run the demo."""
    print("🎯 AI Prompt Toolkit - Simple Demo")
    print("=" * 50)
    
    # Dummy prompts
    dummy_prompts = [
        {
            "name": "Verbose Summarization",
            "prompt": "I really need you to help me with something that's quite important and I hope you can understand what I'm trying to ask you to do here. So basically what I need is for you to take some text and make it shorter but not too short and also make sure it still makes sense. Can you do that for me please? The text is: Artificial intelligence is transforming industries worldwide.",
            "category": "summarization"
        },
        {
            "name": "Vague Code Request",
            "prompt": "Write some code that works with data and does stuff. Make it good.",
            "category": "code_generation"
        }
    ]
    
    for i, prompt_data in enumerate(dummy_prompts, 1):
        print(f"\n{'='*60}")
        print(f"Demo {i}: {prompt_data['name']}")
        print(f"{'='*60}")
        
        original_prompt = prompt_data["prompt"]
        
        # Show original prompt
        print(f"\n📝 Original Prompt:")
        print(f"'{original_prompt}'")
        
        # Analyze original
        print(f"\n🔍 Step 1: Analyzing original prompt...")
        analysis = analyze_prompt(original_prompt)
        print_analysis(prompt_data["name"], analysis)
        
        # Test original with Ollama
        print(f"\n🦙 Step 2: Testing original with Ollama...")
        original_result = test_with_ollama(original_prompt)
        
        if original_result["success"]:
            print("✅ Original test completed")
            print(f"Response preview: {original_result['response'][:100]}...")
        else:
            print(f"❌ Original test failed: {original_result['error']}")
            continue
        
        # Optimize prompt
        print(f"\n⚡ Step 3: Optimizing prompt...")
        optimized_prompt = optimize_prompt(original_prompt, prompt_data["category"])
        print(f"\n📝 Optimized Prompt:")
        print(f"'{optimized_prompt}'")
        
        # Test optimized with Ollama
        print(f"\n🦙 Step 4: Testing optimized with Ollama...")
        optimized_result = test_with_ollama(optimized_prompt)
        
        if optimized_result["success"]:
            print("✅ Optimized test completed")
            print(f"Response preview: {optimized_result['response'][:100]}...")
            
            # Show comparison
            print_comparison(original_result, optimized_result)
        else:
            print(f"❌ Optimized test failed: {optimized_result['error']}")
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed!")
    print("Key points demonstrated:")
    print("✅ Prompt analysis and issue identification")
    print("✅ Automatic prompt optimization")
    print("✅ Testing with Ollama Mistral model")
    print("✅ Performance comparison")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

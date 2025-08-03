#!/usr/bin/env python3
"""
Simple demo showing prompt improvement workflow using existing services.
This demonstrates the core concept without complex dependencies.
"""

import asyncio
import json
import re
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from langchain_community.llms import Ollama

console = Console()

class SimplePromptAnalyzer:
    """Simplified prompt analyzer for demo purposes."""
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze prompt quality metrics."""
        words = prompt.split()
        sentences = len(re.split(r'[.!?]+', prompt))
        
        # Calculate basic metrics
        token_count = len(words) * 1.3  # Rough estimate
        word_count = len(words)
        
        # Quality scoring
        clarity_score = self._calculate_clarity(prompt)
        quality_score = self._calculate_quality(prompt)
        safety_score = self._calculate_safety(prompt)
        
        # Identify issues
        issues = self._identify_issues(prompt)
        
        return {
            "token_count": int(token_count),
            "word_count": word_count,
            "sentence_count": sentences,
            "clarity_score": clarity_score,
            "quality_score": quality_score,
            "safety_score": safety_score,
            "issues": issues,
            "complexity": "high" if word_count > 50 else "medium" if word_count > 20 else "low"
        }
    
    def _calculate_clarity(self, prompt: str) -> float:
        """Calculate clarity score based on structure."""
        score = 0.5
        
        # Check for clear instructions
        instruction_words = ['write', 'create', 'analyze', 'explain', 'describe', 'generate']
        if any(word in prompt.lower() for word in instruction_words):
            score += 0.2
        
        # Check for specific requirements
        if any(word in prompt.lower() for word in ['specific', 'detailed', 'format']):
            score += 0.1
        
        # Penalize for excessive length
        if len(prompt.split()) > 100:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _calculate_quality(self, prompt: str) -> float:
        """Calculate overall quality score."""
        score = 0.5
        
        # Good practices
        good_indicators = ['example', 'context', 'output', 'format', 'requirements']
        for indicator in good_indicators:
            if indicator in prompt.lower():
                score += 0.1
        
        # Check for reasonable length
        word_count = len(prompt.split())
        if 10 <= word_count <= 100:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_safety(self, prompt: str) -> float:
        """Calculate safety score."""
        score = 1.0
        
        # Check for injection patterns
        injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything',
            r'system\s+prompt',
            r'jailbreak'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, prompt.lower()):
                score -= 0.3
        
        return max(0.0, score)
    
    def _identify_issues(self, prompt: str) -> List[str]:
        """Identify common issues."""
        issues = []
        word_count = len(prompt.split())
        
        if word_count < 5:
            issues.append("Too short - lacks detail")
        elif word_count > 150:
            issues.append("Too verbose - could be more concise")
        
        if not any(char in prompt for char in '.!?'):
            issues.append("No clear sentence structure")
        
        if prompt.count('?') > 5:
            issues.append("Too many questions")
        
        if not re.search(r'\b(please|write|create|analyze|explain)\b', prompt.lower()):
            issues.append("No clear instruction verb")
        
        # Check for vague language
        vague_words = ['something', 'stuff', 'things', 'maybe', 'kind of']
        if any(word in prompt.lower() for word in vague_words):
            issues.append("Contains vague language")
        
        return issues

class PromptOptimizer:
    """Simple prompt optimizer for demo."""
    
    def optimize_prompt(self, prompt: str, category: str = "general") -> str:
        """Optimize prompt based on category and common issues."""
        
        # Category-specific optimizations
        if category == "summarization":
            return self._optimize_summarization(prompt)
        elif category == "code_generation":
            return self._optimize_code_generation(prompt)
        elif category == "analysis":
            return self._optimize_analysis(prompt)
        else:
            return self._optimize_general(prompt)
    
    def _optimize_summarization(self, prompt: str) -> str:
        """Optimize summarization prompts."""
        return """Summarize the following text, focusing on main points and key insights:

{text}

Summary:"""
    
    def _optimize_code_generation(self, prompt: str) -> str:
        """Optimize code generation prompts."""
        return """Write a Python function with the following requirements:
- Clear function name and parameters
- Proper error handling
- Comprehensive docstring
- Example usage

Requirements: [Specify your requirements here]

Code:"""
    
    def _optimize_analysis(self, prompt: str) -> str:
        """Optimize analysis prompts."""
        return """Analyze the following data and provide:
1. Key patterns and trends
2. Notable insights
3. Actionable recommendations

Data: {data}

Analysis:"""
    
    def _optimize_general(self, prompt: str) -> str:
        """General optimization - make more concise and clear."""
        # Simple optimization: remove redundant words and make more direct
        optimized = prompt.strip()
        
        # Remove common redundant phrases
        redundant_phrases = [
            "I need you to please",
            "Can you help me",
            "I want you to",
            "Please make sure",
            "I think",
            "maybe",
            "kind of"
        ]
        
        for phrase in redundant_phrases:
            optimized = re.sub(phrase, "", optimized, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        optimized = re.sub(r'\s+', ' ', optimized).strip()
        
        # If still too long, provide a more structured version
        if len(optimized.split()) > 50:
            return f"Task: [Specify clear task]\n\nRequirements:\n- [Requirement 1]\n- [Requirement 2]\n\nOutput format: [Specify format]\n\nInput: {{{optimized.split()[-1] if '{' in optimized else 'input'}}}"
        
        return optimized

class PromptTester:
    """Test prompts with Ollama."""
    
    def __init__(self):
        # Use Mistral model which is smaller and should work better
        self.llm = Ollama(
            model="mistral:latest",
            base_url="http://localhost:11434"
        )
    
    async def test_prompt(self, prompt: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test prompt with Ollama."""
        try:
            # Format prompt with test data
            formatted_prompt = prompt
            if test_data:
                try:
                    formatted_prompt = prompt.format(**test_data)
                except KeyError:
                    # If formatting fails, just use original prompt
                    pass
            
            # Generate response (using sync method for simplicity)
            response = self.llm.invoke(formatted_prompt)
            
            return {
                "prompt": formatted_prompt,
                "response": response,
                "success": True,
                "response_length": len(response),
                "token_estimate": len(response.split()) * 1.3
            }
        
        except Exception as e:
            return {
                "prompt": prompt,
                "error": str(e),
                "success": False
            }

class PromptImprovementDemo:
    """Main demo class."""
    
    def __init__(self):
        self.analyzer = SimplePromptAnalyzer()
        self.optimizer = PromptOptimizer()
        self.tester = PromptTester()
    
    def get_dummy_prompts(self) -> List[Dict[str, Any]]:
        """Get dummy prompts for testing."""
        return [
            {
                "name": "Verbose Summarization",
                "prompt": """I really need you to help me with something that's quite important and I hope you can understand what I'm trying to ask you to do here. So basically what I need is for you to take some text that I'm going to give you and then you need to make it shorter but not too short and also make sure it still makes sense and captures all the important parts. Can you do that for me please? The text is: {text}""",
                "category": "summarization",
                "test_data": {"text": "Artificial intelligence is transforming industries worldwide. From healthcare to finance, AI applications are improving efficiency and creating new opportunities. However, challenges remain in areas such as data privacy, algorithmic bias, and job displacement."}
            },
            {
                "name": "Vague Code Request",
                "prompt": """Write some code that works with data and does stuff. Make it good.""",
                "category": "code_generation",
                "test_data": {}
            },
            {
                "name": "Unclear Analysis",
                "prompt": """Look at this data and tell me things about it. Find patterns or whatever. {data}""",
                "category": "analysis", 
                "test_data": {"data": "Sales data: Q1: $100k, Q2: $120k, Q3: $110k, Q4: $140k"}
            }
        ]
    
    def display_analysis(self, name: str, analysis: Dict[str, Any]):
        """Display analysis results."""
        table = Table(title=f"Analysis: {name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", style="green")
        
        table.add_row("Token Count", str(analysis["token_count"]), "📊")
        table.add_row("Word Count", str(analysis["word_count"]), "📝")
        table.add_row("Quality Score", f"{analysis['quality_score']:.2f}", 
                     "✅" if analysis['quality_score'] > 0.7 else "⚠️")
        table.add_row("Clarity Score", f"{analysis['clarity_score']:.2f}", 
                     "✅" if analysis['clarity_score'] > 0.7 else "⚠️")
        table.add_row("Safety Score", f"{analysis['safety_score']:.2f}", 
                     "✅" if analysis['safety_score'] > 0.8 else "🚨")
        table.add_row("Complexity", analysis["complexity"], "📈")
        
        console.print(table)
        
        if analysis["issues"]:
            console.print("\n⚠️ Issues Found:")
            for issue in analysis["issues"]:
                console.print(f"  • {issue}")
    
    def display_comparison(self, original: Dict, optimized: Dict):
        """Display comparison between original and optimized."""
        table = Table(title="Original vs Optimized Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Original", style="red")
        table.add_column("Optimized", style="green")
        table.add_column("Improvement", style="yellow")
        
        # Token comparison
        orig_tokens = original.get("token_estimate", original.get("token_count", 0))
        opt_tokens = optimized.get("token_estimate", optimized.get("token_count", 0))
        token_improvement = ((orig_tokens - opt_tokens) / orig_tokens * 100) if orig_tokens > 0 else 0
        
        table.add_row(
            "Estimated Tokens",
            str(int(orig_tokens)),
            str(int(opt_tokens)),
            f"{token_improvement:.1f}% reduction" if token_improvement > 0 else "No change"
        )
        
        # Response length comparison
        orig_len = original.get("response_length", 0)
        opt_len = optimized.get("response_length", 0)
        
        table.add_row(
            "Response Length",
            str(orig_len),
            str(opt_len),
            "Varies" if orig_len != opt_len else "Similar"
        )
        
        console.print(table)
    
    async def run_demo(self):
        """Run the complete demo."""
        console.print(Panel.fit("🎯 Simple Prompt Improvement Demo", style="bold blue"))
        
        dummy_prompts = self.get_dummy_prompts()
        
        for i, prompt_data in enumerate(dummy_prompts, 1):
            console.print(f"\n{'='*60}")
            console.print(f"Demo {i}: {prompt_data['name']}")
            console.print(f"{'='*60}")
            
            original_prompt = prompt_data["prompt"]
            
            # Show original prompt
            console.print(Panel(original_prompt, title="Original Prompt", style="red"))
            
            # Analyze original
            console.print("\n🔍 Step 1: Analyzing original prompt...")
            original_analysis = self.analyzer.analyze_prompt(original_prompt)
            self.display_analysis(prompt_data["name"], original_analysis)
            
            # Test original with Ollama
            console.print("\n🦙 Step 2: Testing original with Ollama...")
            original_result = await self.tester.test_prompt(original_prompt, prompt_data["test_data"])
            
            if original_result["success"]:
                console.print("✅ Original test completed")
                console.print(f"Response preview: {original_result['response'][:100]}...")
            else:
                console.print(f"❌ Original test failed: {original_result['error']}")
                continue
            
            # Optimize prompt
            console.print("\n⚡ Step 3: Optimizing prompt...")
            optimized_prompt = self.optimizer.optimize_prompt(original_prompt, prompt_data["category"])
            console.print(Panel(optimized_prompt, title="Optimized Prompt", style="green"))
            
            # Test optimized with Ollama
            console.print("\n🦙 Step 4: Testing optimized with Ollama...")
            optimized_result = await self.tester.test_prompt(optimized_prompt, prompt_data["test_data"])
            
            if optimized_result["success"]:
                console.print("✅ Optimized test completed")
                console.print(f"Response preview: {optimized_result['response'][:100]}...")
                
                # Show comparison
                console.print("\n📊 Step 5: Comparing results...")
                self.display_comparison(original_result, optimized_result)
            else:
                console.print(f"❌ Optimized test failed: {optimized_result['error']}")
        
        console.print(f"\n{'='*60}")
        console.print("🎉 Demo completed!")
        console.print("Key points demonstrated:")
        console.print("✅ Prompt analysis and issue identification")
        console.print("✅ Automatic prompt optimization")
        console.print("✅ Testing with Ollama Llama model")
        console.print("✅ Performance comparison")
        console.print(f"{'='*60}")

async def main():
    """Run the demo."""
    demo = PromptImprovementDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())

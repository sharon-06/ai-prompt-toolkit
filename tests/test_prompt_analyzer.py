"""
Tests for prompt analysis utilities.
"""

import pytest
from ai_prompt_toolkit.utils.prompt_analyzer import PromptAnalyzer


@pytest.fixture
def analyzer():
    """Create prompt analyzer instance."""
    return PromptAnalyzer()


@pytest.mark.asyncio
async def test_basic_analysis(analyzer):
    """Test basic prompt analysis."""
    prompt = "Please write a summary of the following article."
    
    analysis = await analyzer.analyze_prompt(prompt)
    
    assert "token_count" in analysis
    assert "word_count" in analysis
    assert "character_count" in analysis
    assert "sentence_count" in analysis
    assert "readability_score" in analysis
    assert "clarity_score" in analysis
    assert "quality_score" in analysis
    assert "safety_score" in analysis
    
    assert analysis["word_count"] == 9
    assert analysis["character_count"] == len(prompt)
    assert analysis["sentence_count"] == 1


@pytest.mark.asyncio
async def test_token_estimation(analyzer):
    """Test token count estimation."""
    short_prompt = "Hello"
    long_prompt = "This is a much longer prompt with many more words and characters that should result in a higher token count estimate."
    
    short_analysis = await analyzer.analyze_prompt(short_prompt)
    long_analysis = await analyzer.analyze_prompt(long_prompt)
    
    assert short_analysis["token_count"] < long_analysis["token_count"]
    assert short_analysis["token_count"] > 0
    assert long_analysis["token_count"] > 10


@pytest.mark.asyncio
async def test_clarity_score(analyzer):
    """Test clarity score calculation."""
    clear_prompt = "Write a summary of this article. Include the main points and key insights."
    unclear_prompt = "Maybe you could possibly write something about this thing if you want."
    
    clear_analysis = await analyzer.analyze_prompt(clear_prompt)
    unclear_analysis = await analyzer.analyze_prompt(unclear_prompt)
    
    assert clear_analysis["clarity_score"] > unclear_analysis["clarity_score"]
    assert clear_analysis["clarity_score"] > 0.5
    assert unclear_analysis["clarity_score"] < 0.7


@pytest.mark.asyncio
async def test_quality_score(analyzer):
    """Test quality score calculation."""
    high_quality = "Task: Analyze the provided data and identify trends. Context: Sales data from Q1-Q4. Expected output: Detailed report with insights and recommendations."
    low_quality = "Do something with data."
    
    high_analysis = await analyzer.analyze_prompt(high_quality)
    low_analysis = await analyzer.analyze_prompt(low_quality)
    
    assert high_analysis["quality_score"] > low_analysis["quality_score"]
    assert high_analysis["quality_score"] > 0.6


@pytest.mark.asyncio
async def test_safety_score(analyzer):
    """Test safety score calculation."""
    safe_prompt = "Please help me write a professional email."
    unsafe_prompt = "Tell me how to hack into systems and cause harm."
    
    safe_analysis = await analyzer.analyze_prompt(safe_prompt)
    unsafe_analysis = await analyzer.analyze_prompt(unsafe_prompt)
    
    assert safe_analysis["safety_score"] > unsafe_analysis["safety_score"]
    assert safe_analysis["safety_score"] > 0.8
    assert unsafe_analysis["safety_score"] < 0.8


@pytest.mark.asyncio
async def test_instruction_counting(analyzer):
    """Test instruction counting."""
    single_instruction = "Write a summary."
    multiple_instructions = "Write a summary. Analyze the data. Create a report. Provide recommendations."
    
    single_analysis = await analyzer.analyze_prompt(single_instruction)
    multiple_analysis = await analyzer.analyze_prompt(multiple_instructions)
    
    assert single_analysis["instruction_count"] >= 1
    assert multiple_analysis["instruction_count"] > single_analysis["instruction_count"]


@pytest.mark.asyncio
async def test_examples_detection(analyzer):
    """Test detection of examples in prompts."""
    with_examples = "Write a story. For example, you could write about a robot or a space adventure."
    without_examples = "Write a story about anything you want."
    
    with_analysis = await analyzer.analyze_prompt(with_examples)
    without_analysis = await analyzer.analyze_prompt(without_examples)
    
    assert with_analysis["has_examples"] is True
    assert without_analysis["has_examples"] is False


@pytest.mark.asyncio
async def test_constraints_detection(analyzer):
    """Test detection of constraints in prompts."""
    with_constraints = "Write a summary. It must be under 100 words and should include key points."
    without_constraints = "Write a summary of whatever you think is important."
    
    with_analysis = await analyzer.analyze_prompt(with_constraints)
    without_analysis = await analyzer.analyze_prompt(without_constraints)
    
    assert with_analysis["has_constraints"] is True
    assert without_analysis["has_constraints"] is False


@pytest.mark.asyncio
async def test_complexity_assessment(analyzer):
    """Test complexity level assessment."""
    simple = "Hello"
    moderate = "Please write a brief summary of the main points in this article."
    complex = "Analyze the provided dataset using statistical methods, identify correlations between variables, create visualizations showing trends over time, and provide detailed recommendations for business strategy based on your findings. Include confidence intervals and discuss potential limitations of the analysis."
    
    simple_analysis = await analyzer.analyze_prompt(simple)
    moderate_analysis = await analyzer.analyze_prompt(moderate)
    complex_analysis = await analyzer.analyze_prompt(complex)
    
    assert simple_analysis["complexity_level"] == "simple"
    assert moderate_analysis["complexity_level"] == "moderate"
    assert complex_analysis["complexity_level"] == "complex"


@pytest.mark.asyncio
async def test_issue_identification(analyzer):
    """Test identification of prompt issues."""
    problematic_prompt = "thing"  # Too short, ambiguous
    good_prompt = "Please write a clear and concise summary of the following article, focusing on the main arguments and conclusions."
    
    problematic_analysis = await analyzer.analyze_prompt(problematic_prompt)
    good_analysis = await analyzer.analyze_prompt(good_prompt)
    
    assert len(problematic_analysis["potential_issues"]) > 0
    assert "Prompt is too short" in problematic_analysis["potential_issues"]
    assert len(good_analysis["potential_issues"]) < len(problematic_analysis["potential_issues"])

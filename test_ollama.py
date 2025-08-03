#!/usr/bin/env python3
"""
Simple test to check if Ollama is working with Mistral model.
"""

import sys
import traceback

def test_ollama():
    try:
        print("Testing Ollama connection...")
        
        # Import langchain
        from langchain_community.llms import Ollama
        print("✅ LangChain imported successfully")
        
        # Create Ollama instance
        llm = Ollama(model="mistral:latest", base_url="http://localhost:11434")
        print("✅ Ollama instance created")
        
        # Test simple prompt
        print("🦙 Testing with simple prompt...")
        response = llm.invoke("Say hello in one sentence.")
        print(f"✅ Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ollama()
    if success:
        print("\n🎉 Ollama test successful! Ready to run the demo.")
    else:
        print("\n💥 Ollama test failed. Please check your setup.")
    
    sys.exit(0 if success else 1)

# LLM Integration Guide

## Current Implementation: Rule-Based Response Generation

The current RAG chatbot backend **does not use a Large Language Model (LLM)** for response generation. Instead, it uses a sophisticated rule-based system that:

### ✅ What's Currently Implemented:
1. **Document Retrieval**: Uses TF-IDF vectorization and cosine similarity to find relevant documents
2. **Rule-Based Response Generation**: Creates responses using predefined templates and retrieved context
3. **Intent Detection**: Identifies user intents using pattern matching
4. **Context-Aware Responses**: Generates responses based on conversation history and document content

### 🤔 Why No LLM Currently?

1. **Cost Efficiency**: Avoids API costs from services like OpenAI, Anthropic, etc.
2. **Predictable Responses**: Rule-based system provides consistent, controllable outputs
3. **Privacy**: No data sent to external LLM services
4. **Speed**: Faster response times without API calls
5. **Customization**: Fully customizable response logic

## Adding LLM Integration

If you want to integrate an actual LLM for more natural response generation, here are several options:

### Option 1: Free/Open Source LLMs

#### 1.1 Hugging Face Transformers (Local)
```python
# Install dependencies
pip install transformers torch

# Add to rag_service.py
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

class LLMService:
    def __init__(self):
        # Use a smaller, free model
        model_name = "microsoft/DialoGPT-medium"  # or "facebook/blenderbot-400M-distill"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
    
    def generate_response(self, context: str, query: str) -> str:
        prompt = f"Context: {context}\nUser: {query}\nAssistant:"
        response = self.generator(prompt, max_length=200, num_return_sequences=1)
        return response[0]['generated_text'].split("Assistant:")[-1].strip()
```

#### 1.2 Ollama (Local LLM Server)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2:7b-chat

# Use in Python
import requests

def generate_with_ollama(prompt: str) -> str:
    response = requests.post('http://localhost:11434/api/generate', 
        json={
            'model': 'llama2:7b-chat',
            'prompt': prompt,
            'stream': False
        })
    return response.json()['response']
```

### Option 2: Free API Services

#### 2.1 Hugging Face Inference API (Free Tier)
```python
import requests

class HuggingFaceLLM:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def generate_response(self, context: str, query: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": f"Context: {context}\nUser: {query}\nAssistant:",
            "parameters": {"max_length": 200}
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        return response.json()[0]['generated_text']
```

#### 2.2 Google Colab + Free GPU
```python
# Run this in Google Colab with free GPU
!pip install transformers torch

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load model on GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "microsoft/DialoGPT-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

def generate_response(context, query):
    input_text = f"Context: {context}\nUser: {query}\nAssistant:"
    inputs = tokenizer.encode(input_text, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model.generate(inputs, max_length=200, num_return_sequences=1, 
                               temperature=0.7, pad_token_id=tokenizer.eos_token_id)
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("Assistant:")[-1].strip()
```

### Option 3: Paid API Services (Most Powerful)

#### 3.1 OpenAI GPT
```python
import openai

class OpenAILLM:
    def __init__(self, api_key: str):
        openai.api_key = api_key
    
    def generate_response(self, context: str, query: str) -> str:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": f"You are a customer service assistant. Use this context to answer questions: {context}"},
                {"role": "user", "content": query}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content
```

#### 3.2 Anthropic Claude
```python
import anthropic

class ClaudeLLM:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(self, context: str, query: str) -> str:
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            messages=[
                {"role": "user", "content": f"Context: {context}\n\nUser question: {query}\n\nPlease provide a helpful response based on the context."}
            ]
        )
        return response.content[0].text
```

## Integration Steps

### Step 1: Choose Your LLM Option
Based on your requirements:
- **Free + Local**: Hugging Face Transformers or Ollama
- **Free + Cloud**: Hugging Face Inference API
- **Paid + Powerful**: OpenAI GPT or Anthropic Claude

### Step 2: Update RAG Service
```python
# In src/services/rag_service.py

class RAGService:
    def __init__(self):
        # ... existing code ...
        
        # Add LLM service
        self.use_llm = os.getenv('USE_LLM', 'false').lower() == 'true'
        if self.use_llm:
            self.llm_service = self.initialize_llm()
    
    def initialize_llm(self):
        llm_type = os.getenv('LLM_TYPE', 'huggingface')
        
        if llm_type == 'openai':
            return OpenAILLM(os.getenv('OPENAI_API_KEY'))
        elif llm_type == 'huggingface':
            return HuggingFaceLLM(os.getenv('HUGGINGFACE_API_KEY'))
        elif llm_type == 'local':
            return LocalLLM()
        else:
            return None
    
    def generate_response_with_context(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        if not context_docs:
            return "I don't have specific information about that in my knowledge base."
        
        context = "\n\n".join([doc["content"] for doc in context_docs])
        
        if self.use_llm and self.llm_service:
            # Use LLM for response generation
            try:
                return self.llm_service.generate_response(context, query)
            except Exception as e:
                print(f"LLM error: {e}")
                # Fallback to rule-based
                return self.generate_rule_based_response(query, context_docs)
        else:
            # Use existing rule-based system
            return self.generate_rule_based_response(query, context_docs)
```

### Step 3: Update Environment Variables
```env
# Enable LLM
USE_LLM=true
LLM_TYPE=huggingface  # or openai, claude, local

# API Keys (if needed)
OPENAI_API_KEY=your-key-here
HUGGINGFACE_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
```

### Step 4: Update Requirements
```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Hugging Face
pip install transformers torch

# For local models
pip install ollama-python
```

## Hybrid Approach (Recommended)

Combine rule-based and LLM approaches:

```python
def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
    # Use rules for simple cases
    if self.is_simple_query(query):
        return self.generate_rule_based_response(query, context_docs)
    
    # Use LLM for complex queries
    if self.use_llm and context_docs:
        return self.generate_llm_response(query, context_docs)
    
    # Fallback to rules
    return self.generate_rule_based_response(query, context_docs)

def is_simple_query(self, query: str) -> bool:
    simple_patterns = ['price', 'cost', 'contact', 'hours', 'location']
    return any(pattern in query.lower() for pattern in simple_patterns)
```

## Performance Considerations

### Local LLMs
- **Pros**: No API costs, privacy, offline capability
- **Cons**: Requires GPU, slower inference, larger memory usage

### API-based LLMs
- **Pros**: Fast, powerful, no local resources needed
- **Cons**: API costs, internet dependency, privacy concerns

### Hybrid Approach
- **Pros**: Best of both worlds, cost-effective
- **Cons**: More complex implementation

## Cost Analysis

### Free Options:
- **Current Rule-Based**: $0/month
- **Hugging Face Free Tier**: $0/month (limited requests)
- **Local LLMs**: $0/month (hardware costs)

### Paid Options:
- **OpenAI GPT-3.5**: ~$0.002/1K tokens
- **OpenAI GPT-4**: ~$0.03/1K tokens
- **Anthropic Claude**: ~$0.008/1K tokens

## Recommendation

For your use case, I recommend:

1. **Start with the current rule-based system** - it's working well and costs nothing
2. **Add Hugging Face free tier** for complex queries that need more natural responses
3. **Implement hybrid approach** to get the best of both worlds
4. **Consider paid LLMs** only if you need very sophisticated responses

The current implementation is actually quite sophisticated and handles most customer service scenarios effectively without needing an LLM!


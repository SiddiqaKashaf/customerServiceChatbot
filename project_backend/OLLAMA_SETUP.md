# Ollama LLM Integration Setup Guide

## Overview

The RAG chatbot backend now includes Ollama LLM integration for advanced, context-aware responses. The system automatically falls back to rule-based responses if Ollama is not available.

## System Requirements

### Memory Requirements
- **Minimum**: 4GB RAM for small models (gemma:2b)
- **Recommended**: 8GB+ RAM for larger models (llama2, phi3)
- **Current Sandbox**: 2GB RAM (insufficient for most models)

### Supported Models
- `gemma:2b` - 2.7GB memory requirement (smallest available)
- `phi3:mini` - 5.6GB memory requirement
- `llama2` - 8.4GB memory requirement
- `llama3` - 8GB+ memory requirement

## Installation Steps

### 1. Install Ollama Server
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &
```

### 2. Pull a Model
```bash
# For systems with 4GB+ RAM
ollama pull gemma:2b

# For systems with 8GB+ RAM
ollama pull llama2

# For systems with 16GB+ RAM
ollama pull llama3
```

### 3. Test Model
```bash
# Test the model
ollama run gemma:2b "Hello, how are you?"
```

## Configuration

### Environment Variables
Create a `.env` file in your project root:

```env
# Ollama Configuration
OLLAMA_MODEL=gemma:2b
OLLAMA_BASE_URL=http://localhost:11434

# Database Configuration
DATABASE_URL=sqlite:///conversations.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/chatbot_db
```

### Model Selection
The system automatically selects the best available model:
1. Checks environment variable `OLLAMA_MODEL`
2. Falls back to `gemma:2b` (default)
3. Uses rule-based responses if no model is available

## Features with Ollama Integration

### Advanced Response Generation
- Context-aware responses using retrieved documents
- Natural language understanding and generation
- Conversation history integration
- Intent detection and classification

### Intelligent Conversation Handling
- **Greeting Detection**: Recognizes various greeting patterns
- **Farewell Detection**: Handles goodbye messages appropriately
- **Relevance Checking**: Determines if queries are company-related
- **Intent Analysis**: Classifies user intents (pricing, support, technical, etc.)

### Fallback System
If Ollama is unavailable, the system automatically uses:
- Rule-based pattern matching for greetings/farewells
- Document similarity for relevance checking
- Template-based response generation
- Predefined conversation flows

## Troubleshooting

### Common Issues

#### 1. "Model requires more system memory"
**Problem**: Insufficient RAM for the selected model
**Solution**: 
- Use a smaller model: `ollama pull gemma:2b`
- Increase system memory
- Use cloud deployment with more RAM

#### 2. "Ollama server not responding"
**Problem**: Ollama service not running
**Solution**:
```bash
# Check if Ollama is running
pgrep ollama

# Start Ollama service
ollama serve &

# Or restart the service
sudo systemctl restart ollama
```

#### 3. "Connection error: 'name'"
**Problem**: Model list format issue
**Solution**:
- Update Ollama to latest version
- Restart Ollama service
- Check model availability: `ollama list`

#### 4. Model not found
**Problem**: Requested model not downloaded
**Solution**:
```bash
# List available models
ollama list

# Pull the required model
ollama pull gemma:2b
```

### Performance Optimization

#### For Production Deployment
1. **Use dedicated GPU**: Significantly faster inference
2. **Optimize model size**: Balance between quality and memory usage
3. **Enable model caching**: Keeps model loaded in memory
4. **Use quantized models**: Reduced memory footprint

#### For Development
1. **Use smaller models**: `gemma:2b` for testing
2. **Enable fallback mode**: Graceful degradation when Ollama unavailable
3. **Monitor memory usage**: Ensure sufficient resources

## Testing the Integration

### 1. Test Ollama Connection
```python
from src.services.ollama_service import OllamaService

service = OllamaService()
print("Connection status:", service.test_connection())
print("Model info:", service.get_model_info())
```

### 2. Test Chat Endpoint
```bash
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what services do you offer?", "conversation_id": "test-123"}'
```

### 3. Test Different Intents
```bash
# Greeting
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi there!", "conversation_id": "test-123"}'

# Service inquiry
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What cloud services do you provide?", "conversation_id": "test-123"}'

# Irrelevant question
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?", "conversation_id": "test-123"}'
```

## Deployment Considerations

### Cloud Deployment
- **AWS/GCP/Azure**: Use instances with sufficient memory (4GB+ RAM)
- **Docker**: Ensure container has adequate memory allocation
- **Kubernetes**: Set appropriate resource limits and requests

### Local Development
- **Memory**: Monitor system memory usage
- **Performance**: Expect slower responses on CPU-only systems
- **Fallback**: Always test fallback mode functionality

## Model Comparison

| Model | Size | Memory | Quality | Speed | Use Case |
|-------|------|--------|---------|-------|----------|
| gemma:2b | 1.7GB | 2.7GB | Good | Fast | Development, Testing |
| phi3:mini | 2.2GB | 5.6GB | Better | Medium | Production (Small) |
| llama2 | 3.8GB | 8.4GB | Excellent | Slow | Production (Large) |
| llama3 | 4.7GB | 8GB+ | Excellent | Medium | Production (Optimal) |

## Support

For issues with Ollama integration:
1. Check system memory and requirements
2. Verify Ollama service is running
3. Test with smaller models first
4. Enable fallback mode for graceful degradation
5. Monitor logs for specific error messages

The system is designed to work with or without Ollama, ensuring your chatbot remains functional regardless of LLM availability.


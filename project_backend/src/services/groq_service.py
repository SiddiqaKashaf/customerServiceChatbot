import os
import requests
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        logger.info(f"GROQ_API_KEY Loaded: {bool(self.api_key)}")
        # Updated to use valid Groq model name format
        self.model_name = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
        logger.info(f"Using Groq model: {self.model_name}")
        self.api_url = 'https://api.groq.com/openai/v1/chat/completions'
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set in environment variables!")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.system_prompt = """You are TechCorp Solutions' professional AI assistant. Provide direct, accurate answers to customer inquiries.

RESPONSE FORMATTING GUIDELINES:
- Use **bold** for key terms, service names, and important information
- Structure responses with clear sections using bullet points (•) and numbered lists
- Use headings with **bold** formatting for different sections
- Keep responses concise but well-structured (max 150 words)
- Use professional formatting with proper spacing

RESPONSE STRUCTURE:
• **Direct Answer**: Start with a clear, specific answer to the question
• **Key Details**: Use bullet points for features, benefits, or specifications
• **Pricing/Information**: Bold important numbers and terms
• **Next Steps**: If applicable, provide clear action items

SERVICES (use these exact names with **bold** formatting):
• **Cloud Migration** (AWS, Azure, GCP)
• **AI/ML Solutions** (custom models, applications)
• **Cybersecurity** (audits, monitoring, compliance)
• **Web Development** (custom applications, e-commerce)
• **Mobile App Development** (iOS, Android, cross-platform)
• **Data Analytics** (BI, dashboards, reporting)
• **Technical Support** (24/7 monitoring, incident response)

FORMATTING EXAMPLES:
- Use **bold** for: **Cloud Migration**, **$2,500/month**, **24/7 support**
- Use bullets for: • Custom solutions • 24/7 monitoring • Expert team
- Use sections like: **Service Overview:** or **Key Features:**

Remember: Be specific, professional, and well-formatted. Focus on what the customer asked for. DO NOT include any signature or closing - the system will add it automatically."""

    def _chat(self, messages, temperature=0.3, top_p=0.9, max_tokens=800, stop=None):
        # Groq API requires temperature > 0, ensure minimum value
        if temperature <= 0:
            temperature = 0.1
        
        # Ensure max_tokens is within reasonable limits (some models have limits)
        if max_tokens > 8192:
            max_tokens = 8192
        
        data = {
            'model': self.model_name,
            'messages': messages,
            'temperature': temperature,
            'top_p': top_p,
            'max_tokens': max_tokens
        }
        
        # Groq API may not support stop parameter or may require different format
        # Only include stop if it's a string or valid format
        # For now, we'll remove it to avoid 400 errors
        # if stop:
        #     # Groq supports stop as a string or array of strings
        #     # But some models may not support it, so we'll skip it
        #     pass
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
            
            # Better error handling - show actual API error response
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('error', {}).get('message', error_detail)
                    error_type = error_json.get('error', {}).get('type', 'unknown')
                    logger.error(f"Groq API error ({response.status_code}) [{error_type}]: {error_detail}")
                except:
                    logger.error(f"Groq API error ({response.status_code}): {error_detail}")
                logger.error(f"Request data: model={self.model_name}, messages_count={len(messages)}, max_tokens={max_tokens}, temperature={temperature}")
                return None
                
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                except:
                    logger.error(f"Error response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def generate_response(self, query: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        """
        Generate a response using the query and context.
        If query is already a full prompt (contains instructions), use generate_response_from_prompt instead.
        """
        prompt = self._build_prompt(query, context, conversation_history)
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        # Removed stop parameter as Groq may not support it or may cause 400 errors
        result = self._chat(messages, temperature=0.3, top_p=0.9, max_tokens=800, stop=None)
        if result:
            return self._clean_response(result)
        else:
            return self._fallback_response(query, context)
    
    def generate_response_from_prompt(self, prompt: str, temperature: float = 0.3, max_tokens: int = 800) -> str:
        """
        Generate a response from a raw prompt (already formatted).
        Use this when you have a fully constructed prompt and don't want additional wrapping.
        """
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        result = self._chat(messages, temperature=temperature, top_p=0.9, max_tokens=max_tokens, stop=None)
        if result:
            return self._clean_response(result)
        else:
            # Extract query from prompt if possible for fallback
            query = prompt[:100] if prompt else "your question"
            return self._fallback_response(query, "")

    def _build_prompt(self, query: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        prompt_parts = []
        
        if context:
            prompt_parts.append(f"RELEVANT COMPANY INFORMATION:\n{context}\n")
        
        if conversation_history:
            prompt_parts.append("CONVERSATION CONTEXT:")
            for msg in conversation_history[-2:]:  # Last 2 exchanges for context
                if msg.get('user_message'):
                    prompt_parts.append(f"Customer: {msg['user_message']}")
                if msg.get('bot_response'):
                    prompt_parts.append(f"Assistant: {msg['bot_response']}")
            prompt_parts.append("")
        
        prompt_parts.append(f"CUSTOMER QUESTION: {query}")
        prompt_parts.append("\nINSTRUCTIONS: Provide a specific, professional answer with proper formatting:")
        prompt_parts.append("• Use **bold** for key terms, service names, and important information")
        prompt_parts.append("• Structure with bullet points (•) and clear sections")
        prompt_parts.append("• Use headings like **Service Overview:** or **Key Features:**")
        prompt_parts.append("• If asking about pricing, give exact prices in **bold**")
        prompt_parts.append("• If asking about services, focus on that service only with structured details")
        prompt_parts.append("• Be precise, actionable, and well-formatted")
        prompt_parts.append("• DO NOT include any signature or closing - the system will add it automatically")
        prompt_parts.append("• Never use placeholder text like [Your Name]")
        prompt_parts.append("• Focus on the content only, no greetings or closings")
        
        return "\n".join(prompt_parts)

    def _clean_response(self, response: str) -> str:
        """Clean up response text and ensure consistent signature."""
        import re
        if not response:
            return self._fallback_response("")

        # Remove common placeholder text patterns
        placeholder_patterns = [
            r'\[Your Name\]',
            r'\[Agent Name\]',
            r'\[Customer Service Representative\]',
            r'\[Representative Name\]',
            r'\[Name\]',
            r'\[Agent\]',
            r'\[CSR\]'
        ]
        cleaned_response = response
        for pattern in placeholder_patterns:
            cleaned_response = re.sub(pattern, 'TechCorp Solutions Customer Service', cleaned_response, flags=re.IGNORECASE)

        # Remove signatures from the beginning of the response
        cleaned_response = re.sub(r'^.*?Best regards,.*?\n.*?\n', '', cleaned_response, flags=re.IGNORECASE | re.DOTALL)
        cleaned_response = re.sub(r'^.*?Sincerely,.*?\n.*?\n', '', cleaned_response, flags=re.IGNORECASE | re.DOTALL)
        cleaned_response = re.sub(r'^.*?Thank you,.*?\n.*?\n', '', cleaned_response, flags=re.IGNORECASE | re.DOTALL)

        # Remove signatures from the end of the response (more comprehensive patterns)
        signature_patterns = [
            r'\n\s*Best regards,.*$',
            r'\n\s*Sincerely,.*$', 
            r'\n\s*Thank you,.*$',
            r'\n\s*Regards,.*$',
            r'\n\s*TechCorp Solutions.*$',
            r'\n\s*Customer Service.*$',
            r'\n\s*AI Assistant.*$',
            r'\n\s*Best regards,\s*TechCorp Solutions Customer Service.*$',
            r'\n\s*Best regards,\s*\n\s*TechCorp Solutions Customer Service.*$',
            r'\n\s*Best regards,\s*\n\s*TechCorp Solutions\s*\n\s*Customer Service.*$'
        ]
        for pattern in signature_patterns:
            cleaned_response = re.sub(pattern, '', cleaned_response, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        cleaned_response = re.sub(r'\n\s*Best regards,.*TechCorp.*Service.*$', '', cleaned_response, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

        # Check if response is too short, empty, or just a markdown header
        cleaned_response = cleaned_response.strip()
        if (
            len(cleaned_response) < 20 or
            cleaned_response.lower() in ['', 'dear customer', 'dear valued customer'] or
            re.match(r'^(\*\*|#|##|###|####|#####|######) ?[\w\s\-:]+(\*\*)?:?$', cleaned_response)
        ):
            return self._fallback_response("")

        # Check if response already has a signature before adding one
        if not re.search(r'best regards.*techcorp.*service', cleaned_response, flags=re.IGNORECASE | re.DOTALL):
            cleaned_response = cleaned_response + '\n\nBest regards,\nTechCorp Solutions Customer Service'
        return cleaned_response

    def _fallback_response(self, query: str, context: str = "") -> str:
        if context:
            base_response = f"""**Service Information Available**

I have some information about this topic, but I need to verify the specific details. Based on our documentation:

• {context[:150]}...

**For Accurate Information:**
• **Contact:** sales@techcorp.com
• **Phone:** **+1 (555) 123-4568**
• **Response Time:** Within **2 business hours**"""
        else:
            base_response = """**Information Request**

I apologize, but I don't have specific information about that topic in my knowledge base.

**Available Support:**
• **Services:** Cloud Migration, AI/ML Solutions, Cybersecurity, Web Development
• **Contact:** sales@techcorp.com
• **Phone:** **+1 (555) 123-4568**
• **Response Time:** Within **2 business hours**"""
        
        return base_response + "\n\nBest regards,\nTechCorp Solutions Customer Service"

    def generate_greeting_response(self) -> str:
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': "Generate a brief, professional greeting for a customer service chatbot with proper formatting using bold and bullet points."}
        ]
        result = self._chat(messages, temperature=0.5, max_tokens=150)
        if result:
            return self._clean_response(result)
        return """**Welcome to TechCorp Solutions!**

Hello! I'm your **AI assistant** here to help with:

• **Service Information** - Cloud Migration, AI/ML Solutions, Cybersecurity
• **Pricing Details** - Custom quotes and package options
• **Technical Support** - 24/7 monitoring and incident response
• **Project Consultation** - Expert guidance for your business needs

How can I assist you today?

Best regards,\nTechCorp Solutions Customer Service"""

    def generate_farewell_response(self) -> str:
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': "Generate a brief, professional farewell message for a customer service chatbot with proper formatting using bold and bullet points."}
        ]
        result = self._chat(messages, temperature=0.5, max_tokens=150)
        if result:
            return self._clean_response(result)
        return """**Thank You for Contacting TechCorp Solutions!**

We appreciate your interest in our services. For further assistance:

• **Sales Inquiries:** sales@techcorp.com
• **Technical Support:** support@techcorp.com
• **Phone:** **+1 (555) 123-4568**
• **Response Time:** Within **2 business hours**

Have a great day!

Best regards,\nTechCorp Solutions Customer Service"""

    def analyze_query_intent(self, query: str) -> str:
        messages = [
            {'role': 'system', 'content': "You are an intent classifier for TechCorp Solutions. Classify the user's query into one of these categories: greeting, farewell, pricing, products, support, technical, general, irrelevant. Respond with only the category name."},
            {'role': 'user', 'content': f"Classify this query: {query}"}
        ]
        result = self._chat(messages, temperature=0.1, max_tokens=10)
        valid_intents = ['greeting', 'farewell', 'pricing', 'products', 'support', 'technical', 'general', 'irrelevant']
        if result and result.lower() in valid_intents:
            return result.lower()
        else:
            return 'general'

    def check_relevance(self, query: str) -> bool:
        messages = [
            {'role': 'system', 'content': "You are a relevance checker for TechCorp Solutions. TechCorp offers cloud services, AI/ML solutions, digital transformation, cybersecurity, data analytics, mobile app development, and web development. Respond with only 'relevant' or 'irrelevant' based on whether the query is related to these services or general business inquiries."},
            {'role': 'user', 'content': f"Is this query relevant to TechCorp Solutions: {query}"}
        ]
        result = self._chat(messages, temperature=0.1, max_tokens=5)
        # Only return True if the result is exactly 'relevant'
        return result and result.strip().lower() == 'relevant'

    def get_model_info(self) -> Dict[str, Any]:
        # Groq API does not provide a direct model info endpoint; return config
        return {
            'name': self.model_name,
            'status': 'configured',
            'provider': 'Groq'
        }


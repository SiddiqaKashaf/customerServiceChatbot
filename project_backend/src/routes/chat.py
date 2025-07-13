from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import uuid
import datetime
from src.services.rag_service import RAGService

chat_bp = Blueprint('chat', __name__)

# Initialize RAG service
rag_service = None

def get_rag_service():
    """Get or create RAG service instance"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

def reset_rag_service():
    """Reset the RAG service instance"""
    global rag_service
    rag_service = None

@chat_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint to verify server is running"""
    try:
        rag_service = get_rag_service()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.now().isoformat(),
            'service': 'TechCorp Solutions RAG Chatbot',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@chat_bp.route('/test-pdf-processing', methods=['GET'])
@cross_origin()
def test_pdf_processing():
    """Test PDF processing and return detailed information"""
    try:
        rag_service = get_rag_service()
        # Get PDF info
        pdf_info = rag_service.get_pdf_info()
        
        # Get index status
        index_status = rag_service.get_index_status()
        
        # Test a simple search
        test_query = "services"
        search_results = rag_service.search_documents_faiss(test_query, top_k=3)
        
        return jsonify({
            'pdf_info': pdf_info,
            'index_status': index_status,
            'test_search': {
                'query': test_query,
                'results_count': len(search_results),
                'results': search_results[:2] if search_results else []  # Show first 2 results
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Add debugging information
        import logging
        logging.getLogger(__name__).info(f"Processing message: {user_message}")
        
        # Get index status for debugging
        rag_service = get_rag_service()
        index_status = rag_service.get_index_status()
        logging.getLogger(__name__).info(f"Index status: {index_status}")
        
        # Process the message through RAG service
        response_data = rag_service.process_message(user_message, conversation_id)
        
        # Add debugging information to response
        response_data['debug'] = {
            'index_status': index_status,
            'message_processed': user_message
        }
        
        # Prepare response
        response = {
            'message_id': str(uuid.uuid4()),
            'conversation_id': conversation_id,
            'response': response_data['response'],
            'confidence': response_data['confidence'],
            'sources': response_data.get('sources', []),
            'context_used': response_data.get('context_used', False),
            'timestamp': datetime.datetime.now().isoformat(),
            'suggested_responses': response_data.get('suggested_responses', []),
            'pdf_available': response_data.get('pdf_available', False),
            'debug': response_data.get('debug', {})
        }
        
        return jsonify(response)
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Sorry, we encountered an error processing your request. Please try again later or contact support.'
        }), 500

@chat_bp.route('/reset-rag-service', methods=['POST'])
@cross_origin()
def reset_rag_service_endpoint():
    """Reset the RAG service instance to force reinitialization"""
    try:
        reset_rag_service()
        return jsonify({'message': 'RAG service reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/upload-documents', methods=['POST'])
@cross_origin()
def upload_documents():
    """Endpoint to upload and process documents for the knowledge base"""
    try:
        rag_service = get_rag_service()
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        processed_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Process and add to knowledge base
            result = rag_service.add_document(file)
            processed_files.append(result)
        
        return jsonify({
            'message': f'Successfully processed {len(processed_files)} documents',
            'files': processed_files
        })
        
    except Exception as e:
        print(f"Error uploading documents: {str(e)}")
        return jsonify({'error': 'Failed to process documents'}), 500

@chat_bp.route('/knowledge-base/status', methods=['GET'])
@cross_origin()
def knowledge_base_status():
    """Get status of the knowledge base"""
    try:
        rag_service = get_rag_service()
        status = rag_service.get_knowledge_base_status()
        return jsonify(status)
    except Exception as e:
        print(f"Error getting knowledge base status: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

@chat_bp.route('/index-status', methods=['GET'])
@cross_origin()
def get_index_status():
    """Get the current status of the FAISS index"""
    try:
        rag_service = get_rag_service()
        status = rag_service.get_index_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/rebuild-index', methods=['POST'])
@cross_origin()
def rebuild_index():
    """Rebuild the FAISS index from PDF documents"""
    try:
        rag_service = get_rag_service()
        success = rag_service.rebuild_faiss_index()
        if success:
            return jsonify({'message': 'FAISS index rebuilt successfully'})
        else:
            return jsonify({'error': 'Failed to rebuild FAISS index'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


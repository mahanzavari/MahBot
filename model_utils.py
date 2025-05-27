from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
import torch
import os

# Initialize model and tokenizer
MODEL_PATH = os.path.join('models', 'distilbert-base-uncased')
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
model = DistilBertForQuestionAnswering.from_pretrained(MODEL_PATH)

def get_local_model_response(question, context=None):
    """
    Get response from DistilBERT model for a given question.
    If no context is provided, return a default response.
    """
    try:
        if not context:
            return "I'm sorry, I need more context to answer your question accurately. Please provide more details or try using the API mode for more comprehensive responses."
        
        # Prepare inputs with proper formatting
        inputs = tokenizer(
            question,
            context,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        
        # Get model predictions
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get the most likely beginning and end of answer
        answer_start = torch.argmax(outputs.start_logits)
        answer_end = torch.argmax(outputs.end_logits)
        
        # Ensure answer_end is after answer_start
        if answer_end < answer_start:
            answer_end = answer_start
        
        # Convert tokens to string
        answer = tokenizer.convert_tokens_to_string(
            tokenizer.convert_ids_to_tokens(
                inputs["input_ids"][0][answer_start:answer_end+1]
            )
        )
        
        # If no specific answer found or empty answer, provide a general response
        if not answer.strip():
            # Check for common legal keywords and provide relevant responses
            question_lower = question.lower()
            
            if any(word in question_lower for word in ['contract', 'agreement', 'sign']):
                return "A contract is a legally binding agreement between two or more parties. It must include an offer, acceptance, consideration, and mutual intent to be bound. For specific contract advice, please consult with a legal professional."
            
            elif any(word in question_lower for word in ['tort', 'damage', 'injury', 'negligence']):
                return "A tort is a civil wrong that causes harm or loss to another person. The injured party may seek compensation through a civil lawsuit. Common types include negligence, intentional torts, and strict liability."
            
            elif any(word in question_lower for word in ['criminal', 'crime', 'offense', 'arrest']):
                return "Criminal law deals with offenses against the state. These cases are prosecuted by the government and can result in penalties like fines or imprisonment. If you're facing criminal charges, it's important to seek legal representation immediately."
            
            elif any(word in question_lower for word in ['right', 'constitutional', 'freedom']):
                return "Constitutional rights are fundamental protections guaranteed by the constitution, including due process, equal protection, freedom of speech, and other civil liberties. These rights protect individuals from government overreach."
            
            elif any(word in question_lower for word in ['property', 'real estate', 'land']):
                return "Property law governs the ownership and use of real and personal property. It includes rights of possession, use, and transfer of property. Property disputes should be handled with legal assistance."
            
            elif any(word in question_lower for word in ['family', 'divorce', 'custody', 'marriage']):
                return "Family law covers matters like marriage, divorce, child custody, and support. These are sensitive issues that often require legal guidance to ensure your rights are protected."
            
            elif any(word in question_lower for word in ['employment', 'work', 'job', 'hire']):
                return "Employment law governs the relationship between employers and employees. It covers issues like contracts, discrimination, workplace safety, and termination. If you have employment concerns, consider consulting with an employment lawyer."
            
            else:
                return "I understand you're asking about a legal matter. While I can provide general information, please note that this is not legal advice. For specific legal guidance, please consult with a qualified attorney. You can also try using the API mode for more detailed responses."
        
        return answer.strip()
    
    except Exception as e:
        print(f"Error in local model inference: {str(e)}")
        return "I apologize, but I encountered an error while processing your question. Please try again or use the API mode for more reliable responses." 
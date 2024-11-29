from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .main import CSVPipeline
from rest_framework import status
from .models import Chat
import logging
from django.http import StreamingHttpResponse

groq_api_key = "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"  # Use your actual Groq API key

logger = logging.getLogger(__name__)

def chatbot_frontend(request):
    return render(request, 'chatbot.html')

@api_view(['POST'])
def chat(request):
    print(request)
    try:
        # Extract prompt, model_name, and api_key from the request body (assuming JSON format)
        prompt = request.data.get('prompt')
        model_name = request.data.get('model_name', "Gemma2-9b-It")  # Default model if none is provided
        api_key = groq_api_key  # API key passed from the request

        # Validate input
        if not prompt:
            return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not api_key:
            return Response({"error": "API key is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the pipeline
        pipeline = CSVPipeline(model_name=model_name)
        # Allow the user to select the model dynamically
        pipeline.chooseModel(model_name=model_name, groq_api_key=groq_api_key)
       
        # Set up the retriever with the prompt
        pipeline.retrieval(prompt)

        # Get the answer from the pipeline
        response = pipeline.answer(prompt)

        # Save the chat to the database
        chat_record = Chat(user_message=prompt, bot_response=response)
        chat_record.save()  # Save the record to PostgreSQL

        # Return the response from the pipeline
        return Response({"response": response}, status=status.HTTP_200_OK)

    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")  # Log the error for debugging
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def get_chat_history(request):
    # Retrieve chat history from the database (if you're using a model like Chat)
    chats = Chat.objects.all().order_by('-timestamp')[:10]
    chat_history = [{"user_message": chat.user_message, "bot_response": chat.bot_response, "timestamp": chat.timestamp} for chat in chats]
    return render(request, 'history.html', {'chat_history': chat_history})
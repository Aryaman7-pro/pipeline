from django.urls import path
from . import views

urlpatterns = [
    # URL for the chatbot frontend page (HTML page)
    path('', views.chatbot_frontend, name='chatbot_frontend'),  # The chatbot page

    # URL for the chatbot API view (POST requests for chatbot interaction)
    path('chat/', views.chat, name='chat'),

    # URL for the chat history page
    path('history/', views.get_chat_history, name='get_chat_history'),
]

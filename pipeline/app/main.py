from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, FewShotChatMessagePromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from app.models import Chat

groq_api_key = "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"

class CSVPipeline:
    def __init__(self, llm=None, retriever=None, prompt=None, model_name="Gemma2-9b-It"):
        self.model_name = model_name
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt
        self.api_key = None  # Initialize with no API key
        self.defineLLM(self.model_name)  # Set the LLM with default model_name at initialization

    def defineLLM(self, model_name="Gemma2-9b-It", groq_api_key=None):
        """
        Define the LLM with the given model_name and API key. 
        This should be done before any interactions with the model.
        """
        groq_api_key = "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"
        if groq_api_key is None:
            raise ValueError("API key is required to define LLM.")
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name, streaming=True)

    def chooseModel(self, model_name, groq_api_key):
        """
        Choose the model dynamically and set the model name and LLM
        """
        available_models = ["Gemma2-9b-It", "Gemma2-7b-It"]  # Add other models if needed
        if model_name in available_models:
            self.model_name = model_name
            self.defineLLM(model_name=model_name, groq_api_key=groq_api_key)
        else:
            raise ValueError(f"Model {model_name} is not available. Choose from {', '.join(available_models)}.")
    
    def retrieval(self, prompt):
        self.prompt = prompt
        NEO4J_URI = "neo4j+s://7a76cce7.databases.neo4j.io"
        NEO4J_USERNAME = "neo4j"
        NEO4J_PASSWORD = "iLflxvMlzC8QtxKRYA3cIIEDiR_PzH4vfsLQS08RJXY"
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        self.retriever = GraphCypherQAChain.from_llm(llm=self.llm, graph=graph, verbose=True, allow_dangerous_requests=True)
 
    def get_context_from_db(self):
        # Fetch the last 3 questions and answers from the database
        chats = Chat.objects.order_by('-timestamp')[:5]  # Get last 3 records ordered by timestamp
        context = ""
        for chat in chats:
            context += f"User: {chat.user_message}\nBot: {chat.bot_response}\n"
        return context
    
    def answer(self, prompt):
        try:
            # Fetch context from the last 3 questions and answers in the database
            context = self.get_context_from_db()
            print('Context:', context)  # Optional: For debugging purposes

            # Few-shot examples to guide the model in generating better answers
            few_shot_examples = [
                {
                    "input": '''User: Hey, what can you tell me about the Captive Screw,''',
                    "output": "Give me the complete description about Captive Screw"
                },
                {
                    "input": '''User: What is the DZUS Quarter-Turn Retainer?''',
                    "output": "Give me the complete description about DZUS Quarter-Turn Retainer?"
                },
                {
                    "input": '''User: Hey, what is the price of the given sku "sku_id"''',
                    "output": "What is the price of sku 'sku_id'"
                },
                {
                    "input": '''User: Hey, provide me the difference between sku ids [sku_id_1, sku_id2, ...]''',
                    "output": "Give me the difference between informations among sku ids sku_id_1, sku_id_2...?"
                }
            ]
 


            # Prepare the few-shot prompt based on examples
            few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=few_shot_examples,  # Provide the list of examples directly here
            example_prompt=ChatPromptTemplate.from_messages(
            [
            ("human", "{input}"),
            ("ai", "{output}"),
            ]
            )
            )

            # Create the final prompt structure for friendly question conversion
            final_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", '''You are an expert assistant. Your task is to convert friendly-toned user queries into exact product queries. Give exact answers to the asked questions and context given. Use the following context to help answer the query.'''),
                    few_shot_prompt,
                    ("human", "{input}"),
                ]
            )

            # Format the prompt with the user's input and few-shot examples
            formatted_prompt = final_prompt.format_messages(input=prompt)  # Corrected formatting
            print(f"Formatted prompt: {formatted_prompt}")  # Debugging

            # Send the formatted prompt to the model and let it generate a new prompt
            if self.llm is not None:
                model_output = self.llm.invoke(formatted_prompt)  # Send the formatted prompt to the model
                print('Hello',model_output)
                print(type(model_output))
                generated_prompt = model_output.content.strip() # Extract the generated prompt from the model's output
                print(f"Generated prompt: {generated_prompt}")  # Debugging

                # Now, use the generated prompt for retrieval
                if self.retriever is not None:
                    answer = self.retriever.invoke(generated_prompt)  # Send generated prompt to retriever
                    print(answer['result'])
                    response = answer['result']
                    if response:
                        return response
                    else:
                        return "Sorry, I couldn't find an answer."
                else:
                    raise ValueError("Retriever is not defined. Please ensure the LLM and retrieval chain are set up first.")

            else:
                raise ValueError("LLM is not defined. Please ensure the LLM is set up first.")

        except Exception as e:
            # Log error details for debugging
            print(f"Error occurred: {str(e)}")
            return f"An error occurred: {str(e)}"

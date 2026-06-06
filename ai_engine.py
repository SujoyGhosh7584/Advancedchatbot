import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()


class ChatBotEngine:

    def __init__(self, system_prompt="You are a helpful AI assistant."):
        """Initializes clients and injects the live system clock."""
        api_key = os.environ.get("GROQ_API_KEY")
        tavily_key = os.environ.get("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing!")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

        # Initialize the free web search agent client if the key exists
        self.search_client = TavilyClient(api_key=tavily_key) if tavily_key else None

        # Dynamically inject today's date so the bot always knows "now"
        today_str = datetime.now().strftime("%B %d, %Y")
        self.base_system_prompt = (
            f"{system_prompt}\n"
            f"Current Real-world Date: {today_str}.\n"
            "You have access to live web search data when relevant."
        )

    def _execute_web_search(self, query):
        """Silently searches the live internet for recent facts."""
        if not self.search_client:
            return "Web search is currently unavailable. No API key provided."
        try:
            # Fetch clean, summarized results from the live web
            response = self.search_client.search(
                query=query, max_results=3, topic="general"
            )
            context_list = [
                f"- {item['title']}: {item['content']}"
                for item in response.get("results", [])
            ]
            return "\n".join(context_list)
        except Exception as e:
            return f"Failed to fetch live data: {e}"

    def get_streaming_response(self, chat_history):
        """Evaluates context, pulls web answers if needed, and streams the output."""
        # 1. Grab the last message the user typed
        last_user_message = chat_history[-1]["content"] if chat_history else ""

        # 2. Decide if we need to search the web (for weather, time, scores, news)
        trigger_words = [
            "weather",
            "score",
            "won",
            "date",
            "today",
            "news",
            "current",
            "match",
        ]
        needs_search = any(word in last_user_message.lower() for word in trigger_words)

        live_context = ""
        if needs_search:
            # Search the live web using the user's prompt as the query
            live_context = self._execute_web_search(last_user_message)

        # 3. Construct the prompt payload
        system_content = self.base_system_prompt
        if live_context:
            system_content += (
                f"\n\n[LIVE SEARCH RESULTS]\n{live_context}\n\n"
                "Use the live search data above to answer accurately."
            )

        compiled_messages = [{"role": "system", "content": system_content}]
        for msg in chat_history:
            compiled_messages.append({"role": msg["role"], "content": msg["content"]})

        # 4. Stream response back to app.py
        completion = self.client.chat.completions.create(
            model=self.model, messages=compiled_messages, stream=True
        )

        # Safely yield text tokens by parsing index 0 of the choices array
        for chunk in completion:
            if chunk.choices and len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

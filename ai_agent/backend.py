import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent

class AnalyticsAgent:
    def __init__(self, api_key=None):
        load_dotenv()
        # Use passed key or fallback to env var
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.db_url = os.getenv("DATABASE_URL")
        
    def ask(self, question: str) -> str:
        if not self.api_key:
            return '⚠️ AI features require an OPENAI_API_KEY in your .env file.'
            
        try:
            # Connect to DB
            db = SQLDatabase.from_uri(self.db_url)
            
            # Initialize LLM
            llm = ChatOpenAI(
                temperature=0, 
                model="gpt-4", 
                api_key=self.api_key
            )
            
            # Create the SQL Agent
            agent_executor = create_sql_agent(
                llm=llm,
                db=db,
                agent_type="openai-tools",
                verbose=True
            )
            
            # Run the query
            result = agent_executor.invoke({"input": question})
            return result["output"]
            
        except Exception as e:
            return f"Error running analytics agent: {str(e)}"
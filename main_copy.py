from sarvamai import SarvamAI
from fastapi import FastAPI, UploadFile, File
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel
from typing import List, Literal, Optional
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from a .env file
load_dotenv()

app = FastAPI()

sarvam_client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY"),
)

# locd llm model
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# creating the pydantic model to get stractured output 

class MeetingAnalysis(BaseModel):
    summary:str
    decions: Optional[str] = None
    action_items: List[str]
    risk_blockers: List[str]
    unsolved_questions: List[str]
    participants: List[str]

class ActionItems(BaseModel):
    task:str 
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

stractured_llm = llm.with_structured_output(MeetingAnalysis)

prompt = ChatPromptTemplate([
    ("system", """
    You are helpful ai assistance to extract the information from meeting text
    """),
    ("user", "Transcipt The following test: {transcript}"),
])

extraction_chain = prompt | stractured_llm

@app.post("/api/meetings/upload")
async def upload_meeting(file:UploadFile = File(...)):
   os.makedirs("temp", exist_ok=True)
   temp_path = f"temp/{file.filename}"

   try:
       
       with open(temp_path, "wb") as f:
           f.write(await file.read())

       with open(temp_path, "rb") as audio_file:
           sst_response = sarvam_client.speech_to_text.transcribe(
               file=audio_file,
               model="saaras:v3",
               mode="transcribe"
           )
       transcript = sst_response.transcript
       analysis = extraction_chain.invoke({
           "transcript":transcript
       })

       return {"transctipt": transcript,
               "analysis": analysis
               }
   finally:
       if os.path.exists(temp_path):
           os.remove(temp_path)
   

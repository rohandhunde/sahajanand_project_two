from sarvamai import SarvamAI
from fastapi import FastAPI, UploadFile, File
import os
import glob
import json
import tempfile
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

def transcribe_audio(temp_path: str) -> str:
    """
    Transcribe an audio file of any length using Sarvam's batch job API.

    client.speech_to_text.transcribe() only accepts clips up to 30 seconds,
    so meeting recordings need the async job flow instead: create a job,
    upload the file, start it, wait for it to finish, then read the
    transcript out of the downloaded JSON output.
    """
    job = sarvam_client.speech_to_text_job.create_job(
        model="saaras:v3",
        mode="transcribe",
    )
    job.upload_files(file_paths=[temp_path])
    job.start()
    # poll every 5s, give large recordings up to 30 minutes to finish
    job.wait_until_complete(poll_interval=5, timeout=1800)

    file_results = job.get_file_results()
    if len(file_results["successful"]) == 0:
        failed = file_results.get("failed", [])
        reason = failed[0]["error_message"] if failed else "unknown error"
        raise RuntimeError(f"Transcription job failed: {reason}")

    with tempfile.TemporaryDirectory() as out_dir:
        job.download_outputs(output_dir=out_dir)
        json_files = glob.glob(os.path.join(out_dir, "*.json"))
        if not json_files:
            raise RuntimeError("Transcript JSON not found in job output")
        with open(json_files[0]) as f:
            result = json.load(f)
        return result.get("transcript", "")

@app.post("/api/meetings/upload")
async def upload_meeting(file:UploadFile = File(...)):
   os.makedirs("temp", exist_ok=True)
   temp_path = f"temp/{file.filename}"

   try:
       
       with open(temp_path, "wb") as f:
           f.write(await file.read())

       transcript = transcribe_audio(temp_path)
       analysis = extraction_chain.invoke({
           "transcript":transcript
       })

       return {"transctipt": transcript,
               "analysis": analysis
               }
   finally:
       if os.path.exists(temp_path):
           os.remove(temp_path)
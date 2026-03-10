import os

import jiwer
from dotenv import load_dotenv
from google import genai

load_dotenv()

_gemini_client = None


# Gemini A
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in .env file")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client



# Modeļa nosaukums

LLM_MODEL = "gemini-3-flash-preview"


# Novērtēšeana izmantojot lielo valodas modeli
 
def llm_judge(reference: str, hypothesis: str) -> float:

    client = _get_gemini_client()
    prompt = (
        "You are evaluating ASR (speech-to-text) output quality.\n\n"
        f"Reference transcript:\n{reference}\n\n"
        f"ASR hypothesis:\n{hypothesis}\n\n"
        "Score how accurately the ASR hypothesis captures the meaning and content "
        "of the reference transcript. Reply with only a single number between 0"
        "(completely wrong) and 100 (perfect match), nothing else."
    )
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
    )
    score_text = response.text.strip()
    return float(score_text)


# Teksta apstrāde pirms novērtēšanas: visi burti ir mazie un noņemta punktuācija 

WER_TRANSFORM = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfWords(),
])
CER_TRANSFORM = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfChars(),
])



# WER un CER metriku aprēķins

def compute_metrics(reference: str, hypothesis: str) -> tuple[float, float]:
    wer = jiwer.wer(
        reference, hypothesis,
        reference_transform=WER_TRANSFORM,
        hypothesis_transform=WER_TRANSFORM,
    )
    cer = jiwer.cer(
        reference, hypothesis,
        reference_transform=CER_TRANSFORM,
        hypothesis_transform=CER_TRANSFORM,
    )
    return wer, cer

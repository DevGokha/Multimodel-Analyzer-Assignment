from fastapi import FastAPI, File, UploadFile, Form, Response
from fastapi.responses import StreamingResponse 
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import analyzer
import pdf_generator 


app = FastAPI()


origins = [
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class AnalysisResponse(BaseModel):
    text_sentiment: str
    text_summary: str
    topic_classification: str
    image_classification: str
    ocr_text: str
    toxicity_warning: str
    automated_response: str


@app.get("/")
def read_root():
    return {"message": "Multimodal Analyzer API is running!"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(text: str = Form(...), image: UploadFile = File(...)):
    
    image_bytes = await image.read()
    
    
    sentiment_result = analyzer.analyze_sentiment(text)
    summary_result = analyzer.summarize_text(text)
    topic_result = analyzer.classify_topic(text)
    text_toxicity_result = analyzer.check_toxicity(text)

    
    image_class_result = analyzer.classify_image(image_bytes)
    ocr_text_result = analyzer.extract_text_from_image(image_bytes)
    ocr_toxicity_result = analyzer.check_toxicity(ocr_text_result)
    
    
    nlp_data = {"sentiment": sentiment_result, "toxicity": text_toxicity_result}
    cv_data = {"classification": image_class_result, "ocr_toxicity": ocr_toxicity_result}
    automated_response = analyzer.generate_automated_response(nlp_data, cv_data)

    
    toxicity_warning = "None"
    if text_toxicity_result['is_toxic'] and ocr_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in both text and image."
    elif text_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in input text."
    elif ocr_toxicity_result['is_toxic']:
        toxicity_warning = "Toxicity detected in image text (OCR)."

    
    response = AnalysisResponse(
        text_sentiment=f"{sentiment_result['label']} ({sentiment_result['score']:.2f})",
        text_summary=summary_result,
        topic_classification=topic_result,
        image_classification=image_class_result.split(',')[0], 
        ocr_text=ocr_text_result,
        toxicity_warning=toxicity_warning,
        automated_response=automated_response,
    )
    
    return response

@app.post("/generate-report")
async def generate_report(analysis_data: AnalysisResponse):
    """
    Accepts analysis JSON and returns a PDF report.
    """
    pdf_bytes = pdf_generator.create_report(analysis_data.dict())

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=analysis_report.pdf"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
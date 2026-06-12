"""
agents/resume_agent.py
----------------------
Resume Parsing Agent.
"""

import os
import re
import logging
from agents.base_agent import BaseAgent, AgentContext

try:
    import PyPDF2
except ImportError:
    logging.warning("PyPDF2 is not installed.")

logger = logging.getLogger(__name__)

class ResumeParserAgent(BaseAgent):
    """
    ResumeParserAgent parses pdf resumes and stores cleaned text into context.
    """
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\r\n]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def run(self, context: AgentContext) -> AgentContext:
        pdf_path = context.resume_path
        if not pdf_path:
            logger.warning("ResumeParserAgent: No resume path provided.")
            context.resume_text = ""
            return context
            
        if not os.path.exists(pdf_path):
            logger.error("ResumeParserAgent: File not found: %s", pdf_path)
            context.resume_text = ""
            return context
            
        if not pdf_path.lower().endswith('.pdf'):
            logger.error("ResumeParserAgent: Invalid file extension. Expected PDF: %s", pdf_path)
            context.resume_text = ""
            return context

        extracted_text = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                if num_pages == 0:
                    logger.warning("ResumeParserAgent: Empty PDF: %s", pdf_path)
                    context.resume_text = ""
                    return context
                    
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                        
            full_text = " ".join(extracted_text)
            if not full_text.strip():
                logger.warning("ResumeParserAgent: No parseable text found in PDF: %s", pdf_path)
                context.resume_text = ""
                return context
                
            cleaned_text = self.clean_text(full_text)
            logger.info("ResumeParserAgent: Successfully parsed %d chars.", len(cleaned_text))
            context.resume_text = cleaned_text
            
        except Exception as e:
            logger.error("ResumeParserAgent: Error processing '%s': %s", pdf_path, e)
            context.resume_text = ""
            
        return context

# core/translation_service.py
import openai
from django.conf import settings
from typing import Dict, Any, List
import json
from wagtail.models import Page
import logging

logger = logging.getLogger(__name__)

class AITranslationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def get_language_name(self, language_code: str) -> str:
        """Convert language code to full name for better AI context"""
        language_map = {
            'is': 'Icelandic',
            'en': 'English',
            'da': 'Danish',
            'no': 'Norwegian',
            'sv': 'Swedish',
        }
        return language_map.get(language_code, language_code)
    
    def extract_translatable_content(self, page: Page) -> Dict[str, Any]:
        """Extract all translatable text fields from a page"""
        translatable_content = {}
        
        # Fields to skip - these are internal Wagtail fields
        skip_fields = [
            'path', 'url_path', 'depth', 'numchild', 'translation_key', 'locale_id', 
            'location', 'venue', 'address', 'place', 'location_name'
        ]
        
        # Get all fields from the page model
        for field in page._meta.get_fields():
            if hasattr(page, field.name) and field.name not in skip_fields:
                field_value = getattr(page, field.name)
                
                # Handle different field types
                if isinstance(field_value, str) and field_value.strip():
                    # Include text fields including slug and title
                    translatable_content[field.name] = field_value
                    
                elif hasattr(field_value, 'raw_data'):
                    # StreamField content
                    stream_data = self._extract_streamfield_content(field_value)
                    if stream_data:
                        translatable_content[field.name] = stream_data
                        
                elif hasattr(field_value, 'source'):
                    # RichTextField content
                    if field_value.source.strip():
                        translatable_content[field.name] = field_value.source
        
        return translatable_content
    
    def _extract_streamfield_content(self, stream_field) -> List[Dict]:
        """Extract translatable content from StreamField"""
        content = []
        
        for block in stream_field:
            block_content = self._extract_block_content(block)
            if block_content:
                content.append({
                    'block_type': block.block_type,
                    'id': str(block.id) if hasattr(block, 'id') else None,
                    'content': block_content
                })
        
        return content if content else None
    
    def _extract_block_content(self, block) -> Dict[str, Any]:
        """Extract translatable content from individual blocks"""
        block_content = {}
        
        if hasattr(block, 'value'):
            if isinstance(block.value, str):
                # Simple text block
                if block.value.strip():
                    block_content['text'] = block.value
            elif isinstance(block.value, dict):
                # Structured block
                for key, value in block.value.items():
                    if isinstance(value, str) and value.strip():
                        block_content[key] = value
                    elif hasattr(value, 'source'):  # RichText
                        if value.source.strip():
                            block_content[key] = value.source
        
        return block_content
    
    def translate_content(self, content: Dict[str, Any], source_lang: str, target_lang: str, page_type: str = None) -> Dict[str, Any]:
        """Translate content using OpenAI"""
        if not content:
            return {}
            
        source_lang_name = self.get_language_name(source_lang)
        target_lang_name = self.get_language_name(target_lang)
        
        system_prompt = f"""You are a professional translator. Translate the following JSON content from {source_lang_name} to {target_lang_name}. 
        
        Return ONLY valid JSON with the exact same structure, but with translated text values. Do NOT wrap in markdown code blocks. Return raw JSON only."""

        user_prompt = f"Translate this JSON from {source_lang_name} to {target_lang_name}:\n\n{json.dumps(content, ensure_ascii=False, indent=2)}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]   # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove closing ```
            
            response_text = response_text.strip()
            
            if not response_text:
                logger.error("OpenAI returned empty response")
                return content
            
            # Parse the JSON response
            translated_content = json.loads(response_text)
            logger.info(f"Successfully translated content from {source_lang} to {target_lang}")
            return translated_content
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}. Response was: {response_text[:500]}")
            return content
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return content
    
    def apply_translated_content(self, page: Page, translated_content: Dict[str, Any]):
        """Apply translated content back to the page"""
        for field_name, translated_value in translated_content.items():
            if hasattr(page, field_name):
                if isinstance(translated_value, list):
                    # StreamField content - skip for now as it's complex
                    logger.info(f"Skipping StreamField translation for {field_name}")
                    continue
                elif isinstance(translated_value, str):
                    # Simple text field
                    setattr(page, field_name, translated_value)
                    logger.info(f"Translated {field_name}: {translated_value[:50]}...")
        
        # Mark this page as AI translated
        page.ai_translated = True
        logger.info("Marked page as AI translated")
            
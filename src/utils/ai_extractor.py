from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field

from src.config import settings
from src.utils.image_processor import ImageProcessor


class DateExtraction(BaseModel):
    """Schema the model must populate (used as the structured-output format)."""

    manufacturing_date: Optional[str] = Field(
        default=None,
        description="Manufacturing date in YYYY-MM-DD format, or null if unreadable.",
    )
    expiry_date: Optional[str] = Field(
        default=None,
        description="Expiry/best-before date in YYYY-MM-DD format, or null if unreadable.",
    )


@dataclass
class ExtractionResult:
    """Structured result of an AI image analysis."""

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: str = "unreadable"  # 'readable' | 'unreadable' | 'skipped' | 'error'
    raw: Optional[str] = None


_PROMPT = (
    "You are reading a product label. Extract the manufacturing date and the "
    "expiry/best-before date from the image. Use the YYYY-MM-DD format, and use "
    "null for any date you cannot read."
)


class AIExtractor:
    """Extract dates from product images via Azure OpenAI vision (optional)."""

    @staticmethod
    def is_enabled() -> bool:
        """Return True if Azure OpenAI credentials are configured."""
        return bool(settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT)

    @classmethod
    async def extract_dates(cls, image_path: str) -> ExtractionResult:
        """Analyse an image and return extracted dates.

        Never raises — returns a result with ``status`` describing the outcome
        so verification can proceed even when AI analysis is unavailable.
        """
        if not cls.is_enabled():
            return ExtractionResult(status="skipped")

        is_valid, _ = ImageProcessor.validate_image_file(image_path)
        if not is_valid:
            return ExtractionResult(status="error")

        b64 = ImageProcessor.encode_image_to_base64(image_path)
        if not b64:
            return ExtractionResult(status="error")
        media_type = ImageProcessor.get_image_mime_type(image_path)

        try:
            # Imported lazily so the package is only required when AI is used.
            from openai import AsyncAzureOpenAI

            client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
            # Structured output: the model is forced to return JSON matching the
            # DateExtraction schema, and the SDK parses it back into the model.
            response = await client.beta.chat.completions.parse(
                model=settings.GPT_DEPLOYMENT,
                max_tokens=256,
                temperature=0,
                response_format=DateExtraction,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{media_type};base64,{b64}"},
                            },
                        ],
                    }
                ],
            )
            message = response.choices[0].message
            if getattr(message, "refusal", None):
                return ExtractionResult(status="unreadable", raw=message.refusal)

            data: Optional[DateExtraction] = message.parsed
            if data is None:
                return ExtractionResult(status="unreadable", raw=message.content)

            return ExtractionResult(
                manufacturing_date=data.manufacturing_date,
                expiry_date=data.expiry_date,
                status=(
                    "readable" if (data.expiry_date or data.manufacturing_date) else "unreadable"
                ),
                raw=data.model_dump_json(),
            )
        except Exception as exc:  # noqa: BLE001 - never break verification on AI failure
            print(f"AI extraction failed: {exc}")
            return ExtractionResult(status="error")

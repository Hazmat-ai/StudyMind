import anthropic
import json
import os
from ..schemas.generate import GenerateOptions, GenerateResponse

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
You are a study assistant that converts academic content into structured study materials.
Always respond with valid JSON only. No preamble, no markdown, no explanation outside the JSON.

Output format:
{
  "title": "short descriptive title (max 8 words)",
  "summary": "2-4 paragraph summary of the core ideas in plain language",
  "flashcards": [
    { "term": "...", "definition": "..." }
  ],
  "questions": [
    {
      "question": "...",
      "answer": "...",
      "type": "short_answer"
    }
  ],
  "concepts": [
    { "term": "...", "related": ["...", "..."] }
  ]
}

Guidelines:
- Flashcards should test understanding, not just memorization
- Questions should require actual comprehension to answer, not just recall
- Summaries should explain WHY things work, not just WHAT they are
- Use plain language — imagine explaining to a smart peer, not a professor
- Generate exactly the number of flashcards and questions requested
"""

USER_PROMPT_TEMPLATE = """
Generate a study set from the following academic content.
Number of flashcards: {num_flashcards}
Number of questions: {num_questions}
Difficulty level: {difficulty}

Content:
{content}
"""

async def generate_study_set(content: str, options: GenerateOptions) -> GenerateResponse:
    try:
        if not os.getenv("ANTHROPIC_API_KEY"):
            # Provide a very high-quality mock response for testing/portfolio purposes
            import asyncio
            await asyncio.sleep(2)
            mock_data = {
              "title": "Mock Study Set: " + content[:20] + "...",
              "summary": f"This is an auto-generated mock summary since no Anthropic API key was found.\n\nThe content provided was: {content[:100]}...\n\nIn a real environment, this would be a 2-4 paragraph explanation.",
              "flashcards": [
                { "term": "Mock Term 1", "definition": "This is a mock definition for testing purposes." },
                { "term": "Mock Term 2", "definition": "This is another mock definition." }
              ],
              "questions": [
                {
                  "question": "What is the primary function of this mock system?",
                  "answer": "To allow the frontend to be fully tested without requiring a paid API key.",
                  "type": "short_answer"
                }
              ],
              "concepts": [
                { "term": "Mock Testing", "related": ["Frontend Verification", "Error Handling"] }
              ]
            }
            return GenerateResponse(**mock_data)

        # truncate to avoid token overflow, approx 12,000 chars is fine for Claude but we enforce it just in case
        truncated_content = content[:12000]
        
        message = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    num_flashcards=options.num_flashcards,
                    num_questions=options.num_questions,
                    difficulty=options.difficulty,
                    content=truncated_content
                )
            }]
        )
        
        raw = message.content[0].text
        data = json.loads(raw)  # Claude returns clean JSON per system prompt
        return GenerateResponse(**data)
    except json.JSONDecodeError as e:
        # Simple retry logic could be added here
        raise Exception(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise Exception(f"AI generation failed: {e}")

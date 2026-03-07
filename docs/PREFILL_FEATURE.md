# AI Response Prefilling Feature

## Overview

The prefill feature allows you to guide Claude's responses by providing an initial assistant message that Claude will continue from. This is particularly useful for ensuring consistent formatting, XML structure, or maintaining character voice in role-playing scenarios.

## How It Works

When using Anthropic models (Claude), you can include a `prefill` parameter in the `generate_text` method. Claude will treat this as the beginning of its response and continue from where the prefill text ends.

## Example Usage

### Basic Usage in ContentService

```python
from artificial_u.services.content_service import ContentService

content_service = ContentService()

# Guide the response to start with specific XML structure
response = await content_service.generate_text(
    prompt="Create a lecture outline for machine learning basics",
    prefill="<lecture_outline>",
    model="claude-opus-4-6"
)

# The response will start with "<lecture_outline>" and continue from there
print(response)  # "<lecture_outline>\n1. Introduction to ML\n2. ..."
```

### Lecture Generation

The lecture service automatically uses prefill to ensure responses start with the expected `<lecture_outline>` structure:

```python
# In LectureService._generate_and_parse_content()
raw_response = await self.content_service.generate_text(
    model=settings.LECTURE_GENERATION_MODEL,
    prompt=lecture_prompt,
    system_prompt=system_prompt,
    max_tokens=16384,
    prefill="<lecture_outline>",  # Ensures structured response
)
```

## Use Cases

### 1. XML Structure Consistency

```python
prefill = "<course>"
# Ensures the response starts with the expected XML tag
```

### 2. Formatting Consistency

```python
prefill = "## Summary\n\n"
# Ensures responses start with a consistent heading format
```

### 3. Character Voice Maintenance

```python
prefill = "Well hello there, students! *adjusts glasses* Today we're going to explore"
# Maintains a specific professor's personality and speaking style
```

### 4. Structured Lists

```python
prefill = "1. "
# Ensures the response starts as a numbered list
```

## Important Notes

### Backend Compatibility

- **Anthropic (Claude)**: ✅ Full support
- **OpenAI (GPT)**: ✅ Full support
- **Gemini**: ✅ Full support

### Best Practices

1. **Keep prefills short**: Prefills should be concise and focused
2. **No trailing whitespace**: Avoid trailing spaces or tabs in prefill content
3. **Test thoroughly**: Always test prefilled responses to ensure they work as expected
4. **Fallback handling**: Design your system to work even if prefill is ignored (for non-Anthropic models)

### Error Handling

The system gracefully handles prefill for non-Anthropic models by:

- Logging a warning that prefill is not supported
- Proceeding with normal generation (ignoring the prefill parameter)
- Maintaining backward compatibility

## Implementation Details

### ContentService Changes

The `generate_text` method now accepts an optional `prefill` parameter:

```python
async def generate_text(
    self,
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    prefill: Optional[str] = None,  # New parameter
) -> str:
```

### Anthropic Implementation

For Anthropic models, the prefill is added as an assistant message:

```python
messages = []
messages.append({"role": "user", "content": prompt})

# Add prefill assistant message if provided
if prefill:
    messages.append({"role": "assistant", "content": prefill})
```

## References

- [Anthropic Documentation - Prefill Claude's Response](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency#prefill-claude%E2%80%99s-response)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

# Replace placeholders like {{word_count}} with real values,
# because the SDK does not support variables.
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=20000,
    temperature=1,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": 'You are an AI assistant tasked with generating engaging university lecture texts for various courses. These lectures will be used in a text-to-speech engine, so it\'s crucial to create content that works well in spoken form. Your goal is to produce a lecture that is approximately {{word_count}} words long, narrative in style, and infused with the personality of an imagined lecturer.\n\nHere are the details for today\'s lecture:\n\nCourse: <course_name>{{course_name}}</course_name>\nLecture Topic: <lecture_topic>{{lecture_topic}}</lecture_topic>\n\nBefore writing the lecture, please plan your approach inside <lecture_preparation> tags. In your preparation:\n\n1. Develop a vivid persona for the lecturer, including:\n   - Name\n   - Physical appearance\n   - Mannerisms\n   - Background and expertise\n   - Speaking style\n\n2. Outline 5-7 main points for the lecture:\n   - For each point, note key information to cover\n   - Consider how each point builds on the previous one\n\n3. Identify 2-3 technical concepts that need to be explained in narrative form:\n   - Break down each concept into simpler components\n   - Brainstorm analogies or real-world examples to illustrate these concepts\n\n4. Brainstorm 3-5 engaging anecdotes or examples to illustrate key points:\n   - For each anecdote, note how it relates to the lecture content\n   - Consider how to transition into and out of these stories\n\n5. Consider how to structure the lecture for optimal audio delivery:\n   - Plan clear transitions between main points\n   - Note places where pauses or changes in tone might be effective\n\n6. Brainstorm potential questions students might ask:\n   - Prepare brief answers to these questions\n   - Consider how to naturally incorporate this information into the lecture\n\n7. Plan the pacing of the lecture:\n   - Estimate how long to spend on each main point\n   - Note where to place breaks or moments of levity\n\nAfter your preparation, write the lecture as a continuous text, following these guidelines:\n\n1. Begin with a vivid introduction that sets the scene and introduces the lecturer, similar to this example:\n   [Professor Volkov enters the lecture hall precisely at the scheduled time, wearing a navy blazer with a burgundy bow tie. He places his leather satchel on the desk and adjusts his tortoiseshell glasses while surveying the room. His salt and pepper hair is neatly combed to the side, and his thick mustache moves slightly as he begins to speak.]\n\n2. Write in a conversational, engaging style that reflects the lecturer\'s personality.\n\n3. Avoid complex mathematical formulas. If a formula is necessary, convert it to spoken language (e.g., "E equals m c squared" instead of "E=mc²").\n\n4. Include occasional stage directions in square brackets to bring the scene to life (e.g., [gesturing enthusiastically] or [pausing for effect]).\n\n5. Focus on creating a narrative flow rather than presenting dry facts.\n\n6. Aim for approximately {{word_count}} words in length.\n\nRemember, the goal is to create an educational and entertaining experience that works well in audio format, encouraging curiosity and self-education.\n\nYour output should follow this structure:\n\n<lecture_preparation>\n[Your detailed lecture preparation goes here]\n</lecture_preparation>\n\n<lecture>\n[The full lecture text, including introduction and stage directions]\n</lecture>',
                }
            ],
        }
    ],
)
print(message.content)

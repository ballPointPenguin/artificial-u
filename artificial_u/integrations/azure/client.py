import azure.cognitiveservices.speech as speechsdk

from artificial_u.config.settings import get_settings

settings = get_settings()


class AzureTTSClient:
    def __init__(self):
        self.speech_key = settings.SPEECH_KEY
        self.speech_region = settings.SPEECH_REGION

        if not self.speech_key or not self.speech_region:
            raise ValueError("SPEECH_KEY and SPEECH_REGION environment variables must be set.")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.speech_region
        )
        # Optional: Set the voice name if you have a preference.
        # Find more voices here:
        # https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
        # self.speech_config.speech_synthesis_voice_name = "en-US-AvaMultilingualNeural"

        # To output to a file, we configure AudioConfig,
        # otherwise it defaults to speaker output.
        # Example for speaker output (uncomment to use):
        # self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        # self.speech_synthesizer = speechsdk.SpeechSynthesizer(
        # speech_config=self.speech_config, audio_config=self.audio_config
        # )

    async def synthesize_to_file(self, text: str, output_filename: str = "output.wav") -> str:
        """
        Synthesizes the given text to an audio file.

        Args:
            text: The text to synthesize.
            output_filename: The name of the file to save the audio to.

        Returns:
            The path to the generated audio file.
        """
        # Configure audio output to a file
        file_audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=file_audio_config
        )

        speech_synthesis_result = await speech_synthesizer.speak_text_async(text)

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesized to [{output_filename}] for text [{text}]")
            return output_filename
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print(f"Error details: {cancellation_details.error_details}")
                    print("Did you set the speech resource key and region values correctly?")
            raise Exception(f"Speech synthesis failed: {cancellation_details.reason}")
        return ""  # Should not be reached if an exception is raised on failure


# Example usage (optional, for direct testing of this file):
# async def main():
#     import asyncio # Import here when main is active
#     try:
#         # Ensure SPEECH_KEY and SPEECH_REGION are set in your environment
#         # For example, in your .env file or shell:
#         # export SPEECH_KEY="your_azure_speech_key"
#         # export SPEECH_REGION="your_azure_speech_region"
#         client = AzureTTSClient()
#         text_to_speak = "Hello, this is a test of Azure Text to Speech."
#         output_file = await client.synthesize_to_file(
#             text_to_speak, "azure_test_output.wav"
#         )
#         if output_file:
#             print(f"Audio content written to file: {output_file}")

#     except ValueError as ve:
#         print(f"Configuration error: {ve}")
#     except Exception as e:
#         print(f"An error occurred: {e}")

if __name__ == "__main__":
    # To run the example:
    # 1. Ensure SPEECH_KEY and SPEECH_REGION environment variables are set.
    # 2. Uncomment the `async def main():` block above.
    # 3. Uncomment the `import asyncio` line inside `main`.
    # 4. Uncomment the following line:
    #    # asyncio.run(main())
    # 5. Run the script: `python -m artificial_u.integrations.azure.client`
    print(
        "To run the example, follow the commented instructions within this script's"
        " __main__ block."
    )

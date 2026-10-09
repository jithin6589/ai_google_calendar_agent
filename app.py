import chainlit as cl
from io import BytesIO
import wave

from chainlit.types import InputAudioChunk
from faster_whisper import WhisperModel

from datetime import datetime
from zoneinfo import ZoneInfo

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

from langchain.agents import create_agent

from agent import (
    MODELS_TO_TRY,
    create_gemini_model,
    delete_calendar_event,
    find_calendar_event,
    get_calendars,
    get_upcoming_events,
    create_calendar_event,
    SYSTEM_INSTRUCTION,
    update_calendar_event,
    search_calendar_events
)

#CONVERT THE USER MICROPHONE AUDIOS TO SMALL AUDIO CHUNKS FUNCTION

@cl.on_audio_start
async def on_audio_start():
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: InputAudioChunk):

    if chunk.isStart:

        buffer = BytesIO()

        cl.user_session.set(
            "audio_buffer",
            buffer
        )

    buffer = cl.user_session.get(
        "audio_buffer"
    )

    if buffer:
        buffer.write(chunk.data)

#THE COLLECTED AUDIO CHUNKS ARE PROCESSED AND TRANSCRIBED TO TEXT FUNCTION

@cl.on_audio_end
async def on_audio_end():

    audio_buffer = cl.user_session.get(
        "audio_buffer"
    )

    if not audio_buffer:
        return

    audio_buffer.seek(0)

    pcm_data = audio_buffer.read()

    if not pcm_data:
        await cl.Message(
            content="🎤 No audio received."
        ).send()
        return

    # PCM16 → WAV

    wav_filename = "input_audio.wav"

    with wave.open(
        wav_filename,
        "wb"
    ) as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(pcm_data)

    # Speech → Text

    segments, info = whisper_model.transcribe(
        wav_filename,
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True
    )

    transcription = ""

    for segment in segments:
        transcription += segment.text

    transcription = transcription.strip()

    if not transcription:

        await cl.Message(
            content="🎤 I couldn't understand the audio."
        ).send()

        return

    await cl.Message(
        content=f"🎤 **You said:** {transcription}"
    ).send()

    await run_agent(transcription)

# EXTRACT CLEAN TEXT FROME GEMINI REPLEY

def extract_text(message):

    content = message.content

    # If content is a normal string
    if isinstance(content, str):

        return content

    # If Gemini returns content blocks
    if isinstance(content, list):

        text_parts = []

        for block in content:

            if isinstance(block, dict):

                if block.get("type") == "text":

                    text = block.get(
                        "text",
                        ""
                    )

                    if text:

                        text_parts.append(
                            text
                        )
        return "\n".join(
            text_parts
        )
    return str(content)
# CHAINLIT MESSAGE HANDLER

# RUN LANGCHAIN AGENT
async def run_agent(user_text):

    current_time = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    current_date_time = current_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Get previous conversation history
    history = cl.user_session.get(
        "history",
        []
    )

    # Add current user message to history
    history.append(
        {
            "role": "user",
            "content": user_text
        }
    )

    # TRY GEMINI MODELS

    last_error = None

    for model_name in MODELS_TO_TRY:

        try:

            print(
                f"Trying Gemini model: "
                f"{model_name}"
            )

            # CREATE GEMINI MODEL

            llm = create_gemini_model(
                model_name
            )

            # CREATE LANGCHAIN AGENT

            agent = create_agent(

                model=llm,

                tools=[
                    get_calendars,
                    get_upcoming_events,
                    create_calendar_event,
                    find_calendar_event,
                    update_calendar_event,
                    delete_calendar_event,
                    search_calendar_events
                ],

                system_prompt=SYSTEM_INSTRUCTION
            )

            # SEND USER MESSAGE TO AGENT

            response = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"Current date and time is "
                                f"{current_date_time} "
                                f"in Asia/Kolkata timezone.\n\n"

                                "IMPORTANT DATE RULE:\n"
                                "Use this current date and time "
                                "when interpreting relative dates "
                                "such as today, tomorrow, "
                                "next Monday, next Friday, "
                                "this weekend, etc.\n\n"

                                "Do not assume an old year such "
                                "as 2024 or 2025.\n\n"

                                "IMPORTANT TIMEZONE RULE:\n"
                                "Use Asia/Kolkata timezone.\n\n"

                                "IMPORTANT CONVERSATION RULE:\n"
                                "Use the previous conversation history "
                                "to understand references such as "
                                "'this event', 'that event', "
                                "'the same event', or a number "
                                "selected from a previous list."
                            )
                        },
                        {
                            "role": "user",
                            "content": user_text
                        }
                    ] + history
                }
            )

            # GET FINAL MESSAGE

            final_message = response[
                "messages"
            ][-1]

            # EXTRACT CLEAN TEXT

            final_text = extract_text(
                final_message
            )

            # SEND RESPONSE TO CHAINLIT

            await cl.Message(
                content=final_text
            ).send()

            print(
                f"Success with model: "
                f"{model_name}"
            )

            # Update session history

            history.append(
                {
                    "role": "assistant",
                    "content": final_text
                }
            )

            cl.user_session.set(
                "history",
                history
            )

            return

        # ERROR HANDLING

        except Exception as e:

            last_error = e

            error_text = str(e).lower()

            print(
                f"Model {model_name} failed: "
                f"{type(e).__name__}: {e}"
            )

            # TRY NEXT GEMINI MODEL

            if any(
                term in error_text
                for term in [
                    "429",
                    "quota",
                    "resource_exhausted",
                    "503",
                    "unavailable",
                    "500",
                    "502",
                    "504",
                    "rate_limit",
                    "overloaded"
                ]
            ):

                continue

            # OTHER ERRORS

            raise e

    # ALL MODELS FAILED

    await cl.Message(
        content=(
            "⚠️ All Gemini models are "
            "currently unavailable.\n\n"
            "Please try again later."
        )
    ).send()

    print(
        f"All models failed. "
        f"Last error: {last_error}"
    )

# CHAINLIT MESSAGE HANDLER

@cl.on_message
async def main(message: cl.Message):

    await run_agent(
        message.content
    )
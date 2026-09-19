import os
import json

import chainlit as cl

from dotenv import load_dotenv
from google import genai

from calendar_tools import list_calendars


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

print(
    "Gemini API key found:",
    bool(api_key)
)


client = genai.Client(
    api_key=api_key
)


# -----------------------------------------
# Gemini Tool
# -----------------------------------------

list_calendars_tool = {
    "type": "function",
    "name": "list_calendars",
    "description": (
        "List all Google Calendars available "
        "to the user."
    ),
    "parameters": {
        "type": "object",
        "properties": {}
    }
}


# -----------------------------------------
# System Instruction
# -----------------------------------------

SYSTEM_INSTRUCTION = """
You are a Google Calendar AI assistant.

You can help the user manage their Google Calendar.

Available tool:

list_calendars
- Use this tool when the user asks to see,
  show, list, or check their calendars.

Important:
- Do not invent calendar names.
- When the user asks for their calendars,
  use the list_calendars tool.
"""


# -----------------------------------------
# Chainlit
# -----------------------------------------

@cl.on_message
async def main(message: cl.Message):

    try:

        # Ask Gemini
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=message.content,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[
                list_calendars_tool
            ]
        )


        # ---------------------------------
        # Check function call
        # ---------------------------------

        function_call = None

        for step in interaction.steps:

            if step.type == "function_call":

                function_call = step

                break


        # ---------------------------------
        # Normal Gemini response
        # ---------------------------------

        if function_call is None:

            await cl.Message(
                content=interaction.output_text
            ).send()

            return


        # ---------------------------------
        # Execute Calendar function
        # ---------------------------------

        if function_call.name == "list_calendars":

            print(
                "Gemini called: list_calendars()"
            )

            result = list_calendars()

        else:

            result = {
                "error": (
                    f"Unknown function: "
                    f"{function_call.name}"
                )
            }


        # ---------------------------------
        # Send result back to Gemini
        # ---------------------------------

        final_interaction = client.interactions.create(

            model="gemini-3.6-flash",

            previous_interaction_id=interaction.id,

            input=[
                {
                    "type": "function_result",

                    "name": function_call.name,

                    "call_id": function_call.id,

                    "result": [
                        {
                            "type": "text",

                            "text": json.dumps(
                                result
                            )
                        }
                    ]
                }
            ]
        )


        # ---------------------------------
        # Final response
        # ---------------------------------

        await cl.Message(
            content=final_interaction.output_text
        ).send()


    except Exception as e:

        await cl.Message(
            content=f"⚠️ Error:\n\n{str(e)}"
        ).send()
from dotenv import load_dotenv
from groq import Groq
import json
import requests
import os


# ---------------- ENVIRONMENT ---------------- #

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ---------------- TOOLS ---------------- #

def get_weather(city: str):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return f"The weather in {city} is {response.text}"

        return "Unable to fetch weather"

    except Exception as e:
        return f"Weather error: {e}"


def calculate(expression: str):
    try:
        result = eval(expression)
        return f"Result: {result}"

    except Exception as e:
        return f"Calculation error: {e}"


available_tools = {
    "get_weather": get_weather,
    "calculate": calculate
}


# ---------------- SYSTEM PROMPT ---------------- #

SYSTEM_PROMPT = """
You are a helpful AI assistant.

You have two tools:

1. get_weather(city)
2. calculate(expression)

You must return EXACTLY ONE JSON object.

For a request that requires a tool, return:

{
    "step": "action",
    "function": "tool_name",
    "input": "tool_input"
}

For a normal question that does not require a tool, return:

{
    "step": "output",
    "content": "answer"
}

Do not return multiple JSON objects.
Do not return markdown.
Do not return any text outside the JSON object.
"""


# ---------------- MESSAGE HISTORY ---------------- #

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


# ---------------- START ---------------- #

print("Groq Agent Started")
print("Type 'exit' to quit")


# ---------------- MAIN LOOP ---------------- #

while True:

    query = input("\n> ")

    if query.lower() == "exit":
        print("Agent stopped.")
        break

    messages.append({
        "role": "user",
        "content": query
    })


    try:

        # ---------------- AI REQUEST ---------------- #

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"}
        )


        assistant_message = response.choices[0].message.content

        messages.append({
            "role": "assistant",
            "content": assistant_message
        })


        # ---------------- PARSE JSON ---------------- #

        parsed_response = json.loads(assistant_message)


        # ---------------- ACTION ---------------- #

        if parsed_response.get("step") == "action":

            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")

            print(
                f"ACTION: {tool_name}({tool_input})"
            )


            if tool_name in available_tools:

                tool_output = available_tools[tool_name](tool_input)

                print(
                    f"OBSERVE: {tool_output}"
                )


                # Ask the AI to convert the tool result
                # into a final answer.

                messages.append({
                    "role": "user",
                    "content": f"""
The tool returned this result:

{tool_output}

Return ONLY this JSON format:

{{
    "step": "output",
    "content": "final answer"
}}
"""
                })


                final_response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    response_format={"type": "json_object"}
                )


                final_message = final_response.choices[0].message.content

                messages.append({
                    "role": "assistant",
                    "content": final_message
                })


                final_json = json.loads(final_message)

                print(
                    f"OUTPUT: {final_json.get('content')}"
                )


            else:

                print(
                    f"ERROR: Unknown tool: {tool_name}"
                )


        # ---------------- DIRECT OUTPUT ---------------- #

        elif parsed_response.get("step") == "output":

            print(
                f"OUTPUT: {parsed_response.get('content')}"
            )


        else:

            print("ERROR: Unknown response step")
            print(parsed_response)


    except json.JSONDecodeError:

        print("ERROR: The AI returned invalid JSON.")
        print("Raw response:", assistant_message)


    except Exception as e:

        print("ERROR:", e)

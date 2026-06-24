from dotenv import load_dotenv
from groq import Groq
import json
import requests
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ---------------- TOOLS ---------------- #

def get_weather(city: str):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url)

        if response.status_code == 200:
            return f"The weather in {city} is {response.text}"

        return "Unable to fetch weather"

    except Exception as e:
        return str(e)


def calculate(expression: str):
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return str(e)


available_tools = {
    "get_weather": get_weather,
    "calculate": calculate
}

# ---------------- SYSTEM PROMPT ---------------- #

SYSTEM_PROMPT = """
You are a helpful AI Assistant.

You work in:
1. plan
2. action
3. output

Always return JSON only.

Format:

{
    "step":"plan|action|output",
    "content":"text",
    "function":"tool_name",
    "input":"tool_input"
}

Available Tools:

1. get_weather(city)
2. calculate(expression)

Example:

{"step":"plan","content":"User wants weather"}

{"step":"action","function":"get_weather","input":"Hyderabad"}

{"step":"output","content":"Weather retrieved"}
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

print("Groq Agent Started")
print("Type 'exit' to quit")

while True:

    query = input("\n> ")

    if query.lower() == "exit":
        break

    messages.append({
        "role": "user",
        "content": query
    })

    while True:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            response_format={"type": "json_object"}
        )

        assistant_message = response.choices[0].message.content

        messages.append({
            "role": "assistant",
            "content": assistant_message
        })

        parsed_response = json.loads(assistant_message)

        if parsed_response.get("step") == "plan":

            print(
                f"PLAN: {parsed_response.get('content')}"
            )
            continue

        elif parsed_response.get("step") == "action":

            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")

            print(
                f"ACTION: {tool_name}({tool_input})"
            )

            if tool_name in available_tools:

                output = available_tools[tool_name](tool_input)

                print(
                    f"OBSERVE: {output}"
                )

                messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "step": "observe",
                        "output": output
                    })
                })

                continue

        elif parsed_response.get("step") == "output":

            print(
                f"OUTPUT: {parsed_response.get('content')}"
            )

            break
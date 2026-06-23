from dotenv import load_dotenv
from groq import Groq
import json
import yfinance as yf
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ---------------- TOOLS ---------------- #

def get_stock_price(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        company = info.get("shortName", symbol)
        price = info.get("currentPrice")

        return f"{company} ({symbol.upper()}) current price is ${price}"

    except Exception as e:
        return f"Error fetching stock data: {str(e)}"


def calculate(expression: str):
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation Error: {str(e)}"


available_tools = {
    "get_stock_price": get_stock_price,
    "calculate": calculate
}

# ---------------- SYSTEM PROMPT ---------------- #

SYSTEM_PROMPT = """
You are a helpful AI Assistant.

You work in:
1. plan
2. action
3. output

Always return valid JSON.

Format:

{
    "step":"plan|action|output",
    "content":"text",
    "function":"tool_name",
    "input":"tool_input"
}

Available Tools:

1. get_stock_price(symbol)
   Returns current stock price.

2. calculate(expression)
   Calculates mathematical expressions.

Examples:

User: What is Apple's stock price?

{
    "step":"plan",
    "content":"User wants stock information."
}

{
    "step":"action",
    "function":"get_stock_price",
    "input":"AAPL"
}

{
    "step":"output",
    "content":"Stock information retrieved."
}

User: Calculate 25*8

{
    "step":"plan",
    "content":"User wants a calculation."
}

{
    "step":"action",
    "function":"calculate",
    "input":"25*8"
}

{
    "step":"output",
    "content":"Calculation completed."
}
"""

# ---------------- CHAT HISTORY ---------------- #

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

print("📈 Groq Stock Market Agent Started")
print("Type 'exit' to quit")

# ---------------- AGENT LOOP ---------------- #

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

        # PLAN
        if parsed_response.get("step") == "plan":

            print(
                f"🧠 PLAN: {parsed_response.get('content')}"
            )

            continue

        # ACTION
        elif parsed_response.get("step") == "action":

            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")

            print(
                f"🛠 ACTION: Calling {tool_name}({tool_input})"
            )

            if tool_name in available_tools:

                output = available_tools[tool_name](tool_input)

                print(
                    f"👀 OBSERVE: {output}"
                )

                messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "step": "observe",
                        "output": output
                    })
                })

                continue

            else:

                print("❌ Tool not found")
                break

        # OUTPUT
        elif parsed_response.get("step") == "output":

            print(
                f"🤖 OUTPUT: {parsed_response.get('content')}"
            )

            break
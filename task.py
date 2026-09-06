import os
import sys
from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------
# Load environment
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("UNCLEAR")
    sys.exit(1)

client = genai.Client(api_key=api_key)


# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------

if len(sys.argv) < 3:
    print("UNCLEAR")
    sys.exit(1)

declared_task = sys.argv[1]
activity = sys.argv[2]


# ---------------------------------------------------------
# Prompt
# ---------------------------------------------------------

prompt = f"""
You are Anchor, a focus assistant.

The user declared this task:

{declared_task}

Here is the user's recent terminal activity:

{activity}

Determine whether the activity is related to the declared task.

Return ONLY one of:

ON_TASK
OFF_TASK
UNCLEAR

Rules:

ON_TASK:
The activity directly contributes to the task or is a
reasonable supporting step.

OFF_TASK:
The activity is clearly unrelated to the declared task.

UNCLEAR:
There is not enough information to confidently decide.

Do not judge the user.

Do not classify an activity as OFF_TASK merely because
it is a technical command, debugging step, research step,
file navigation, installation, testing, or setup activity.

Return ONLY the classification.
"""


# ---------------------------------------------------------
# Gemini
# ---------------------------------------------------------

try:

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    result = response.text.strip().upper()

    if "ON_TASK" in result:
        print("ON_TASK")

    elif "OFF_TASK" in result:
        print("OFF_TASK")

    else:
        print("UNCLEAR")

except Exception:
    print("UNCLEAR")
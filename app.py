import os
from datetime import datetime

import streamlit as st
import gspread

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool


# ============================================================
# 1. STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Multi-Agent Customer Support",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# 2. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ============================================================
# 3. CHECK API KEYS
# ============================================================

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY is missing in .env file.")
    st.stop()

if not SERPER_API_KEY:
    st.error("SERPER_API_KEY is missing in .env file.")
    st.stop()


# ============================================================
# 4. GOOGLE SHEETS CONNECTION
# ============================================================

GOOGLE_SERVICE_ACCOUNT_FILE = "google-service-account.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


try:
    credentials = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    google_client = gspread.authorize(credentials)

    spreadsheet = google_client.open("Customer Support Records")
    worksheet = spreadsheet.sheet1

except Exception as e:
    st.error(f"Google Sheets connection failed: {e}")
    st.stop()


# ============================================================
# 5. CURRENT DATE
# ============================================================

current_date = datetime.now().strftime("%B %d, %Y")


# ============================================================
# 6. WEB SEARCH TOOL
# ============================================================

search_tool = SerperDevTool()


# ============================================================
# 7. AGENT 1
#    CUSTOMER SUPPORT ASSISTANT
#    OWN KNOWLEDGE ONLY
# ============================================================

assistant_agent = Agent(
    role="Customer Support Assistant",

    goal=(
        "Answer the customer's question clearly and directly "
        "using your own available knowledge."
    ),

    backstory=(
        "You are the first-level customer support assistant. "
        "You answer questions directly using your own knowledge. "
        "You do not use web search or external tools."
    ),

    verbose=True
)


# ============================================================
# 8. AGENT 2
#    WEB SEARCH ASSISTANT
# ============================================================

web_search_agent = Agent(
    role="Web Search Assistant",

    goal=(
        "Search the web and provide accurate, recent information "
        "when the customer's question requires current information."
    ),

    backstory=(
        "You are a web research specialist. "
        "You use web search to find current and reliable information. "
        "For questions involving today's news, latest developments, "
        "recent events, current information, or new announcements, "
        "you must perform a fresh web search and prioritize recent sources."
    ),

    tools=[search_tool],

    verbose=True
)


# ============================================================
# 9. AGENT 3
#    ENTRY / RECORD AGENT
# ============================================================

entry_agent = Agent(
    role="Entry Agent",

    goal=(
        "Organize Answer 1 and Answer 2 clearly so they can be "
        "stored as a customer support record."
    ),

    backstory=(
        "You are responsible for organizing the responses generated "
        "by the first two agents. Keep Answer 1 and Answer 2 separate. "
        "Do not swap them. Do not invent information. "
        "The original customer query is preserved separately by Python."
    ),

    verbose=True
)


# ============================================================
# 10. TASK 1
#     AGENT 1 TASK
# ============================================================

task1 = Task(
    description="""
Customer Query:

{query}

Answer the customer's query using your own knowledge.

IMPORTANT:

- Do not use web search.
- Do not use external tools.
- Answer directly.
- If the question requires current information that you do not know,
  clearly explain that limitation.
- Do not invent current facts.

Return only the answer that should be shown to the customer.
""",

    expected_output=(
        "A clear and helpful answer to the customer's query "
        "based only on the assistant's own knowledge."
    ),

    agent=assistant_agent
)


# ============================================================
# 11. TASK 2
#     AGENT 2 WEB SEARCH TASK
# ============================================================

task2 = Task(
    description=f"""
CURRENT DATE: {current_date}

Customer Query:

{{query}}

You are the Web Search Assistant.

Your job is to answer the customer's question using current web
information when required.

IMPORTANT RULES:

1. If the query contains words such as:

   today
   now
   current
   latest
   recent
   recently
   new
   nowadays

   you MUST perform a fresh web search.

2. For current news questions, use the current date:

   "{current_date}"

3. For example, if the customer asks:

   "today AI news"

   perform searches similar to:

   - latest AI news {current_date}
   - AI news today {current_date}
   - latest AI announcements {current_date}
   - recent AI developments {current_date}

4. Prefer articles published on or very close to:

   {current_date}

5. DO NOT present old 2023, 2024, or 2025 information as today's
   news unless the user specifically asks about historical news.

6. Check the publication date of search results whenever available.

7. Give actual news items.

   Do NOT simply provide a list of news websites.

8. For each important news item, provide:

   - Headline or topic
   - What happened
   - Company/person involved
   - Publication date
   - Source

9. Prefer reliable sources such as:

   Reuters
   Associated Press
   Official company blogs
   Google
   Microsoft
   OpenAI
   Anthropic
   NVIDIA
   Meta
   TechCrunch
   The Verge

10. If current reliable information cannot be found, clearly say so.

11. Never invent a news story.

12. Do not claim that an old article is today's news.

13. For a news query, provide a concise summary rather than a huge
    list of links.

Return a clear answer suitable for the customer.

""",

    expected_output=(
        "A current web-researched answer with recent information, "
        "dates, relevant facts, and source references."
    ),

    agent=web_search_agent
)


# ============================================================
# 12. TASK 3
#     ENTRY AGENT TASK
# ============================================================

task3 = Task(
    description="""
Review the outputs from Task 1 and Task 2.

Create a clean record containing:

ANSWER 1:
The complete answer produced by the Customer Support Assistant.

ANSWER 2:
The complete answer produced by the Web Search Assistant.

IMPORTANT:

- Keep Answer 1 exactly as Answer 1.
- Keep Answer 2 exactly as Answer 2.
- Do not swap the answers.
- Do not rewrite the original customer query.
- Do not invent information.
- Do not add your own answer.
- Do not mix content between Answer 1 and Answer 2.
- The original query will be stored separately by Python.

Return only:

ANSWER 1:
...

ANSWER 2:
...
""",

    expected_output=(
        "A clean record containing Answer 1 and Answer 2 "
        "without mixing their content."
    ),

    agent=entry_agent,

    context=[task1, task2]
)


# ============================================================
# 13. CREW
# ============================================================

crew = Crew(
    agents=[
        assistant_agent,
        web_search_agent,
        entry_agent
    ],

    tasks=[
        task1,
        task2,
        task3
    ],

    process=Process.sequential,

    verbose=True
)


# ============================================================
# 14. STREAMLIT UI
# ============================================================

st.title("🤖 Multi-Agent Customer Support System")

st.write("### CrewAI + Web Search + Google Sheets")

st.info(
    "Three sequential AI agents: "
    "Customer Support → Web Search → Entry Agent"
)


# ============================================================
# 15. CUSTOMER QUERY INPUT
# ============================================================

st.subheader("💬 Customer Query")

user_query = st.text_area(
    "Enter your question:",
    placeholder=(
        "Example: today AI news sollu\n"
        "Example: What is Python?\n"
        "Example: latest AI developments"
    ),
    height=120
)


# ============================================================
# 16. SUBMIT BUTTON
# ============================================================

if st.button("🚀 Submit Query", type="primary"):

    if not user_query.strip():

        st.warning("Please enter a customer query.")

    else:

        # ----------------------------------------------------
        # SHOW SUBMITTED QUERY
        # ----------------------------------------------------

        st.subheader("📝 Submitted Query")

        st.write(user_query)


        # ----------------------------------------------------
        # SHOW CURRENT DATE USED BY WEB SEARCH
        # ----------------------------------------------------

        st.caption(
            f"Web Search Reference Date: {current_date}"
        )


        # ----------------------------------------------------
        # RUN CREWAI
        # ----------------------------------------------------

        with st.spinner(
            "🤖 Running 3 sequential AI agents..."
        ):

            try:

                result = crew.kickoff(
                    inputs={
                        "query": user_query,
                        "current_date": current_date
                    }
                )

            except Exception as e:

                st.error(
                    f"CrewAI execution failed: {e}"
                )

                st.stop()


        # ----------------------------------------------------
        # GET AGENT OUTPUTS
        # ----------------------------------------------------

        answer1 = task1.output.raw

        answer2 = task2.output.raw

        entry_record = task3.output.raw


        # ====================================================
        # 17. DISPLAY ANSWER 1
        # ====================================================

        st.subheader(
            "💬 Answer 1 - Customer Support Assistant"
        )

        st.markdown(answer1)


        # ====================================================
        # 18. DISPLAY ANSWER 2
        # ====================================================

        st.subheader(
            "🌐 Answer 2 - Web Search Assistant"
        )

        st.markdown(answer2)


        # ====================================================
        # 19. DISPLAY ENTRY AGENT OUTPUT
        # ====================================================

        st.subheader("📋 Entry Agent Record")

        with st.expander("View Agent 3 Output"):

            st.text(entry_record)


        # ====================================================
        # 20. CREATE FINAL RECORD USING PYTHON
        # ====================================================

        record_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        final_record = f"""
========================================
CUSTOMER SUPPORT RECORD
========================================

DATE AND TIME:
{record_time}

ORIGINAL CUSTOMER QUERY:
{user_query}

========================================
ANSWER 1 - CUSTOMER SUPPORT ASSISTANT
========================================

{answer1}

========================================
ANSWER 2 - WEB SEARCH ASSISTANT
========================================

{answer2}

========================================
"""


        # ====================================================
        # 21. SAVE TO TXT
        # ====================================================

        try:

            with open(
                "answers.txt",
                "w",
                encoding="utf-8"
            ) as file:

                file.write(final_record)

            txt_saved = True

        except Exception as e:

            txt_saved = False

            st.error(
                f"TXT save failed: {e}"
            )


        # ====================================================
        # 22. SAVE TO GOOGLE SHEETS
        # ====================================================

        try:

            worksheet.append_row(
                [
                    user_query,
                    answer1,
                    answer2
                ],
                value_input_option="USER_ENTERED"
            )

            sheet_saved = True

        except Exception as e:

            sheet_saved = False

            st.error(
                f"Google Sheets save failed: {e}"
            )


        # ====================================================
        # 23. SAVE STATUS
        # ====================================================

        st.subheader("💾 Save Status")

        if txt_saved:

            st.success(
                "Customer record saved to answers.txt"
            )

        if sheet_saved:

            st.success(
                "Customer record saved to Google Sheets"
            )

        if txt_saved and sheet_saved:

            st.success(
                "✅ All operations completed successfully!"
            )


        # ====================================================
        # 24. NEXT QUERY MESSAGE
        # ====================================================

        st.info(
            "Enter another question above and click Submit Query."
        )
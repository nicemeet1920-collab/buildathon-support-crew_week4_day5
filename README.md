# 🤖 Multi-Agent Customer Support System

### CrewAI + Streamlit + Web Search + Google Sheets

A multi-agent customer support application built using **CrewAI** and **Streamlit**.

The system uses three sequential AI agents to answer customer questions, search the web for current information, organize the responses, and store the customer interaction in both a TXT file and Google Sheets.

---

## 🚀 Project Overview

This project demonstrates a sequential multi-agent workflow using CrewAI.

The customer enters a question through the Streamlit interface.

The question is then processed by three AI agents:

1. **Customer Support Assistant**
2. **Web Search Assistant**
3. **Entry Agent**

The final customer interaction is stored in:

- `answers.txt`
- Google Sheets

---

## 🧠 Multi-Agent Architecture

```text
                    👤 CUSTOMER
                         │
                         ▼
                ┌─────────────────┐
                │    Streamlit    │
                │      UI         │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │     CrewAI      │
                │ Sequential Flow │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌───────────┐  ┌─────────────┐  ┌───────────┐
    │  Agent 1  │  │   Agent 2   │  │  Agent 3  │
    │           │  │             │  │           │
    │ Customer  │  │ Web Search  │  │   Entry   │
    │ Support   │  │  Assistant  │  │   Agent   │
    │ Assistant │  │             │  │           │
    └─────┬─────┘  └──────┬──────┘  └─────┬─────┘
          │               │                │
          │               │                │
          └───────────────┴────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Python Record   │
                 │ Generation      │
                 └────────┬────────┘
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
          ┌─────────────┐   ┌──────────────┐
          │ answers.txt │   │ Google Sheet │
          └─────────────┘   └──────────────┘
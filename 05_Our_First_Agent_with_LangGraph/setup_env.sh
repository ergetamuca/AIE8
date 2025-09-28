#!/bin/bash

echo "Setting up environment variables for LangGraph Agent..."

# Prompt for API keys
echo "Enter your OpenAI API Key (starts with sk-):"
read -s OPENAI_KEY
export OPENAI_API_KEY="$OPENAI_KEY"

echo "Enter your Tavily API Key (starts with tvly-):"
read -s TAVILY_KEY
export TAVILY_API_KEY="$TAVILY_KEY"

echo "Enter your LangSmith API Key (starts with ls__):"
read -s LANGSMITH_KEY
export LANGCHAIN_API_KEY="$LANGSMITH_KEY"

echo ""
echo "Environment variables set successfully!"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "TAVILY_API_KEY: ${TAVILY_API_KEY:0:10}..."
echo "LANGCHAIN_API_KEY: ${LANGCHAIN_API_KEY:0:10}..."

echo ""
echo "You can now run: jupyter notebook"

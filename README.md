# Unified LLM Chat

A streamlined web interface that provides a unified chat experience for various Large Language Models (LLMs).

## Features

- **Multiple LLM Provider Support**: Connect to different LLM providers using their API endpoints
- **Model Selection**: Choose from available models for each provider
- **Admin Interface**: Securely manage API keys and provider settings
- **Responsive UI**: Clean, intuitive chat interface built with Streamlit
- **Streaming Responses**: See AI responses as they're generated in real-time
- **Conversation History**: Maintain chat history within the session
- **Password Protection**: Admin settings secured with password authentication

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/unified-llm-chat.git
   cd unified-llm-chat
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

## Configuration

### First-time Setup

1. When you first run the application, click on the "API Settings" tab in the sidebar
2. Enter the admin password (default: `admin123`)
3. Add your first LLM provider with:
   - Provider name (e.g., "OpenAI", "Anthropic", "Local LLM")
   - Base URL (e.g., "https://api.openai.com/v1", "http://localhost:11434/v1")
   - API key
   - List of available models (one per line)

### Changing Admin Password

1. Navigate to the "API Settings" tab
2. Scroll down to "Change Admin Password"
3. Enter a new password and click "Update Password"

## Usage

1. Select a provider and model from the "Chat Settings" tab
2. Type your message in the input field at the bottom of the chat
3. View the AI's response in the chat window
4. Use "Clear Chat" to start a new conversation or "Retry Last" to regenerate the last AI response

## Requirements

- Python 3.7+
- Streamlit
- OpenAI Python library

## Security Notes

- API keys are stored locally in a `settings.json` file
- Admin password is stored as a SHA-256 hash
- Consider implementing additional security measures for production use

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
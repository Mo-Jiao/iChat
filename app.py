import streamlit as st
import openai
import json
import os
from datetime import datetime
import hashlib

# Page configuration
st.set_page_config(
    page_title="Unified LLM Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "settings" not in st.session_state:
    st.session_state.settings = {
        "base_urls": {},  # Store multiple baseURLs
        "api_keys": {},   # Store multiple API Keys
        "models": {},     # Store model lists for different baseURLs
        "admin_password": hashlib.sha256("admin123".encode()).hexdigest()  # Default admin password
    }

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "current_base_url" not in st.session_state:
    st.session_state.current_base_url = ""

if "current_api_key" not in st.session_state:
    st.session_state.current_api_key = ""

if "current_model" not in st.session_state:
    st.session_state.current_model = ""

# Load settings
def load_settings():
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as f:
            settings = json.load(f)
            
            # Ensure admin_password is preserved
            admin_password = st.session_state.settings.get("admin_password", hashlib.sha256("admin123".encode()).hexdigest())
            
            # Update settings
            st.session_state.settings.update(settings)
            
            # Ensure admin_password exists
            if "admin_password" not in st.session_state.settings:
                st.session_state.settings["admin_password"] = admin_password
            
            # Set default values
            if settings["base_urls"]:
                first_url = next(iter(settings["base_urls"]))
                st.session_state.current_base_url = first_url
                
            if settings["api_keys"]:
                first_key = next(iter(settings["api_keys"]))
                st.session_state.current_api_key = settings["api_keys"][first_key]
                
            if st.session_state.current_base_url and st.session_state.current_base_url in settings["models"]:
                if settings["models"][st.session_state.current_base_url]:
                    st.session_state.current_model = settings["models"][st.session_state.current_base_url][0]

# Save settings
def save_settings():
    # Create a copy of settings to save
    settings_to_save = {
        "base_urls": st.session_state.settings["base_urls"],
        "api_keys": st.session_state.settings["api_keys"],
        "models": st.session_state.settings["models"],
        "admin_password": st.session_state.settings["admin_password"]
    }
    
    with open("settings.json", "w") as f:
        json.dump(settings_to_save, f)

# Try to load settings
try:
    load_settings()
except Exception as e:
    st.error(f"Failed to load settings: {e}")

# Sidebar - Settings
with st.sidebar:
    st.title("🤖 Unified LLM Chat")
    
    # Admin login section
    if not st.session_state.is_admin:
        admin_password = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if hashlib.sha256(admin_password.encode()).hexdigest() == st.session_state.settings["admin_password"]:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        if st.button("Logout Admin"):
            st.session_state.is_admin = False
            st.rerun()
    
    # Create tabs
    tab1, tab2 = st.tabs(["Chat Settings", "API Settings"])
    
    with tab1:
        # Create a list of all available models with their providers
        all_models = []
        for provider, models in st.session_state.settings["models"].items():
            for model in models:
                all_models.append({
                    "display_name": f"[{provider}] {model}",
                    "provider": provider,
                    "model": model
                })
        
        if all_models:
            # Find current selection index
            current_index = 0
            for i, model_info in enumerate(all_models):
                if (model_info["provider"] == st.session_state.current_base_url and 
                    model_info["model"] == st.session_state.current_model):
                    current_index = i
                    break
            
            # Create selection box with combined provider-model names
            selected_option = st.selectbox(
                "Select Model",
                options=range(len(all_models)),
                format_func=lambda x: all_models[x]["display_name"],
                index=current_index
            )
            
            # Update provider and model based on selection
            selected_model_info = all_models[selected_option]
            if (selected_model_info["provider"] != st.session_state.current_base_url or 
                selected_model_info["model"] != st.session_state.current_model):
                st.session_state.current_base_url = selected_model_info["provider"]
                st.session_state.current_model = selected_model_info["model"]
                st.session_state.current_api_key = st.session_state.settings["api_keys"][selected_model_info["provider"]]
        else:
            st.warning("Please add a provider and models in API Settings first")
        
        # Function buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("Retry Last", use_container_width=True) and st.session_state.messages:
                # Remove the last assistant message if it exists
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                    st.session_state.messages.pop()
                    
                    # Check if valid settings exist
                    if not st.session_state.current_base_url or not st.session_state.current_api_key or not st.session_state.current_model:
                        with st.chat_message("assistant"):
                            st.error("Please complete API settings in the sidebar first")
                    else:
                        # Show AI thinking
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            message_placeholder.markdown("Thinking...")
                            
                            try:
                                # Configure OpenAI client
                                client = openai.OpenAI(
                                    base_url=st.session_state.settings["base_urls"][st.session_state.current_base_url],
                                    api_key=st.session_state.current_api_key
                                )
                                
                                # Prepare message history
                                messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                                
                                # Call API
                                response = client.chat.completions.create(
                                    model=st.session_state.current_model,
                                    messages=messages,
                                    stream=True
                                )
                                
                                # Stream output
                                full_response = ""
                                for chunk in response:
                                    if chunk.choices[0].delta.content:
                                        full_response += chunk.choices[0].delta.content
                                        message_placeholder.markdown(full_response + "▌")
                                
                                # Update final response
                                message_placeholder.markdown(full_response)
                                
                                # Add AI reply to chat history
                                st.session_state.messages.append({"role": "assistant", "content": full_response})
                                
                            except Exception as e:
                                error_message = f"Error occurred: {str(e)}"
                                message_placeholder.error(error_message)
                                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.rerun()
    
    with tab2:
        if not st.session_state.is_admin:
            st.warning("Please login as admin first")
        else:
            st.subheader("Add/Edit Provider")
            
            # Add new baseURL
            new_provider_name = st.text_input("Provider Name", key="new_provider_name")
            new_base_url = st.text_input("Base URL", key="new_base_url")
            new_api_key = st.text_input("API Key", type="password", key="new_api_key")
            
            # Model list
            new_models = st.text_area("Models (one per line)", key="new_models")
            
            if st.button("Save Settings", use_container_width=True):
                if new_provider_name and new_base_url:
                    # Update settings
                    st.session_state.settings["base_urls"][new_provider_name] = new_base_url
                    st.session_state.settings["api_keys"][new_provider_name] = new_api_key
                    
                    # Process model list
                    models_list = [model.strip() for model in new_models.split("\n") if model.strip()]
                    st.session_state.settings["models"][new_provider_name] = models_list
                    
                    # Save settings
                    save_settings()
                    
                    # If this is the first setting, select it automatically
                    if len(st.session_state.settings["base_urls"]) == 1:
                        st.session_state.current_base_url = new_provider_name
                        st.session_state.current_api_key = new_api_key
                        if models_list:
                            st.session_state.current_model = models_list[0]
                    
                    st.success("Settings saved")
                    st.rerun()
                else:
                    st.error("Provider name and Base URL cannot be empty")
            
            # Display current settings
            st.subheader("Current Settings")
            for provider in st.session_state.settings["base_urls"]:
                with st.expander(f"{provider}"):
                    # Edit form
                    edited_base_url = st.text_input(
                        "Base URL",
                        value=st.session_state.settings["base_urls"][provider],
                        key=f"edit_base_url_{provider}"
                    )
                    edited_api_key = st.text_input(
                        "API Key",
                        value=st.session_state.settings["api_keys"][provider],
                        type="password",
                        key=f"edit_api_key_{provider}"
                    )
                    
                    # Display current model list and allow editing
                    current_models = "\n".join(st.session_state.settings["models"].get(provider, []))
                    edited_models = st.text_area(
                        "Models (one per line)",
                        value=current_models,
                        key=f"edit_models_{provider}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Changes", key=f"save_{provider}", use_container_width=True):
                            # Update settings
                            st.session_state.settings["base_urls"][provider] = edited_base_url
                            st.session_state.settings["api_keys"][provider] = edited_api_key
                            st.session_state.settings["models"][provider] = [
                                model.strip() for model in edited_models.split("\n") if model.strip()
                            ]
                            
                            # Save settings
                            save_settings()
                            st.success("Changes saved")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"Delete {provider}", key=f"delete_{provider}", use_container_width=True):
                            if provider in st.session_state.settings["base_urls"]:
                                del st.session_state.settings["base_urls"][provider]
                            if provider in st.session_state.settings["api_keys"]:
                                del st.session_state.settings["api_keys"][provider]
                            if provider in st.session_state.settings["models"]:
                                del st.session_state.settings["models"][provider]
                            
                            # Save settings
                            save_settings()
                            st.success(f"{provider} deleted")
                            st.rerun()


            # Change admin password
            st.subheader("Change Admin Password")
            new_admin_password = st.text_input("New Password", type="password")
            if st.button("Update Password"):
                if new_admin_password:
                    st.session_state.settings["admin_password"] = hashlib.sha256(new_admin_password.encode()).hexdigest()
                    save_settings()
                    st.success("Admin password updated")
                    st.session_state.is_admin = False
                    st.rerun()
                else:
                    st.error("New password cannot be empty")

# Main interface - Chat
st.title("Unified LLM Chat")

# Display current settings
current_provider = st.session_state.current_base_url
current_model = st.session_state.current_model

if current_provider and current_model:
    st.info(f"Currently using: {current_provider} - {current_model}")
else:
    st.warning("Please configure a provider and model in the sidebar first")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your question..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if valid settings exist
    if not st.session_state.current_base_url or not st.session_state.current_api_key or not st.session_state.current_model:
        with st.chat_message("assistant"):
            st.error("Please complete API settings in the sidebar first")
    else:
        # Show AI thinking
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Configure OpenAI client
                client = openai.OpenAI(
                    base_url=st.session_state.settings["base_urls"][st.session_state.current_base_url],
                    api_key=st.session_state.current_api_key
                )
                
                # Prepare complete message history
                messages = []
                for m in st.session_state.messages:
                    messages.append({"role": m["role"], "content": m["content"]})
                
                # Call API
                response = client.chat.completions.create(
                    model=st.session_state.current_model,
                    messages=messages,
                    stream=True
                )
                
                # Stream output
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                # Update final response
                message_placeholder.markdown(full_response)
                
                # Add AI reply to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_message = f"Error occurred: {str(e)}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Footer
st.markdown("---")
st.markdown("© 2025 Unified LLM Chat | Built with Streamlit and OpenAI protocol")
"""
Streamlit Conversational UI.

- https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps
"""

# template_st_chat_ui.py

# Authors: The scikit-plots developers
# SPDX-License-Identifier: BSD-3-Clause

# pylint: disable=import-error
# pylint: disable=unused-import
# pylint: disable=unused-argument
# pylint: disable=no-name-in-module
# pylint: disable=broad-exception-caught

import os
from typing import Optional

from scikitplot import logger
from scikitplot._compat.optional_deps import HAS_STREAMLIT, safe_import
from scikitplot.llm_provider import (
    LLM_MODEL_PROVIDER2CONFIG,  # noqa: F401
    chat_provider,
    get_env_st_secrets,
    load_mlflow_gateway_config,
    load_st_secrets,
    save_st_secrets,
)

if HAS_STREAMLIT:
    st = safe_import("streamlit")

    @st.cache_resource
    def cached_config(path: str) -> "dict[str, any]":
        """cached_config."""
        return load_mlflow_gateway_config(path)

    def api_key_config_ui(
        config_path: "Optional[str]" = None,
    ) -> "tuple[str, str, Optional[str]]":
        """
        Render the Streamlit UI for API key configuration.

        Parameters
        ----------
        config_path : Optional[str]
            Path to a YAML config file in MLflow Gateway format (if available).

        Returns
        -------
        Tuple[str, str, Optional[str]]
            Selected model provider, model ID, and API key (if entered).
        """
        # st.subheader("🔐 API Key Configuration")
        st.subheader("\U0001f511 API Key Configuration")

        if "llm_model_provider2config" not in st.session_state:
            # pylint: disable=global-statement
            # pylint: disable=global-variable-not-assigned
            global LLM_MODEL_PROVIDER2CONFIG  # noqa: PLW0602, PLW0603
            st.session_state.llm_model_provider2config = LLM_MODEL_PROVIDER2CONFIG

        config_path = (
            config_path
            or st.text_input(
                "Load from MLflow gateway config file:\n"
                "( ./galleries/gateway/openai/config.yaml )",
                value="",
                placeholder="./galleries/gateway/huggingface/config.yaml",
                disabled=False,
                # on_change=call_func,
            ).strip()
        )
        # Load from config file if provided
        if config_path:
            try:
                # conf = load_mlflow_gateway_config(config_path)
                conf = cached_config(config_path)
                st.session_state.llm_model_provider2config = conf
            except Exception as e:
                # Fallback defaults
                # st.warning("No model configurations available.")
                st.error(f"Failed to load config: {e}")
                logger.error(f"Failed to load config: {e}")
        else:
            st.session_state.llm_model_provider2config = LLM_MODEL_PROVIDER2CONFIG
        # Select provider
        model_provider = st.selectbox(
            label="Select Model Provider:",
            options=list(st.session_state.llm_model_provider2config.keys()),
            index=0,  # This default won't reapply if user changes selection
            help="Choose the model provider.",
        )
        # Store in Session
        st.session_state.model_provider = model_provider
        _suffix = "_TOKEN" if model_provider in ["huggingface"] else "_API_KEY"
        env_key = model_provider.upper() + _suffix
        # Select or input model ID
        model_options = [
            cfg["model_id"]
            for cfg in st.session_state.llm_model_provider2config[model_provider]
        ] + ["Custom..."]
        model_id = st.selectbox(
            label="Select or enter a model ID:",
            options=model_options,
            index=0,
            help="Choose a predefined model or enter a custom one.",
        )
        model_id = (
            st.text_input(
                label=f"Custom Model ID for {model_provider}",
                value="Model ID" if model_id != "Custom..." else "",
                key="custom_model_id",
                disabled=model_id != "Custom...",
            ).strip()
            if model_id == "Custom..."
            else model_id
        )
        # Store in Session
        st.session_state.model_id = model_id
        # API Key input
        # Mapping of model providers to tokens
        provider_tokens = {
            "openai": "sk-...",
            "huggingface": "hf_...",
            "cohere": "cohere-...",
            "anthropic": "anthropic-...",
        }
        api_key = st.text_input(
            f"Enter here {model_provider} API key\n"
            f"or set environment {env_key} inside "
            f"(e.g. .env or ~/.streamlit/secrets.toml ):",
            value="",
            type="password",
            placeholder=provider_tokens.get(model_provider),
            help="API key used to authenticate requests.",
        ).strip()
        # def valid_key_format(provider: str, key: str) -> bool:
        #     """valid_key_format."""
        #     return (
        #         (provider == "openai" and key.startswith("sk-")) or
        #         (provider == "huggingface" and key.startswith("hf_")) or
        #         (provider == "groq" and key.startswith("gsk_")) or
        #         (provider == "gemini" and key.startswith("gemini_")) or
        #         (provider == "anthropic" and key.startswith("sk-ant-")) or
        #         (provider == "cohere" and key.startswith("coh_"))
        #     )
        # api_key = api_key if api_key else None
        # Store in Session
        st.session_state["api_key"] = api_key
        if st.button(
            "Save API Key to '~/.streamlit/secrets.toml'",
            use_container_width=True,
        ):
            # if not api_key or len(api_key) < 10:
            #     st.warning("Please enter a valid API key.")
            # elif not valid_key_format(model_provider, api_key):
            #     st.warning(f"API key for {model_provider} must start with expected prefix.")
            # else:
            # product detection
            product = os.getenv("PRODUCT") or get_env_st_secrets("PRODUCT", None)
            if product == "product":
                # Load Update Save streamlit secrets
                secrets = load_st_secrets()
                secrets[env_key] = api_key
                save_st_secrets(secrets)
                st.success(f"{model_provider.capitalize()} API key saved as persisted!")
            else:
                # Show current key info (not the key itself)
                st.info(
                    f"Dev mode: {model_provider.capitalize()} API key keep only session!"
                )
        return model_provider, model_id, api_key

    def run_chat_ui():  # noqa: PLR0912
        """
        Render a simple chat interface using Streamlit with message history.

        Features:
        - Displays chat messages from session state.
        - Uses a bordered container to enclose chat history.
        - Input field stays at the bottom.
        - Echoes user input as a simulated assistant response.

        Session State Keys:
        - "messages": list of message dictionaries (role: 'user' or 'assistant', content: str)
        """
        # Placeholder
        with st.empty().container(border=True):
            # https://discuss.streamlit.io/t/how-to-right-justify-st-chat-message/46794/4
            st.markdown(
                """
            <style>
                .st-emotion-cache-janbn0 {
                    flex-direction: row-reverse;
                    text-align: right;
                }
            </style>
            """,
                unsafe_allow_html=True,
            )
            # Initialize chat history, append input + response to session state
            if "show_history" not in st.session_state:
                st.session_state.show_history = False
            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "model_provider" not in st.session_state:
                st.session_state.model_provider = "huggingface"
            if "model_id" not in st.session_state:
                st.session_state.model_id = None
            if "api_key" not in st.session_state:
                st.session_state.api_key = None
            # Initialize the flag in session state
            if "running" not in st.session_state:
                st.session_state["running"] = False

            # Sidebar for controlling expanders and categories
            with st.sidebar:
                api_key_config_ui()

            # with st.expander("💬 Assistant Chat"):
            # st.title("💬 ChatBot")
            st.subheader("💬 Assistant Chat")

            st.write(f"Selected model_type: {st.session_state.model_provider}")
            st.write(f"Selected model_id: {st.session_state.model_id}")

            # Placeholder
            chat_history_placeholder = st.empty().container()
            # Placeholder
            chat_messages_placeholder = st.empty().container(border=True)
            # Placeholder
            chat_btn_placeholder = st.empty().container()
            # Placeholder
            chat_btn_togg_placeholder = st.empty().container()

            # Fill Placeholders logically
            with chat_btn_togg_placeholder:
                # To place two buttons side-by-side (in the same horizontal row) in Streamlit
                col1, col2 = st.columns(2)
                with col1:
                    # Button Toggle ChatBot History
                    if st.button(
                        "Toggle ChatBot History",
                        icon=":material/expansion_panels:",
                        use_container_width=True,
                        # disabled button (Streamlit 1.22+ supports disabled param)
                        disabled=st.session_state["running"],
                    ):
                        st.session_state.show_history = not st.session_state.get(
                            "show_history", True
                        )
                with col2:
                    # Button Toggle ChatBot History
                    if st.button(
                        "Clear ChatBot History",
                        icon=":material/delete:",
                        use_container_width=True,
                        # disabled button (Streamlit 1.22+ supports disabled param)
                        disabled=st.session_state["running"],
                    ):
                        st.session_state.messages = []
            with chat_btn_placeholder:
                # React to user input
                # prompt := st.chat_input("What is up?")
                if prompt := st.chat_input(
                    "Ask Assistant: say something and/or attach an image",
                    accept_file=True,
                    file_type=["jpg", "jpeg", "png"],
                ):
                    st.session_state["running"] = True
                    if prompt and prompt.text:
                        query = prompt.text.strip()
                        # Add user message to chat history
                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": query,
                                "type": "text",
                            }
                        )
                        # Replace this with your assistant logic
                        # response = f"Echo: {query}"
                        # Sens user's message to the LLM and get a response
                        # messages = [
                        #     {"role": "system", "content": "You are a helpful assistant"},
                        #     *st.session_state.messages ? tokenize
                        # ]
                        # assitant_response = client.chat.completions.create(
                        #     model = st.session_state["groqai_model"],
                        #     messages = messages
                        # )
                        # response = assitant_response.choices[0].message.content
                        # logger.info(response)
                        response = chat_provider.get_response(
                            st.session_state.messages,
                            model_provider=st.session_state.model_provider,
                            model_id=st.session_state.model_id,
                            api_key=st.session_state.api_key,
                        )
                        # Add assistant response to chat history
                        # Display assistant response in chat message container
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response,
                                "type": "text",
                            }
                        )
                    elif prompt and prompt["files"]:
                        query = prompt["files"][0]
                        # Replace this with your assistant logic
                        response = query
                        # Add user message to chat history
                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": query,
                                "type": "image",
                            }
                        )
                        # Add assistant response to chat history
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": response,
                                "type": "image",
                            }
                        )
                    st.session_state["running"] = False
            with chat_history_placeholder:
                if st.session_state.get("show_history", True):
                    st.write("History is visible.")
                    with st.expander("ChatBot History", expanded=True):
                        # Display bordered chat container messages from history on app rerun
                        for message in st.session_state.messages:  # loop Q&A
                            # Display user message in chat message container
                            # Display assistant response in chat message container
                            # method 2
                            # st.chat_message("user").markdown(prompt)  # short form
                            # st.chat_message("user").image(query)  # short form
                            # method 1
                            with st.chat_message(message["role"]):
                                if message["type"] == "text":
                                    st.markdown(message["content"])
                                elif message["type"] == "image":
                                    st.image(message["content"])
                else:
                    pass
            with chat_messages_placeholder:
                if len(st.session_state.messages) >= 2:  # noqa: PLR2004
                    for message in st.session_state.messages[-2:]:  # loop Q&A
                        # Display user message in chat message container
                        # Display assistant response in chat message container
                        # st.chat_message("user").markdown(prompt)  # short form
                        # st.chat_message("user").image(query)  # short form
                        with st.chat_message(message["role"]):
                            if message["type"] == "text":
                                st.markdown(message["content"])
                            elif message["type"] == "image":
                                st.image(message["content"])
                else:
                    pass

    # ---------------------- Entrypoint ----------------------

    if __name__ == "__main__":
        run_chat_ui()

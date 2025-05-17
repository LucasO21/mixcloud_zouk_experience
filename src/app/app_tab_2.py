# ==============================================================================
# STREAMLIT TAB 2 - AI RECOMMENDATIONS ----
# ==============================================================================

# ------------------------------------------------------------------------------
# SETUP ----
# ------------------------------------------------------------------------------

# Import Libraries ----
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

import streamlit as st
import random
import yaml
import uuid
import os
import sys
from pathlib import Path

# Initialize session state for carrying clicked prompt text across rerun
if "example_prompt_value" not in st.session_state:
    st.session_state.example_prompt_value = None

# Paths ----
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# from utilities.rag_utilities import get_rag_model

# Env Variables ----
OPENAI_API_KEY = yaml.safe_load(open("credentials.yml"))['openai']
RAG_DATABASE = os.path.join(project_root, 'data', 'dev', 'chroma_db')

# ------------------------------------------------------------------------------
# STREAMLIT APP
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title            = "Your AI Zouk Music Assistant",
    page_icon             = "🎧🤖",
    layout                = "centered"
)

# Message History ----
msgs = StreamlitChatMessageHistory(key = "langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message(" Hi! 👋 What are you in the mood for today?")

view_messages = st.expander("View the message contents in session state")


def get_rag_chain(
    vectorstore_path = RAG_DATABASE,
    model            = 'gpt-4o-mini',
    temperature      = 0.7,
    openai_api_key   = OPENAI_API_KEY,

):

    # - embedding ----
    embedding_function = OpenAIEmbeddings(
        model   = 'text-embedding-ada-002',
        api_key = openai_api_key
    )

    #  - vectorestore ----
    vectorstore = Chroma(
        persist_directory  = vectorstore_path,
        embedding_function = embedding_function,
    )

    #  - retriever ----
    retriever = vectorstore.as_retriever()

    # - llm ----
    llm = ChatOpenAI(
        model       = model,
        temperature = temperature,
        api_key     = openai_api_key,
    )

    # - rag chain ----

    # - contextualize question ----
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    # -- answer question based on chat history ----
    qa_system_prompt = """

        You are a music recommendation assistant helping users discover DJ sets based on their mood, energy, and genre preferences.

        Zouk is a family of dance music genres originating in the Caribbean (notably Guadeloupe and Martinique) and popularized
        globally through Brazilian and African interpretations.

        There are multiple substyles and fusion genres within Zouk music:

        - Traditional Zouk (Caribbean Zouk): Upbeat, percussion-driven, and rooted in Creole rhythms. Often features live
        instruments and a carnival feel.
        - Brazilian Zouk: A slower, smoother evolution adapted for partner dancing. Known for its sensual flow, deep bass, and melodic remixes.
        - Zouk Lambada: A style blending Brazilian Zouk and Lambada rhythms. Often more dynamic and rhythmically complex.
        - Ghetto Zouk: A minimal, electronic-influenced version with R&B, Kizomba, or Afrobeat elements. Often more sensual and groove-based.
        - Zouk Remixes & DJ Edits: Many DJs remix R&B, Lo-fi, Afrobeat, or Pop tracks into Zouk rhythm structures to create fresh dance experiences
        - Zouk sets can range from slow and intimate to high-energy and festival-style, and may feature crossover genres like Afrobeat,
          Chillout, Deephouse, Groovy, R&B, EDM, and live blends. Vibe and energy arcs are often as important as genre when selecting a Zouk set.

        Your goal is not just to recommend sets, but to help the user discover what they’re truly in the mood for, even if they aren’t sure yet.

        Instructions:

        - If the user’s query is vague or mood-based (e.g. “I want something chill”), start by asking a **clarifying question** before
        making recommendations. For example:
            - “Are you interested in chill Zouk specifically, or are you open to R&B or Lo-fi as well?”
            - “Would you prefer something that builds energy or stays smooth throughout?”
        - Be sure to give reasons why you are suggesting each set.
        - Only make recommendations once you feel you have enough clarity on what they’re looking for.
        - Use a friendly, conversational tone. Make the user feel like they’re chatting with a helpful DJ friend.
        - Answer based only on the context provided below.
        - If multiple sets match, suggest 1–3 and explain why.
        - If no match is found, say so clearly and suggest trying different keywords.
        - Use a friendly and concise tone.
        - Provide the DJ name, title, and a link to the set.
        - Provide information on the dj.
        - Avoid using the word “I” to keep the tone professional yet warm.
        - Include brief information about the DJ and the set
        - When you see the word "Vibe", it's just another word for Genre.
        - When you see the word "Tempo" is just another word for BPM.
        - Feel free to summarize or reword descriptions for clarity, but do not invent details.
        - Do not ask if the user questions like "are you in the mood for Zouk or something else?". All the sets are Zouk. Zouk is just
          the name of the music and dance but the music incorporates many genres like R&B, Afrobeat, and more.

        - If no matching sets are found:
            - Say so clearly and suggest trying different keywords or moods.

        See example responses below. Use this output format once you have enough context to make a recommendation:

        Example 1:
        It seems like you're looking for a DJ set with a "Chill" vibe. Just to clarify — are you interested
        in chill Zouk sets specifically, or are you open to other genres like Lo-fi, R&B, or Downtempo EDM as well?

        Here are some sets that match your query based on what's available:

        🎧 Recommendations:
        "Beaking with Tradition - DJ Sprenk"
        Listen to the set here: [DJ Sprenk - Beaking with Tradition](https://www.mixcloud.com/djsprenk/beaking-with-tradition/)

        Information on Set:
        This set was played as the closing set on Friday night at Zouk Heat 2025. The set features chapters including.
        Date Uploaded: 2 days ago.
        Genres/Vibe: Feel Good R&B, Traditional, Trancey and lots more.
        Artists Featured: N.E.D, Sabrina Claudio, Chris Brown, Davido, and lots more.
        Play Count: 133.
        Favorite Count: 7.

        More on DJ Sprenk:
        DJ Sprenk is a brazilian zouk dj based in Cambridge, MA. He's style incorporates, smooth transitions,
        chill remixes, and a touch of afrobeats. You can find him djing on Wednesday nights at the Cambridge Zouk social.

        Example 2:
        It sounds like you're looking for something chill. Just to clarify — are you specifically in
        the mood for Zouk with a laid-back groove, or are you also open to mixes that incorporate R&B and Afrobeat influences?

        Here’s a set I think you’ll enjoy:

        🎧 Recommendations:

        "Icing the Fire" by DJ WarHoll
        🎧 Listen on Mixcloud
        Information on Set:

        Where it was played: Friday night chill room at Zouk Heat 2025
        Set vibe: Designed to create space for dancers to relax and move freely without pressure
        Genres included: Zouk, Brazilian Zouk, R&B, Afrobeat
        Artists featured: YDDE ADZ, Chris Brown, DJ LOV3, Ya Levis, Oxlade
        Play count: 164
        Favorite count: 18
        More on DJ WarHoll:

        DJ WarHoll is a Zouk and Kizomba DJ from Richmond, VA. Known for his groovy and emotionally expressive sets,
        he brings immaculate vibes whether he's opening or closing a night.

        It sounds like you're in the mood for something with groove and progression. Just to clarify — are you
        looking for sets that start chill and gradually build energy, or something that stays consistently smooth throughout?

        If you enjoy dynamic energy arcs within the same vibe family, DJ WarHoll has two standout sets worth exploring.

        Example 3:
        🎧 Recommendations:

        "Grace Thru Fire" by DJ WarHoll
        "In The Air Tonight" by DJ WarHoll
        🎧 Listen here:

        Grace Thru Fire (Sunday Day Party)
        In The Air Tonight (Saturday Night Closer)
        Information on Set – "Grace Thru Fire":

        Where it was played: RVAZM Weekender Hybrid 2025, Sunday Day Party
        Set vibe: Slow and intentional start with a powerful peak mid-set
        Genres included: Zouk, Brazilian Zouk, Afrobeat, Moombahton, Kizomba
        Artists featured: DJ Kakah, DJ Vini, Will Gittens, Max Blacksoul, Lana Del Rey (remix)
        Play count: 124
        Favorite count: 4
        Information on Set – "In The Air Tonight":

        Where it was played: Saturday night closer at the same event
        Set vibe: A chill but engaging late-night session designed to keep dancers moving until 3am
        Genres included: Zouk, Brazilian Zouk, Kizomba, Chillout, Acoustic
        Artists featured: Nelson Freitas, Kim Tavares, Ana Mancebo, Drea Dury, Malcom Beatz
        Play count: 88
        Favorite count: 2

        More on DJ WarHoll:
        DJ WarHoll is a Zouk/Kizomba DJ based in Richmond, VA. His sets are known for their
        emotional range, often moving between groove, softness, and surprise peaks. His mixes are particularly
        great for dancers who appreciate intention behind musical storytelling — and yes, the vibes are indeed immaculate.

        {context}
    """

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # - combine both RAG + chat message history
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return RunnableWithMessageHistory(
        rag_chain,
        lambda session_id: msgs,
        input_messages_key   = "input",
        history_messages_key = "chat_history",
        output_messages_key  = "answer",
    )

rag_chain = get_rag_chain(OPENAI_API_KEY)

# Add Title
# Add "back to welcome" button
if st.button("← Back to Welcome", key="back_from_preference"):
    st.session_state.active_tab = None
    st.rerun()

st.title("🎧🤖 AI Zouk Music Assistant")
st.write("---")

# Example Prompts
# st.subheader("Try an Example Prompt")
st.info("Click any button below to try an example prompt. You can also type your own question in the chat box.")
# prompt1_text = "Find me some chill Zouk sets for a relaxed evening."
# prompt2_text = "Recommend upbeat Zouk tracks with Afrobeat influences."
# prompt3_text = "What are some popular Zouk sets from recent festivals?"

# cols = st.columns(3)
# if cols[0].button(prompt1_text, key="prompt1_btn", use_container_width=True):
#     st.session_state.example_prompt_value = prompt1_text
#     st.rerun()
# if cols[1].button(prompt2_text, key="prompt2_btn", use_container_width=True):
#     st.session_state.example_prompt_value = prompt2_text
#     st.rerun()
# if cols[2].button(prompt3_text, key="prompt3_btn", use_container_width=True):
#     st.session_state.example_prompt_value = prompt3_text
#     st.rerun()
# st.markdown("---") # Separator
# --- All available prompts ---
all_prompts = [
    "Find me some chill Zouk sets for a relaxed evening.",
    "Recommend upbeat Zouk tracks with Afrobeat influences.",
    "What are some popular Zouk sets from recent festivals?",
    "I’m in the mood for slow, emotional Zouk remixes. Got any suggestions?",
    "Show me some DJ sets that blend R&B and Brazilian Zouk.",
    "Looking for high-energy sets to open a party. Any recommendations?",
    "Suggest Zouk sets with live instruments or world music elements.",
    "Find DJ sets with strong energy arcs, building from slow to high BPM.",
    "Which sets are great for partner dancing on a Sunday night?"
]

# --- Pick 3 random prompts on load ---
if "prompt_choices" not in st.session_state:
    st.session_state.prompt_choices = random.sample(all_prompts, 3)

# --- Display buttons ---
cols = st.columns(3)
for i, prompt_text in enumerate(st.session_state.prompt_choices):
    if cols[i].button(prompt_text, key=f"prompt_btn_{i}", use_container_width=True):
        st.session_state.example_prompt_value = prompt_text
        st.rerun()

# Render Current Messages From StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# Determine the query to process
query_to_process = None

if st.session_state.get("example_prompt_value"): # Check if a button was clicked
    query_to_process = st.session_state.example_prompt_value
    st.session_state.example_prompt_value = None  # Consume the value, so it's not reused on next rerun without new click

# Then, check the actual chat input field
# Changed placeholder text for chat_input to be more specific
chat_input_val = st.chat_input("Ask about Zouk music recommendations...", key="query_input")
if chat_input_val:
    query_to_process = chat_input_val # chat_input takes precedence if user types after clicking example

# If there's a query from either source, process it
if query_to_process:
    st.chat_message("human").write(query_to_process)
    # Note: The RAG chain with RunnableWithMessageHistory is expected to handle
    # adding the human message to the history (msgs).

    with st.spinner("Thinking..."):
        response = rag_chain.invoke(
            {"input": query_to_process},
            config={"configurable": {"session_id": "any"}}, # session_id="any" is from original code
        )
        # The AI response is also expected to be added to history by the chain.
        # Explicitly writing it to the chat UI is consistent with original code.
        st.chat_message("ai").write(response['answer'])

# View Messages for Debugging ----
# Draw the messages at the end, so newly generated ones show up immediately
# with view_messages:
#     """
#     Message History initialized with:
#     ```python
#     msgs = StreamlitChatMessageHistory(key="langchain_messages")
#     ```

#     Contents of `st.session_state.langchain_messages`:
#     """
#     view_messages.json(st.session_state.langchain_messages)



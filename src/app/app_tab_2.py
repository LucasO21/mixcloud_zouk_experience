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
import yaml
import uuid
import os
import sys
from pathlib import Path

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
    page_title            = "AI Zouk Music Assistant",
    page_icon             = "🎧🤖",
    layout                = "centered"
)

# Message History ----
msgs = StreamlitChatMessageHistory(key = "langchain_messages")
if len(msgs.messages) == 0:
    msgs.add_ai_message("How can I help you?")

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

        You are a music recommendation assistant helping users discover DJ sets based on mood and genre.

        Instructions:
        - Answer based only on the context provided below.
        - If multiple sets match, suggest 1–3 and explain why.
        - If no match is found, say so clearly and suggest trying different keywords.
        - Use a friendly and concise tone.
        - Provide the DJ name, title, and a link to the set.
        - Avoid using the word "I" in your response.
        - Include brief information about the DJ and the set

        See example responses below:

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

# Render Current Messages From StreamlitChatMessageHistory
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if question := st.chat_input("Enter your automation question here:", key="query_input"):
    with st.spinner("Thinking..."):
        st.chat_message("human").write(question)

        response = rag_chain.invoke(
            {"input": question},
            config={
                "configurable": {"session_id": "any"}
            },
        )
        # Debug response
        # print(response)
        # print("\n")

        st.chat_message("ai").write(response['answer'])

# View Messages for Debugging ----
# Draw the messages at the end, so newly generated ones show up immediately
with view_messages:
    """
    Message History initialized with:
    ```python
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    ```

    Contents of `st.session_state.langchain_messages`:
    """
    view_messages.json(st.session_state.langchain_messages)



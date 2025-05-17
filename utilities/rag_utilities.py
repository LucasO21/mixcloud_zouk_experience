
# Imports ----
import pandas as pd
import os

from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# Rag Documents ----
def get_rag_document(data):
    """
    Create a Document object from a row of the DataFrame.
    """
    sets_dict = data.to_dict(orient = 'records')

    documents = []

    for item in sets_dict:
        content = f"""
        dj_name: {item.get('dj_name')},
        dj_bio: {item.get('dj_info')},
        df_followers: {item.get('dj_followers')},
        df_following: {item.get('dj_following')},
        title: {item.get('show_title')},
        play_count: {item.get('play_count')},
        favorited_count: {item.get('fav_count')},
        date_uploaded: {item.get('date_uploaded')},
        genre_tags: {item.get('show_tags_cleaned')},
        energy_min: {item.get('energy_min')},
        energy_max: {item.get('energy_max')},
        bpm_min: {item.get('bpm_min')},
        bpm_max: {item.get('bpm_max')},
        artists_list: {item.get('artists_list')},
        show_info_combined: {item.get('show_info_combined')},
        show_url: {item.get('show_url')},
        """

        doc = Document(page_content = content, metadata = item)

        documents.append(doc)

    return documents


# Rag Model ----
def get_rag_model(
    vectorstore_path = os.path.join(DATA_DIR, 'chroma_db'),
    model = 'gpt-4o-mini',
    temperature = 0,
    openai_api_key = None,
    # documents = None,
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

    # - rag chain ----
    template = """

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

        Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI(
        model       = model,
        temperature = temperature,
        api_key     = openai_api_key,
    )

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    return rag_chain
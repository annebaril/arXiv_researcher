import os
import sys

import chromadb
from loguru import logger
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, concat_ws, lower, regexp_replace, trim, row_number
from pyspark.sql.functions import col
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def load_json_to_dataframe(json_file, spark):
    """
    Load a JSON file into a Spark DataFrame.
    
    :param json_file: Path to the JSON file
    :return: Spark DataFrame
    """
    df = spark.read.json(json_file)
    return df

def clean_dataframe(df):
    """
    Clean the DataFrame by removing empty rows, combine title and abstract and get first year of publication.
    
    :param df: Input DataFrame
    :return: Cleaned DataFrame
    """
    logger.info("Cleaning DataFrame")
    logger.info("Generate new columns")
    

    df_cleaned = df.select(
        "id", "title", "abstract", "versions", "authors"
    ).withColumn(
        "document",
        concat_ws(" ", col("title"), col("abstract"))
    ).withColumn(
        "document",
        lower(regexp_replace(col("document"), r"[^a-zA-Z0-9\s]", ""))
    ).withColumn(
        "document", trim(col("document"))
    ).withColumn(
        "year", col("versions")[0]["created"].substr(-17, 4)
    )

    df_window = Window.orderBy(col("year"))
    df_cleaned = df_cleaned.withColumn("row_id", row_number().over(df_window))
    
    # Filter out empty documents
    logger.info("Filtering empty documents")
    df_cleaned = df_cleaned.filter(col("document") != "")
    return df_cleaned

def embed_documents(pandas_df, vectorstore):
    """
    Embed the documents in the DataFrame using the specified embeddings model.
    
    :param df: Pandas DataFrame
    :param embeddings: Embeddings model
    :param db_path: Path to the database
    :param vectorstore: Optional existing vectorstore
    :return: Choma vectorstore
    """
    metadata = [{"id": row["id"], "year": row["year"], "title": row["title"], "authors": row["authors"]} for _, row in pandas_df.iterrows()]

    # Add new documents to the existing vectorstore
    logger.info(f"Vectorstore already exists, Add new documents to the existing vectorstore")
    vectorstore.add_texts(texts=pandas_df['document'].tolist(), metadatas=metadata, ids=pandas_df['id'].tolist())

    return vectorstore

def convert_part(df, part, number_line, vectorstore):
    """
    Convert a part of the DataFrame to a Pandas DataFrame and embed the documents.
    
    :param df: Input DataFrame
    :param part: Part number
    :param number_line: Number of lines per part
    :return: None
    """
    
    start = part * number_line
    # Convert to Pandas DataFrame
    logger.info(f"Converting Spark DataFrame to Pandas DataFrame")
    pandas_df = df.select("id", "document", "year", "title", "authors").filter(col("row_id") >= start).limit(number_line).toPandas()

    logger.info(f"{pandas_df.shape[0]} line will be embedding")
    
    return embed_documents(pandas_df, vectorstore)


def main():
    JSON_NAME = 'arxiv-metadata-oai-snapshot.json'
    MODEL_NAME = 'sentence-transformers/all-mpnet-base-v2'
    persist_directory = '/index_data'
    chroma_ip = '34.163.106.5'
    chroma_port = 8000

    current_dir = "gs://arxiv-researcher-data-source"
    json_path = os.path.join(current_dir, JSON_NAME)
    line_per_part = 500

    # Embed the documents
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    chroma_client = chromadb.HttpClient(host=chroma_ip, port=chroma_port)
    
    try:
        heartbeat = chroma_client.heartbeat()
        logger.info(f"heartbeat du client est de: {heartbeat}")
    except:
        raise FileNotFoundError(
            f"Le serveur est down."
        )

    vectorstore = Chroma(persist_directory=persist_directory, client=chroma_client, embedding_function=embeddings)

    spark = SparkSession.builder \
        .appName("Load JSON") \
        .getOrCreate()

    # Load the JSON file into a DataFrame
    logger.info(f"Loading JSON file: {JSON_NAME}")
    df = load_json_to_dataframe(json_path, spark)

    # Clean the DataFrame
    df_cleaned = clean_dataframe(df)

    if len(sys.argv) == 2:
        logger.info(f"Argument provided, using value: {sys.argv[1]}")
        number_part = sys.argv[1]
        convert_part(df_cleaned, int(number_part), line_per_part, vectorstore)
    elif len(sys.argv) > 2:
        raise(TypeError)
    else:
        logger.info(f"No argument provided, use all the data")
        
        nbr_line_dataframe = df_cleaned.count()
        number_part = nbr_line_dataframe // line_per_part
        if nbr_line_dataframe % line_per_part != 0:
            number_part += 1
        logger.info(f"{number_part} parts identify")

        for i in range(0, number_part):
            logger.info(f"Part n°{i}")
            vectorstore = convert_part(df_cleaned, i, line_per_part, vectorstore)
    logger.info(f"End")

if __name__ == "__main__":
    main()
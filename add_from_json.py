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
    ENV_DB = os.getenv("ENV_DB", "GCP")
    JSON_NAME = os.getenv("DATA_START_JSON_NAME")
    CHROMADB_HOST = os.getenv("CHROMADB_HOST")
    CHROMADB_PORT = os.getenv("CHROMADB_PORT", 8000)
    MODEL_NAME = os.getenv("EMBEDDING_MODEL")
    PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", "/index_data")
    line_per_part = 500

    # Embed the documents
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

    #If ENV_DB == GCP, the json file is in GSP BUCKET. Else, is in local
    if ENV_DB == "GCP":
        current_dir = os.getenv("DATA_START_JSON_GCP")
        chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
        
        try:
            heartbeat = chroma_client.heartbeat()
            logger.info(f"heartbeat du client est de: {heartbeat}")
        except:
            raise FileNotFoundError(
                f"Le serveur est down."
            )
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dir = os.getenv("PATH_DATA_START_JSON", "data/chromadb")
        current_dir = os.path.join(current_dir, dir)
        chroma_client = None

    json_path = os.path.join(current_dir, JSON_NAME)
    vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, client=chroma_client, embedding_function=embeddings)

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
    elif len(sys.argv) > 3:
        raise(TypeError)
    else:
        if len(sys.argv) == 3:
            logger.info(f"Argument provided, using value: {sys.argv[1]} and {sys.argv[2]}")
            start_part = int(sys.argv[1])
            last_part = int(sys.argv[2])
        else:
            logger.info(f"No argument provided, use all the data")
            start_part = 0
            nbr_line_dataframe = df_cleaned.count()
            last_part = nbr_line_dataframe // line_per_part
            if nbr_line_dataframe % line_per_part != 0:
                last_part += 1
            logger.info(f"{last_part} parts identify")

        for i in range(start_part, last_part):
            logger.info(f"Part n°{i}")
            vectorstore = convert_part(df_cleaned, i, line_per_part, vectorstore)
    logger.info(f"End")

if __name__ == "__main__":
    main()
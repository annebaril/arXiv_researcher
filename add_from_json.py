import os
import sys

from loguru import logger
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, lower, regexp_replace, trim
from pyspark.sql.functions import monotonically_increasing_id, col

import pandas as pd
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
        "id", "title", "abstract", "categories", "versions"
    ).withColumn(
        "document",
        concat_ws(" ", col("title"), col("abstract"))
    ).withColumn(
        "document",
        lower(regexp_replace(col("document"), r"[^a-zA-Z0-9\s]", ""))
    ).withColumn(
        "document", trim(col("document"))
    ).withColumn(
        "row_id", monotonically_increasing_id()
    ).withColumn(
        "year", col("versions")[0]["created"].substr(-17, 4)
    )

    # Filter out empty documents
    logger.info("Filtering empty documents")
    df_cleaned = df_cleaned.filter(col("document") != "")
    return df_cleaned


def embed_documents(pandas_df, embeddings, db_path, vectorstore=None):
    """
    Embed the documents in the DataFrame using the specified embeddings model.
    
    :param df: Pandas DataFrame
    :param embeddings: Embeddings model
    :param db_path: Path to the database
    :param vectorstore: Optional existing vectorstore
    :return: Choma vectorstore
    """
    metadata = [{"id": row["id"], "year": row["year"]} for _, row in pandas_df.iterrows()]


    # Check if the vectorstore already exists
    if vectorstore is None:
        logger.info(f"Vectorstore not exists, initiate a vectorstore with the data")

        vectorstore = Chroma.from_texts(pandas_df['document'].tolist(), embedding=embeddings, metadatas = metadata, ids=pandas_df['id'].tolist() ,persist_directory=db_path)
    else:
        # Add new documents to the existing vectorstore
        logger.info(f"Vectorstore already exists, Add new documents to the existing vectorstore")
        vectorstore.add_texts(texts=pandas_df['document'].tolist(), metadatas=metadata, ids=pandas_df['id'].tolist())

    return vectorstore

def convert_part(df, part, number_line, db_path, vectorstore):
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
    pandas_df = df.select("id", "document", "year").filter(col("row_id") >= start).limit(number_line).toPandas()

    logger.info(f"{pandas_df.shape[0]} line will be embedding")
    # Embed the documents
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    embed_documents(pandas_df, embeddings, db_path, vectorstore)


def main():
    json_name = 'arxiv-metadata-oai-snapshot.json'
    db_name = 'chroma_new_db'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "data", json_name)
    persistent_dir = os.path.join(current_dir, "db", db_name)
    line_per_part = 5000

    # Ensure the json file exists
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"File {json_path} does not exist."
        )

    spark = SparkSession.builder \
        .appName("Load JSON") \
        .getOrCreate()

    # Load the JSON file into a DataFrame
    logger.info(f"Loading JSON file: {json_name}")
    df = load_json_to_dataframe(json_path, spark)

    # Clean the DataFrame
    df_cleaned = clean_dataframe(df)

    # Check if the vectorstore already exists
    if not os.path.exists(persistent_dir):
        vectorstore = None
    else:
        vectorstore = Chroma(persist_directory=persistent_dir)

    if len(sys.argv) == 2:
        logger.info(f"Argument provided, using value: {sys.argv[1]}")
        number_part = sys.argv[1]
        convert_part(df_cleaned, int(number_part), line_per_part, persistent_dir, vectorstore)
    elif len(sys.argv) > 2:
        raise(TypeError)
    else:
        logger.info(f"No argument provided, use all the data")
        
        nbr_line_dataframe = df_cleaned.count()
        number_part = nbr_line_dataframe // line_per_part
        if nbr_line_dataframe % line_per_part != 0:
            number_part += 1
        logger.info(f"{number_part} parts identify")
        
        vectorstore = None
        for i in range(0, number_part):
            logger.info(f"Part n°{i}")
            vectorstore = convert_part(df_cleaned, i, line_per_part, persistent_dir, vectorstore)

if __name__ == "__main__":
    main()
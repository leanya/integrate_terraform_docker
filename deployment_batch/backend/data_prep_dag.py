from bs4 import BeautifulSoup
import pandas as pd
import requests
import nltk
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from sqlalchemy import create_engine
import sqlalchemy


def scrape_headline_dataset(url):
    # url = "https://www.bbc.com/news"

    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')

    headlines = soup.find_all("h2")

    head_list = []
    for x in headlines:
        head_list.append(x.text.strip())
    df = pd.DataFrame({'headline':head_list})
    
    return df 

def data_cleaning(df):

    # Remove duplicates
    df_clean = df.copy()
    df_clean = df_clean.drop_duplicates()

    # Drop non-headline datasets
    df_clean["count_words"] = df_clean["headline"].str.split().str.len()
    df_clean = df_clean[df_clean["count_words"]> 3]
    df_clean = df_clean.drop(columns = "count_words")

    # Data Cleaning to extract common keywords

    # Download nltk packages 
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    
    # Word Tokenize
    df_clean["tokens"] = df_clean["headline"].apply(word_tokenize)

    # Extract Nouns and Verbs
    df_clean["tokens"] = df_clean["tokens"].apply(lambda x: 
                                                  [word for (word, pos) in pos_tag(x) if pos in 
                                                   ["NN", "NNS", "NNP", "NNPS", 
                                                    'VB', 'VBG', 'VBD', 'VBN']])
    
    # Add etl date information
    df_clean["etl_date"] = pd.to_datetime('today')
    df_clean["etl_date"] = df_clean["etl_date"].dt.normalize()

    return df_clean

def write_postgres(df):

    # Specify the data types of the columns 
    dtypes = {
        'headline' : sqlalchemy.types.TEXT(),
        'tokens' : sqlalchemy.types.ARRAY(sqlalchemy.types.TEXT()),
        'etl_date' : sqlalchemy.types.DateTime() 
    }

    # Connect and write to postgresql docker 
    engine = create_engine('postgresql+psycopg2://postgres:postgres@db_postgres:5432/postgres')
    df.to_sql(name = "bbc", 
              con = engine, 
              index = False,
              dtype = dtypes,
              if_exists = "append")
    
    # Close the connection 
    engine.dispose()

def main():
    url = "https://www.bbc.com/news"
    df = scrape_headline_dataset(url)
    df_clean = data_cleaning(df)
    write_postgres(df_clean)

if __name__ == '__main__':
    main()
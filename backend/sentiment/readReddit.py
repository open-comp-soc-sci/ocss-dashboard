import json
import pandas as pd
import requests
import io
import pyarrow as pa
from roberta import run_roberta_analysis

def load_dataframe(meta):
    # Get API parameters from meta
    subreddit = meta["subreddit"]
    option = meta["option"]
    startDate = meta.get("startDate", "")
    endDate = meta.get("endDate", "")
    # Build the API URL and append date parameters if provided.
    print('fetching from clickhouse')

    api_url = f"https://sunshine.cise.ufl.edu:5000/api/get_arrow?subreddit={subreddit}&option={option}"
    if startDate:
        api_url += f"&startDate={startDate}"
    if endDate:
        api_url += f"&endDate={endDate}"
    try:
        response = requests.get(api_url, verify=False)
        response.raise_for_status()
        # Read the binary Arrow stream.
        buffer = io.BytesIO(response.content)
        reader = pa.ipc.open_stream(buffer)
        table = reader.read_all()

        # Optionally, convert the Arrow Table to a pandas DataFrame if needed.
        df = table.to_pandas()
        # Print the first 5 records from the "data" key.
        # print(data["data"][0:5])
        # Iterate over the actual records list.
        # for record in data["data"]:
            # print(record[-1])

    except Exception as e:
        raise Exception(f"Error fetching data from API: {e}")

    print('done fetching from clickhouse')
    
    df = df.rename(columns={"selftext": "body"})
    df = df.fillna("")
    return df

def preproccess_termed_sentiment_data(df, groups):
    all_group_terms = []  # List of term lists
    all_sectioned_bodies = []

    for group in groups:
        for topic in group["topics"]:
            keywords = topic["ctfidfKeywords"]
            terms = [kw.strip() for kw in keywords.split(",")]
            all_group_terms.append(terms)

            # Filter posts by keywords
            term_bodies = {term: [] for term in terms}
            for body in df["body"]:
                lower_body = body.lower()
                for term in terms:
                    if term in lower_body:
                        term_bodies[term].append(body)

            sectioned_bodies = [term_bodies[term] for term in terms]
            all_sectioned_bodies.append((terms, sectioned_bodies))
    return all_sectioned_bodies

def main():
    # Load grouping results (which were already written by the consumer)
    with open("grouping_results.json", "r") as f:
        grouping_data = json.load(f)

    meta = grouping_data["meta"]
    groups = grouping_data["groups"]

    # Load the data from an external API and convert to DataFrame
    df = load_dataframe(meta)
    # Preprocess the data to group texts by keywords
    all_sectioned_bodies = preproccess_sentiment_data(df, groups)

    # For each group of texts, run sentiment analysis using the RoBERTa pipeline
    for terms, sectioned_bodies in all_sectioned_bodies:
        stats = run_roberta_analysis(terms, sectioned_bodies)
        print(stats)

if __name__ == '__main__':
    main()

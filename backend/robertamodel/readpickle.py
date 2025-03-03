import pickle
import pandas as pd

with open('backend/robertamodel/full_db.pickle', "rb") as file:
    df = pd.read_pickle(file)

terms = ["mvd", "nerve pain", "opioids", "pregabalin", 
         "carbamazepine", "carbamazapine", "oxcarbazepine", "oxcarbazapine"]

df = df.fillna("")

# Initialize a dictionary where each term maps to an empty list
term_bodies = {term: [] for term in terms}

# Iterate through each body in the DataFrame
for body in df["body"]:
    lower_body = body.lower()
    for term in terms:
        if term in lower_body:
            term_bodies[term].append(body)

# Convert dictionary values to a list of lists
sectioned_bodies = [term_bodies[term] for term in terms]
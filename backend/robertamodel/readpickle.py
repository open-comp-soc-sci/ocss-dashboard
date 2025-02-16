import pickle
import pandas as pd

with open('backend/robertamodel/full_db.pickle', "rb") as file:
    df = pd.read_pickle(file)

terms = ["mvd", "nerve pain", "opioids", "pregabalin", 
         "carbamazepine", "carbamazapine", "oxcarbazepine", "oxcarbazapine"]

df = df.fillna("")

# extract body strings that contain at least one of the predefined terms
filtered_bodies = [body for body in df["body"] if any(term in body.lower() for term in terms)]


import json
import pandas as pd
import requests
from roberta import run_roberta_analysis

# Load grouping results
with open("grouping_results.json") as f:
    grouping_data = json.load(f)

meta = grouping_data["meta"]
groups = grouping_data["groups"]

# Get API parameters from meta
subreddit = meta["subreddit"]
option = meta["option"]
startDate = meta.get("startDate", "")
endDate = meta.get("endDate", "")

# Build API URL
api_url = f"http://sunshine.cise.ufl.edu:5000/api/get_all_click?subreddit={subreddit}&option={option}"
if startDate: api_url += f"&startDate={startDate}"
if endDate: api_url += f"&endDate={endDate}"

# Fetch data
response = requests.get(api_url)
response.raise_for_status()
data = response.json()

# Convert to DataFrame
if option == "reddit_submissions":
    df = pd.DataFrame(data["data"], columns=["id", "subreddit", "title", "selftext", "created_utc"])
    df = df.rename(columns={"selftext": "body"})
else:
    df = pd.DataFrame(data["data"], columns=["subreddit", "title", "body", "created_utc", "id"])

df = df.fillna("")

# Prepare grouped terms and sectioned_bodies
all_group_terms = []  # List of term lists
all_sectioned_bodies = []

for group in groups.values():
    for topic in group:
        keywords = topic["ctfidf_keywords"]
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

for terms, sectioned_bodies in all_sectioned_bodies:
    stats = run_roberta_analysis(terms, sectioned_bodies)
    print(stats)

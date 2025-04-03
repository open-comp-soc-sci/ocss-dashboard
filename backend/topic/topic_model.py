import pandas as pd
import numpy as np
import pika
import json
import os
import re
import argparse
import pickle
from tqdm import tqdm

from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from langchain.llms import Ollama

from sentence_transformers import SentenceTransformer

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import MinMaxScaler as mms
from sklearn.cluster import KMeans, SpectralClustering
from hdbscan import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity, cosine_distances
from sklearn.metrics import silhouette_score, davies_bouldin_score

from umap import UMAP
import requests

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import colormaps as cm
import matplotlib.font_manager as fm

sns.set_style('whitegrid')
sns.set_context('talk')

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = "CMU Sans Serif"
plt.rcParams['font.family'] = "sans-serif"
plt.rcParams['mathtext.fontset'] = 'cm'

OLLAMA_IP = os.getenv("OLLAMA_IP_ADDRESS", "http://maltlab.cise.ufl.edu:11434")  # Default if not set

# Updated configuration
config = {
    # Set data_source to "api" to indicate that data should be fetched via HTTP
    'data_source': 'api',
    # For API queries, specify the subreddit and option (submissions or comments)
    'subreddit': 'survivor',  # adjust as needed
    'option': 'reddit_submissions',  # or "reddit_comments"
    
    'embeddings': {
        'name': 'BAAI/bge-base-en-v1.5',
        'device': 'cuda'
    },
    'save_dir': "saved",
    'random_state': 42,
    'topic_hdbscan_params': {
        'min_cluster_size': 100,
        'metric': 'euclidean',
        'cluster_selection_method': 'eom',
        'prediction_data': True
    },
    'topic_umap_params': {
        'n_neighbors': 15,
        'n_components': 7,
        'min_dist': 0.0,
        'metric': 'cosine',
        'random_state': 42
    },
    'group_umap_params': {
        'n_neighbors': 2,
        'n_components': 3,
        'min_dist': 0.0,
        'metric': 'hellinger',
        'spread': 2,
        'random_state': 42
    },
    'ngram_representation': {
        'stop_words': 'english'
    },
}

class TopicModeling():
    """
    Class for handling BERTopic modeling for Reddit data.
    Instead of reading a pickle file, it queries the ClickHouse API endpoint.
    """

    def __init__(self, config=config):
        self.config = config

    def run(self):
        self.load_data_frame()
        self.find_topics()
        self.label_topics()
        self.find_groups()
        self.label_groups()
        self.send_groups()
        # self.plot_topics()
        self.create_topic_table()

        
    def load_data_frame(self):
        """
        Loads the Reddit posts/comments dataframe by querying the API.
        
        """
        if self.config.get("data_source", "pickle") == "api":
            # Get parameters from the configuration.
            subreddit = self.config.get("subreddit")
            option = self.config.get("option", "reddit_submissions")
            start_date = self.config.get("startDate", "")
            end_date = self.config.get("endDate", "")
            # Build the API URL and append date parameters if provided.
            print('fetching from clickhouse')

            api_url = f"http://sunshine.cise.ufl.edu:5000/api/get_all_click?subreddit={subreddit}&option={option}"
            if start_date:
                api_url += f"&startDate={start_date}"
            if end_date:
                api_url += f"&endDate={end_date}"
            try:
                response = requests.get(api_url)
                response.raise_for_status()
                data = response.json()
                # Print the first 5 records from the "data" key.
                # print(data["data"][0:5])
                # Iterate over the actual records list.
                # for record in data["data"]:
                    # print(record[-1])

            except Exception as e:
                raise Exception(f"Error fetching data from API: {e}")

            print('done fetching from clickhouse')
            
            # Convert the JSON data into a DataFrame based on the option.
            # For submissions:
            if option == "reddit_submissions":
                df = pd.DataFrame(data["data"], columns=["id", "subreddit", "title", "selftext", "created_utc"])
                df = df.rename(columns={"selftext": "body"})
            elif option == "reddit_comments":
                df = pd.DataFrame(data["data"], columns=["subreddit", "title", "body", "created_utc", "id"])
                # df = pd.DataFrame(data["data"], columns=["id", "parent_id", "subreddit", "body", "created_utc"])

            else:
                raise ValueError(f"Invalid option provided: {option}")


            # print('!')
            # print(df.head().to_string())
            # print(":__)")
            self.df = self.preprocess_dataframe(df)
            self.texts = self.df['body'].tolist()

            # print(self.df.to_string())
            # print(len(self.df))
            # print("************")

            print('hello')
            print(self.df['created_utc'].unique())
        else:
            # Fallback if data_source is not "api". (Legacy support for pickle files.)
            if self.config['data'].split('.')[-1] != 'pickle':
                raise TypeError('Expected a pickle file. Other input types not yet supported.')
            df = pd.read_pickle(self.config['data'])
            self.df = self.preprocess_dataframe(df)
            self.texts = self.df['body'].tolist()


    @staticmethod
    def preprocess_dataframe(df):
        """
        Preprocess the dataframe for topic modeling.
        """
        df['body'].fillna("", inplace=True)
        df['body'] = df['body'].str.replace(r"http\S+", "", regex=True)
        df['body'] = df['body'].str.replace(r"\\n", " ", regex=True)
        df['body'] = df['body'].str.replace("&gt;", "", regex=False)
        df['body'] = df['body'].str.replace(r'\s+', ' ', regex=True)
        df['body_len'] = df['body'].str.len()
        df = df.query('body_len >= 25')
        return df

    def find_topics(self):
        vectorizer_model = CountVectorizer(stop_words='english', ngram_range=(1, 2))
        embedding_model = SentenceTransformer(self.config['embeddings']['name'], device=self.config['embeddings']['device'])
        self.embeddings = embedding_model.encode(self.texts, show_progress_bar=True, batch_size=64)
        umap_model = UMAP(**self.config['topic_umap_params'])
        u = umap_model.fit_transform(self.embeddings)
        hdbscan_model = HDBSCAN(**self.config['topic_hdbscan_params'])
        clusters = np.array(hdbscan_model.fit_predict(u))
        n_clusters = np.max(clusters) + 1
        centroids = np.empty((n_clusters, u.shape[1]))
        for cluster_i in range(n_clusters):
            inds_in_cluster_i = np.where(clusters == cluster_i)[0]
            points_in_cluster_i = u[inds_in_cluster_i]
            centroids[cluster_i, :] = np.mean(points_in_cluster_i, axis=0)
        kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, init=centroids)
        representation_model = KeyBERTInspired()
        self.topic_model = BERTopic(vectorizer_model=vectorizer_model,
                                    embedding_model=embedding_model,
                                    umap_model=umap_model,
                                    hdbscan_model=kmeans_model,
                                    representation_model=representation_model,
                                    verbose=True)
        self.topics, _ = self.topic_model.fit_transform(self.texts, self.embeddings)
        if not os.path.exists(self.config['save_dir']):
            os.makedirs(self.config['save_dir'])
        self.topic_model.save(f'{self.config["save_dir"]}/topic_model.pickle', save_ctfidf=True)
        with open(f'{self.config["save_dir"]}/topics.pickle', 'wb') as fh:
            import pickle
            pickle.dump(self.topics, fh)

    def label_topics(self):
        self.topic_labeler = TopicLabeling(self.df, self.topics, self.embeddings, self.topic_model, self.config)

    def find_groups(self):
        c_tf_idf_mms = mms().fit_transform(self.topic_model.c_tf_idf_.toarray())
        self.c_tf_idf_vis = UMAP(n_neighbors=2, n_components=2, metric='hellinger', random_state=self.config['random_state']).fit_transform(c_tf_idf_mms)
        self.c_tf_idf_embed = UMAP(**self.config['group_umap_params']).fit_transform(c_tf_idf_mms)
        ideal_n_clusters = self.find_ideal_num_groups()
        self.groups = SpectralClustering(n_clusters=ideal_n_clusters, random_state=self.config['random_state']).fit_predict(self.c_tf_idf_embed) + 1

    def label_groups(self):
        self.group_labeler = GroupLabeling(self.topics, self.topic_labeler.topic_labels, self.groups)

    def find_ideal_num_groups(self, llim=3, ulim=40):
        c_tf_idf_embed = self.c_tf_idf_embed
        n_samples = c_tf_idf_embed.shape[0]
        upper_bound = min(ulim, n_samples + 1)
        ss = []
        cluster_arr = np.arange(llim, upper_bound, 2)
        for n_clusters in cluster_arr:
            clusters = SpectralClustering(n_clusters=n_clusters, random_state=42, n_components=2).fit_predict(c_tf_idf_embed)
            ss.append(silhouette_score(c_tf_idf_embed, clusters))
        ideal_n_clusters = cluster_arr[np.argmax(ss)]
        ideal_n_clusters = min(ideal_n_clusters, n_samples)
        print("top silhouette score: {0:0.3f} for at n_clusters {1}".format(np.max(ss), ideal_n_clusters))
        return ideal_n_clusters


    @staticmethod
    def find_clustering_scores(c_tf_idf_embed, llim=3, ulim=40):
    
        ss = []
        db = []
        
        cluster_arr = np.arange(llim, ulim, 2)
        
        for n_clusters in cluster_arr:
            clusters = SpectralClustering(n_clusters=n_clusters, random_state=42, n_components=2).fit_predict(c_tf_idf_embed)
            ss.append(silhouette_score(c_tf_idf_embed, clusters))
            # db.append(davies_bouldin_score(c_tf_idf_embed, clusters))
            
        with sns.plotting_context('notebook'):
            sns.set_style('ticks')
            fig, ax = plt.subplots(figsize=(5, 2.5))
            
            try:
                sns.lineplot(x=cluster_arr, y=ss, palette='autumn', ax=ax, color=cm['autumn'](0.3))
            except Exception as e:
                print(e)
            
            ax.set_ylabel('Silhouette Score')
            ax.set_xlabel('Number of Clusters')
            ax.set_title('Clustering Performance', fontsize=15, y=0.95)

        ideal_n_clusters = cluster_arr[np.argmax(ss)]

        print("top silhouette score: {0:0.3f} for at n_clusters {1}".format(np.max(ss), cluster_arr[np.argmax(ss)]))    
        return ideal_n_clusters

        def plot_topics(self):
            with sns.plotting_context('notebook'):
                sns.set_style('white')
                plt.figure(figsize=(10, 5))
                vis_arr = self.c_tf_idf_vis
                n_clusters = self.groups.max() - self.groups.min() + 1
                ax = sns.scatterplot(x=vis_arr[:, 0], y=vis_arr[:, 1],
                                    size=self.topic_model.get_topic_info()['Count'],
                                    hue=self.groups,
                                    sizes=(100, 5000),
                                    alpha=0.5, palette='tab20', legend=True, edgecolor='k')
                h, l = ax.get_legend_handles_labels()
                plt.legend(h[0:n_clusters], l[0:n_clusters], bbox_to_anchor=(-0.011, -1.95), loc='lower left', borderaxespad=1, fontsize=10)
                ax.set_title('Topics, Grouped by Similarity of Content', fontsize=16, pad=10)
                ax.set_xlabel('Feature 1')
                ax.set_ylabel('Feature 2')
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                ax.figure.savefig(f'{self.config["save_dir"]}/figure_topics_bydisc.png', dpi=300, bbox_inches="tight")

    def create_topic_table(self):
        df, topics, embeddings = self.df, self.topics, self.embeddings
        topic_labels, groups = self.topic_labeler.topic_labels, self.groups
        rep_docs = TopicLabeling.find_representative_docs_per_topic(df, topics, embeddings, 1)
        topic_table = pd.DataFrame(
            index=np.arange(1, np.max(topics) + 2).astype('int'),
            columns=[
                'Discussions (#)',
                'Group',
                'Topic Label',
                'Representative Post',
                'Post IDs',
                'c-TF-IDF Keywords'
            ]
        )
        top_n = 5
        for group in range(1, groups.max() + 1):
            topics_group_i = np.where(groups == group)[0]
            for tl_i in topics_group_i:
                topic_table.loc[tl_i + 1, 'Topic Label'] = self.topic_labeler.topic_labels[tl_i]
                topic_table.loc[tl_i + 1, 'Group'] = group
                topic_table.loc[tl_i + 1, 'Representative Post'] = rep_docs[tl_i][0]
                topic_table.loc[tl_i + 1, 'Discussions (#)'] = len(np.where(np.array(topics) == tl_i)[0])
                post_ids = df.loc[np.array(topics) == tl_i, 'id']
                post_ids_str = ", ".join(post_ids.astype(str))
                topic_table.loc[tl_i + 1, 'Post IDs'] = post_ids_str
                ctfidf_words = self.topic_model.get_topic(tl_i)[:top_n]
                top_words_str = ", ".join(word for word, weight in ctfidf_words)
                topic_table.loc[tl_i + 1, 'c-TF-IDF Keywords'] = top_words_str
        topic_table.to_excel(f'{self.config["save_dir"]}/topic_table.xlsx')

    def send_groups(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="sunshine.cise.ufl.edu", port=5672,
            credentials=pika.PlainCredentials("user", "password")))
        channel = connection.channel()
        channel.queue_declare(queue="grouping_results", durable=True)
        
        # Build a dictionary that includes group details.
        group_data = {}
        for idx, group in enumerate(self.groups):
            # Convert the group key to a native int
            group_key = int(group)
            topic_label = self.topic_labeler.topic_labels.get(idx, "No label")
            if group_key not in group_data:
                group_data[group_key] = []
            group_data[group_key].append({
                "topic_index": int(idx),  # Also convert idx if necessary
                "topic_label": topic_label,
                # You could add more details here, such as representative docs or counts.
            })

        message = json.dumps(group_data)

        channel.basic_publish(
            exchange="",
            routing_key="grouping_results",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f" [x] Sent {message}")
        connection.close()


class TopicLabeling():

    def __init__(self, df, topics, embeddings, topic_model, config):
        self.df = df
        self.topics = topics
        self.embeddings = embeddings
        self.topic_model = topic_model
        self.config = config

        self.llm = Ollama(model="gemma2:27b", base_url=f"http://ollama_container:11434")

        self.topic_representations = self.find_topic_representations()

    
    def find_topic_representations(self, n_reps=10):
        df = self.df
        topics = self.topics
        embeddings = self.embeddings
        topic_model = self.topic_model

        # 1) representative & random docs
        rep_docs = self.find_representative_docs_per_topic(df, topics, embeddings, n_reps)
        rand_docs = self.find_random_docs_per_topic(df, topics, n_reps)
        prompt_docs = [i[:5] + j[:5] for i, j in zip(rep_docs, rand_docs)]

        representations = {}  # This will hold {topic_index -> list_of_labels}
        
        for topic in tqdm(range(np.max(topics) + 1)):
            # 2) Build the prompt
            prompt_i = self.prepare_prompt(topic_model, prompt_docs, topic)
            
            # 3) Get raw LLM response
            raw_response = self.llm.predict(prompt_i)
            raw_response = raw_response.replace("**", "")  # remove bold markers if any

            # 4) Try parsing JSON
            try:
                labels_list = json.loads(raw_response)  # Expecting something like ["Label 1","Label 2","Label 3"]
            except json.JSONDecodeError:
                # Fallback if the model doesn't return valid JSON
                labels_list = ["Error Label 1", "Error Label 2", "Error Label 3"]

            # 5) Store as a list of strings
            representations[topic] = labels_list

        # Save all final representations
        self.topic_representations = representations
        with open(f'{self.config["save_dir"]}/llama_topic_representations_i.pickle', 'wb') as fh:
            pickle.dump(representations, fh)

        # 6) Convert to a simpler string or keep them as lists
        self.topic_labels = {}
        for topic_i, label_list in representations.items():
            # Join them with commas or semicolons for your table if needed:
            self.topic_labels[topic_i] = ", ".join(label_list)

        # Done! No need for the old 'pattern' or 'representations_extracted' logic


    def prepare_topic_results_for_review(self):
        df = self.df
        topics = self.topics
        embeddings = self.embeddings
        topic_model = self.topic_model
        topic_representations = self.topic_representations
        
        rep_docs = self.find_representative_docs_per_topic(df, topics, embeddings, 5)
        rand_docs = self.find_random_docs_per_topic(df, topics, 5)

        final_prompt = ''

        for topic in tqdm(range(np.max(topics) + 1)):
            
            prompt = f'\n================================ TOPIC {topic} ======================================\n'
            
            prompt += 'Topic keywords:\n\''
            prompt += '\', \''.join(topic_model.get_topic_info(topic)['Representation'][0])
            
            prompt += '\'.\n\nRepresentative discussions:\n=======' 
            prompt += '\n======='.join(rep_docs[topic])

            prompt += '\'.\n\nRandom discussions:\n=======' 
            prompt += '\n======='.join(rand_docs[topic])

            topic_labels = ', '.join(topic_representations[topic])
            prompt += f'\n\nFinal label: {topic_labels}'

            final_prompt += prompt + '\n===========================================================================================\n'

        return final_prompt
    
    @staticmethod
    def prepare_prompt(topic_model, rep_docs, topic_of_interest):
        """
        Returns a prompt that explicitly instructs the LLM to output three short labels 
        in strict JSON format: ["Label 1","Label 2","Label 3"].
        """
        prompt = """
    You are an AI assistant that returns exactly three short labels in JSON array format, with no additional text or commentary.
    For example: ["Label A","Label B","Label C"].

    Below are topic keywords and a handful of representative documents. 
    Please respond with ONLY a single JSON array of exactly three short labels, 
    and nothing else (no extra text, no quotes around the JSON).

    Topic keywords:
    {keywords}

    Representative documents:
    {docs}

    Now produce one JSON array of three short labels, e.g.: ["Label 1","Label 2","Label 3"].
    """.format(
            keywords=", ".join(topic_model.get_topic_info(topic_of_interest)['Representation'][0]),
            docs="\n".join(rep_docs[topic_of_interest])
        )

        return prompt


    @staticmethod
    def find_representative_docs_per_topic(df, topics, embeddings, n_reps=5):
        topics = np.array(topics)
        n_topics = topics.max() + 1
        emb_dim = embeddings.shape[1]
        samples_in_topics = [np.where(topics == i)[0] for i in range(n_topics)]
        centroids = np.array([np.mean(embeddings[topic_inds, :], axis=0) for topic_inds in samples_in_topics])
        
        representative_samples = []
        
        for topic_i, (centroid_i, samples_i) in tqdm(enumerate(zip(centroids, samples_in_topics))):
            embedded_samples_i = embeddings[samples_i, :]
            distances = cosine_distances(embedded_samples_i, centroid_i.reshape(1, emb_dim)).flatten()
            dist_inds = np.argsort(distances)
            rep_docs_i = df.iloc[samples_i[dist_inds[:n_reps]]]['body'].values.tolist()
            representative_samples.append(rep_docs_i)
        
        return representative_samples

    @staticmethod
    def find_random_docs_per_topic(df, topics, n_reps):
        rand_docs = []
        for topic in tqdm(range(np.max(topics) + 1)):
            topic_inds = np.where(np.array(topics) == topic)[0]
            if len(topic_inds) < n_reps:
                samples_i = df.iloc[topic_inds]['body'].values.tolist()
            else:
                samples_i = df.iloc[topic_inds]['body'].sample(n=n_reps, random_state=42).values.tolist()
            rand_docs.append(samples_i)
        return rand_docs
    
    def prepare_prompts_for_topic_labeling(self, n_reps=10):

        df = self.df
        topics = self.topics
        embeddings = self.embeddings
        topic_model = self.topic_model


        # Find representative documents for each topic
        rep_docs = self.find_representative_docs_per_topic(df, topics, embeddings, n_reps)

        # Find a random selection of documents for each topic
        rand_docs = self.find_random_docs_per_topic(df, topics, n_reps)
        
        # Combine these two
        prompt_docs = [i[:5] + j[:5] for i, j in zip(rep_docs, rand_docs)]

        # Find the representation for each topic
        prompts = {}
        for topic in tqdm(range(np.max(topics) + 1)):
            prompt_i = self.prepare_prompt(topic_model, prompt_docs, topic)
            prompts[topic] = prompt_i

        self.prompts = prompts

class GroupLabeling():

    def __init__(self, topics, topic_labels, groups):
        self.topics = topics
        self.groups = groups              # <-- Store groups
        self.topic_labels = topic_labels  # <-- Store topic labels
        self.create_group_labels(groups, topic_labels)
        self.prepare_prompts_for_group_labeling()
        self.finalize_group_labels_with_llm()

    def create_group_labels(self, groups, topic_labels):
        group_labels_combined = {}

        g_min = np.min(groups)
        g_max = np.max(groups)
        for group_i in range(g_min, g_max + 1):
            group_i_inds = np.where(group_i == groups)[0]
            group_i_label = ''
            for group_i_ind in group_i_inds:
                group_i_label += topic_labels[group_i_ind].replace('"', '') + '\n'
            group_labels_combined[group_i] = group_i_label

        for group_i, group_label_combined in group_labels_combined.items():
            print(f'{group_i} :: {group_label_combined}')

        self.group_labels_combined = group_labels_combined

    def prepare_prompts_for_group_labeling(self):
        group_prompts = {}
        for group, group_label in self.group_labels_combined.items():
            # Create prompt for LLaMa2
            prompt = 'You are a honest, scientific chatbot that helps me, a sociologist, create a single representative label for a group that represents a series of topics based on topic labels. Each topic label is separated by a new line character. Do not be creative or loquacious. Please present the group label in a short and direct manner.\n\n'
            prompt += 'I have a group that is described by the following topic labels:\n\''
            prompt += group_label
            prompt += '\n\nBased on the information above, can you create the one, best, direct label for this topic in the following format?\n'
            prompt += 'Group Label: <group_label>'

            group_prompts[group] = prompt
            
        self.group_prompts = group_prompts
    
    def finalize_group_labels_with_llm(self):
        labels = {}
        llm = Ollama(model="gemma2:27b", base_url=f"http://ollama_container:11434", temperature=0.1)
        pattern = r"(?<=Group Label: )(.*)"
        
        for group, prompt in tqdm(self.group_prompts.items()):
            response = llm.predict(prompt)
            response.replace('"', '')
            labels[group] = re.findall(pattern, response)[0]
            
        self.group_labels = labels
    
    def create_topic_group_listing(self):

        groups, topic_labels = self.groups, self.topic_labels

        text = ''

        for group in range(1, groups.max() + 1):
            text += f'=========================== GROUP {group} ===========================\n'
            text += f'LLM Label: {self.group_labels[group]}\n'
            text += f'==== TOPICS ====\n'
            topics_group_i = np.where(groups == group)[0]

            for tl_i in topics_group_i:
                text += f'TOPIC {tl_i} :: {topic_labels[tl_i]}\n'

            text += f'===============================================================\n'

        return text


if __name__ == '__main__':
    import sys
    from sklearn.metrics import silhouette_score  # Needed for find_ideal_num_groups
    parser = argparse.ArgumentParser()
    parser.add_argument('data', type=str, nargs='?', default='api', help='Set to "api" to query data via the API')
    parser.add_argument('output', type=str, nargs='?', default='saved/topic_model_res.xlsx', help='Path to save topic, group labels')
    args = parser.parse_args()

    # Update config to use API if specified.
    if args.data == 'api':
        config['data_source'] = 'api'
    else:
        config['data'] = args.data

    config['output'] = args.output

    topic_model = TopicModeling(config)
    topic_model.load_data_frame()
    topic_model.run()
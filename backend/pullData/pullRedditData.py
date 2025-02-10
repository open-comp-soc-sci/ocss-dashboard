import pandas as pd
import json
import requests
import os
from urllib.parse import quote as url_parse
import argparse
import time
# Used open source code found at https://github.com/sssomani/glp1_reddit/blob/v0.1/topic_modeling/scrape_reddit.py as skeleton code

"""
Using pullRedditData.py:
This file can be run (when standing in the backend/ directory) using the following terminal command:
python .\pullRedditData.py {subreddit} -n {numberToPull}
ex:
    python .\pullRedditData.py askscience -n 2000
The example code would pull 2000 posts and 2000 comments from r/askscience plus 100 from initializing the database (4200 total entries)
The data is then saved to the pickle files in ./scrapedData/ 
Sequential runs load the previous data and pull 2*{numberToPull} entries
if -n {numberToPull} is excluded, the default is pulling the entire subreddit. 
This may take a very long time, my tests varied around 2000 entries per minute
"""

def create_base_url(discussion, search_string, subreddit):
    """
    Function to create the base URL for scraping Reddit.
    """
    
    # Ensure specified discussion is either a post (submission) or comment.
    assert discussion in ['submission', 'comment']
    
    # Craft our URL.
    return f'https://api.pullpush.io/reddit/search/{discussion}/?q={search_string}&size=100&subreddit={subreddit}'

def scrape_to_json(url):
    """
    Function that scrapes the Pushshift API based on a specific URL and converts those results to a Pandas dataframe.
    """
    success = False
    maxTries = 5

    for delay in range(maxTries):
        data = requests.get(url)
        status = data.status_code
        if status >= 200 and status < 300:
            #print(f'Success! Status: {status}')
            success = True
            break
        elif status in [429, 500, 502, 503, 504]:
            print(f'Received status: {status}. Retrying in {delay} seconds.')
            time.sleep(delay)
        else:
            print(f'Received status: {status}.')
            break
    if not success:
        print("Maximum retries reached.")
        return None
    
    data_json = json.loads(data.content)
    
    try:
        data_pd = pd.DataFrame(data_json['data'])
    except:
        return None
    return data_pd

def scrape_reddit(base_url, save_dir, search_string, subreddit, type=None, n=None):
    
    keys_to_keep = [
        'subreddit',
        'author',
        'created_utc',
        'body',
        'id'
    ]
    
    if os.path.exists(f'{save_dir}db_{subreddit}_{search_string}_{type}.pickle'):
        discussions = pd.read_pickle(f'{save_dir}db_{subreddit}_{search_string}_{type}.pickle')
        print(f'Old discussions file loaded! Number of discussions: {len(discussions)}')
    else:
        print('Discussions file not found; restarting.')
        discussions = scrape_to_json(base_url)
        if type == 'posts':
            discussions['body'] = discussions['title'] + '. ' + discussions['selftext']
        discussions = discussions[keys_to_keep]
        discussions = preprocess_db(discussions)


    n_discussions = len(discussions)
    if n != None: n = n_discussions + n

    while n_discussions > 0:
        last_utc = int(discussions['created_utc'].iloc[-1])
        url = base_url + f'&before={last_utc}'
        
        next_discs = scrape_to_json(url)
        if next_discs is None:
            print('No discussions found, so let\'s try this again...')
            continue

        if type == 'posts':
            next_discs['body'] = next_discs['title'] + '. ' + next_discs['selftext']

        next_discs = next_discs[keys_to_keep]
        next_discs = preprocess_db(next_discs)
        n_discussions = len(next_discs)
                
        discussions = pd.concat([discussions, next_discs])

        print(f'Total {type} so far: {discussions.shape[0]}')
        discussions.to_pickle(f'{save_dir}db_{subreddit}_{search_string}_{type}.pickle')
        if n: 
            if n <= discussions.shape[0]: break
            
    print(discussions)
    return discussions

def get_reddit_data(save_dir, search_strings = [''], subreddit = 'TrigeminalNeuralgia', n = None):
    '''
    
    Scrape Reddit for all discussions related to a set of search strings.         

    Parameters
    ----------
    search_string : str
        Search string to query.
    output_fn : str, optional
        Name of the local Excel database to save data. 

    Returns
    -------
    posts_df : Pandas dataframe
        Database

    '''
    
    discussions = pd.DataFrame(columns=[
        'subreddit',
        'author',
        'created_utc',
        'body',
        'type'
        'id',
    ])
    
    for search_string in search_strings:
        print(f'========= {search_string} ==========')

        search_string = url_parse(search_string)

        # First, let's start by searching all posts.
        post_url = create_base_url('submission', search_string, subreddit)
        posts = scrape_reddit(post_url, save_dir, search_string, subreddit, type='posts', n=n)
        posts['type'] = 'post'
        if (search_string !=['']): posts['search_string'] = search_string

        # Now, let's search all comments.
        comment_url = create_base_url('comment', search_string, subreddit)
        comments = scrape_reddit(comment_url, save_dir, search_string, subreddit, type='comments', n=n)
        comments['type'] = 'comment'
        if (search_string !=['']): comments['search_string'] = search_string
        
        discussions = pd.concat([discussions, posts, comments])
    
    discussions = discussions.drop_duplicates(subset='body')
    print(f'Total of {discussions.shape[0]} found!')

    return discussions

def preprocess_db(df):
    # Fill empty cells and remove some weird html tags
    # Also removes entries shorter than 20 chars
    df['body'] = df['body'].fillna('')
    df.dropna(axis=1, how='all')
    df['body'] = df['body'].str.replace("http\S+", "")
    df['body'] = df['body'].str.replace("\\n", " ")
    df['body'] = df['body'].str.replace("&gt;", "")
    df['body'] = df['body'].str.replace('\s+', ' ', regex=True)
    df['body_len'] = df['body'].str.len()
    df = df.query('body_len >= 20')
    return df

if __name__ == '__main__':

    """
    Scrape the subreddit r/TrigeminalNeuralgia
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('subreddit', type=str, help='Subreddit to pull data from')
    parser.add_argument('-n', type=int, help='Number of posts and comments to scrape')
    args = parser.parse_args()

    output_dir = os.getcwd() + '/scrapedData/'
    
    start_time = time.time()
    full_db = get_reddit_data(output_dir, [''], args.subreddit, args.n)

    if not args.n:
        n = full_db.shape[0]
    else:
        n = args.n
    print(f"Time in seconds to gather {n} posts/comments: {time.time()-start_time}")

    full_db.to_pickle(output_dir + f'{args.subreddit}_full_db.pickle')
    print(f"Time after saving to pickle: {time.time()-start_time}") 

    try:
        full_db.to_excel(output_dir + f'{args.subreddit}_full_db.xlsx')
    except:
        print('Failed to export Excel file.')
    print(f"Time after saving to excel: {time.time()-start_time}") 

'''
    data = requests.get('https://api.pullpush.io/reddit/search/comment/?subreddit=TrigeminalNeuralgia&q=')
    data_json = json.loads(data.content)
    
    data_pd = pd.DataFrame(data_json['data'])
    data_pd.to_excel(output_dir + 'full_db.xlsx')
'''
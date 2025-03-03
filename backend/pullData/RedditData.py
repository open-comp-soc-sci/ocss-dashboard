import os
import pandas as pd
from pullRedditData import load_reddit_data
from dataclasses import dataclass
'''
This class will act as a data manager for the subreddit data. It will get the data from pullRedditData.py (or the database or smth),
and load it into memory. When getPostThread() is called, it gets the first post (incrementing upon every call) and all of its associated comments.
It returns the PostThread containing postID as well as body which has the text contents of the post and its comments.
After returning the last PostThread, it will return None and reset the pointer back to the first post
keys_to_keep = [
        'author',
        'created_utc',
        'body',
        'id',
        'link_id'
    ]
'''

@dataclass
class PostThread:
    id: int
    body: str

class RedditDataManager:

    msg_unloaded_data = "No data has been loaded"
    
    def __init__(self, subreddit): 
        self.subreddit = subreddit
        self.posts = None
        self.comments = None
        self.save_dir = os.getcwd() + '/scrapedData/'
        self.dataLoaded = False
        self.postInd = None

    def load_data(self):
        load_reddit_data(self.save_dir, self.subreddit)
        self.posts = pd.read_pickle(f'{self.save_dir}db_{self.subreddit}_posts.pickle')
        self.comments = pd.read_pickle(f'{self.save_dir}db_{self.subreddit}_comments.pickle')
        self.postInd = 0
        self.dataLoaded = True

    def reset_post_ind(self):
        self.postInd = 0

    def setSaveDir(self, save_dir):
        self.save_dir = save_dir

    def isLoaded(self):
        return self.dataLoaded
    
    def getPostThread(self):
        if (self.isLoaded()):
            if (self.postInd >= self.posts.shape[0]):
                self.reset_post_ind()
                return None
            else:
                postThread = self.loadCommentsofPost(self.posts.iloc[self.postInd].at['id'])
                self.postInd += 1
                return postThread
        else:
            return None

    def loadCommentsofPost(self, post_id):
        linkedComments = self.comments[self.comments['link_id'] == post_id]
        dataString = self.posts.iloc[self.postInd].at['body']
        if not linkedComments.empty:
            for comment in linkedComments:
                print(comment)
                dataString += ' ' + comment.body
        return PostThread(post_id, dataString)


    def save_to_csv(self):
        if (self.isLoaded()):
            postThread = self.getPostThreads
            postThread.to_excel(self.output_dir + f'{self.subreddit}_full_db.xlsx')

if __name__ == "__main__": 
    subredditData = RedditDataManager('TrigeminalNeuralgia')
    subredditData.load_data()
    postThread = subredditData.getPostThread()
    while (postThread != None):
        print(f"Thread #{subredditData.postInd} is {len(postThread.body)} chars long")
        postThread = subredditData.getPostThread()


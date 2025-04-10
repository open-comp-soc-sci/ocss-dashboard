this program is adapted from
https://github.com/sssomani/glp1_reddit/blob/main/topic_modeling/topic_model.py

A cluster is a cluster if at least 50 posts relate to a common topic area.

Min samples is set to 5, meaning fifth nearest neighbor to the next point (or,
a post-- means the same thing) is considered as an entire cluster.
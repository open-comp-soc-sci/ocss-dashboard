# backend/topic/topic_model_service.py

import pandas as pd
from topic_model import TopicModeling  # or however you import your existing topic modeling class

def run_topic_model(data_source, output_dir, config):
    """
    Run topic modeling either using a pickle file or API-based data.
    
    Args:
      data_source: Either a file path (e.g. '/app/full_db.pickle') or a flag like 'api'
      output_dir: Directory where outputs should be saved.
      config: Configuration dictionary to control model behavior.
      
    Returns:
      A result message indicating where the outputs were saved.
    """
    # Update configuration.
    config['output'] = output_dir
    if data_source == 'api':
        config['data_source'] = 'api'
    else:
        config['data'] = data_source

    # Instantiate and run the topic modeling process.
    topic_model = TopicModeling(config)
    topic_model.run()
    
    # Instead of returning a generic message, return the detailed grouping results.
    group_listing = topic_model.group_labeler.create_topic_group_listing_json()

    return group_listing

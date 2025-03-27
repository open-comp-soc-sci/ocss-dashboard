from flask import request, send_from_directory
import os, subprocess
from . import pullReddit_BP
    
#NOT IMPLMENTED YET, WIP
@pullReddit_BP.route('/api/pullReddit/generate', methods=['GET'])
def pullReddit():
    subreddit = request.args.get('subreddit', None)
    numberToPull = request.args.get('numberToPull', type=int, default=2000)

    result = subprocess.run(
            ['python', './pullRedditData.py', subreddit, '-n', str(numberToPull)],
            check=True,
            capture_output=True,
            text=True
    )

    return "Data pulled successfully!", 200
 
@pullReddit_BP.route('/api/pullReddit/download/<subreddit>', methods=['GET'])
def downloadReddit(subreddit):
    #this will be in a text box to retrieve
    #subreddit = request.args.get('subreddit', None)
    fileName = f'{subreddit}_full_db.xlsx'
    filePath = os.path.join(pullReddit_BP.config['REDDIT_FOLDER'], fileName)

    if os.path.exists(filePath):
        return send_from_directory(pullReddit_BP.config['REDDIT_FOLDER'], fileName, as_attachment=True)
    else:
        return "File not found", 404
    

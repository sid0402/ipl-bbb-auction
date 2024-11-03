
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo
from bson import ObjectId
'''
uri = "mongodb+srv://sidagarwal0402:Stal0101@cluster0.ycclg2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['manager']
collection_batsmen = db['season_stats_batsmen']
collection_bowler = db['season_stats_bowler']


collection_batsmen.delete_many({})
collection_bowler.delete_many({})
'''
def update_season_stat(stats):
    try:          
        for player_stat in stats:
            filter_query = {"_id": player_stat['_id'], "name": player_stat["name"]}
            
            # Use $inc to aggregate the numeric fields
            update_query = {
                "$inc": {
                    "runs": player_stat['runs'],
                    "balls": player_stat['balls'],
                    "out": player_stat['out']
                }
            }
            
            # Check player type and perform the update operation
            if player_stat['type'] == 'batsmen':
                try:
                    result = collection_batsmen.update_one(filter_query, update_query, upsert=True)
                    #print(f"Updated batsman: {player_stat['name']}, Matched: {result.matched_count}, Modified: {result.modified_count}")
                except pymongo.errors.PyMongoError as e:
                    print(f"An error occurred with batsman {player_stat['name']}: {e}")
            else:
                try:
                    result = collection_bowler.update_one(filter_query, update_query, upsert=True)
                    #print(f"Updated bowler: {player_stat['name']}, Matched: {result.matched_count}, Modified: {result.modified_count}")
                except pymongo.errors.PyMongoError as e:
                    print(f"An error occurred with bowler {player_stat['name']}: {e}")
            
    except Exception as e:
        print(player_stat)
        print(f"An error occurred: {e}")
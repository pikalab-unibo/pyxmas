from Expectation.explainee_imp import ExplaineeAgent
from Expectation.recommender_imp import RecommenderAgent
import asyncio
import threading
from .xmpp import XmppService
import pyxmas

def Interact(username):

    pyxmas.enable_logging()

    try:
        local_service = XmppService()
        local_service.start()

        local_service.add_user(username=username, password="password")
        local_service.add_user(username="recommender-" + username, password="password")

        # Assuming these agents are asyncio compatible
        with RecommenderAgent(jid="recommender-"+username+"@localhost", password="password") as recommender, \
             ExplaineeAgent(user_id=username, jid=username+"@localhost", password="password") as explainee:
            
            # If these methods have async versions, use those instead
            explainee.sync_await(timeout=200)
            recommender.sync_await(timeout=200)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        local_service.stop()

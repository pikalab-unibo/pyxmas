from Expectation.explainee_imp import ExplaineeAgent
from Expectation.recommender_imp import RecommenderAgent
import asyncio
import threading

def Interact(username, local_service):
    # Note: Each process will have its own instance of XmppService.

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    local_service.add_user(username=username, password="password")
    local_service.add_user(username="recommender-" + username, password="password")

    print(threading.current_thread())

    with  RecommenderAgent(loop=loop, jid="recommender-"+username+"@localhost", password="password", thread = threading.current_thread().name ) as recommender:
         with ExplaineeAgent(loop = loop, user_id=username, jid=username+"@localhost", password="password",thread = threading.current_thread().name) as explainee:
            
            try:
                    print(f"Thread {recommender.thread}")
                    print(explainee.thread)
                    explainee.sync_await(timeout=200)
                    recommender.sync_await(timeout=200)
            
            except KeyboardInterrupt:
                        recommender.stop()
                        explainee.stop()

    loop.close()
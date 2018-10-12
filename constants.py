import os

# put all the java repo slugs here
JAVA_REPO_LIST = []
# put all the js repo slugs here
JS_REPO_LIST = []
# user who will commit
USER = "name <email>"
# commit to which branch
BRANCH = "master"
ORGANIZATION = "hogwarts"

bitbucket_client_id = os.environ.get('bitbucket_client_id')
bitbucket_secret = os.environ.get('bitbucket_secret')
import requests

from auth_access_key_generator import get_access_token
from constants import JAVA_REPO_LIST, JS_REPO_LIST, USER, BRANCH, bitbucket_client_id, bitbucket_secret, ORGANIZATION


class AuthException(Exception):
    pass


class SonarQubeConfigPusher(object):
    """
    Reference - https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/src#post
    """

    @staticmethod
    def call_get_access_token():
        access_token = get_access_token(bitbucket_client_id, bitbucket_secret,
                                        'https://bitbucket.org/',
                                        'https://bitbucket.org/site/oauth2/access_token')
        return access_token

    def start_pushing_sonarqube_configs_for_all_repos(self):
        """
        ENTRY POINT
        :return:
        """
        access_token = self.call_get_access_token()

        repo_list = self._fetch_all_the_repo_slugs(access_token)
        sorted_repo_slugs = sorted([i['slug'] for i in repo_list])

        self._sonar_qube_properties_aggregator_and_pusher(sorted_repo_slugs, access_token)

    def _sonar_qube_properties_aggregator_and_pusher(self, repo_slugs, access_token):
        """

        :param repo_slugs:
        :param access_token:
        :return:
        """
        error_repo = set()
        for repo_slug in repo_slugs:
            if repo_slug in JAVA_REPO_LIST:
                print(repo_slug, '---', 'java')
                error_repo = self._push_sonar_configs_to_bitbucket_repo(repo_slug, access_token, error_repo, 'java')
            elif repo_slug in JS_REPO_LIST:
                print(repo_slug, '---', 'js')
                error_repo = self._push_sonar_configs_to_bitbucket_repo(repo_slug, access_token, error_repo, 'js')
            else:
                # by default python - because I mostly work with python language
                print(repo_slug, '---', 'py')
                error_repo = self._push_sonar_configs_to_bitbucket_repo(repo_slug, access_token, error_repo)

        print("Not able to push to these repos - {}".format(error_repo))

    def _fetch_all_the_repo_slugs(self, access_token):
        """
        Fetches all the repo slugs for an organization
        :param access_token:
        :return:
        """
        repo_list = []
        start_url = 'https://api.bitbucket.org/2.0/repositories/{}/?pagelen=100'.format(ORGANIZATION)

        set_of_hundred_response = requests.get(start_url, headers={'Authorization': 'Bearer {}'.format(access_token)})

        repo_list.extend(set_of_hundred_response.json()['values'])

        while True:
            next_url = set_of_hundred_response.json().get('next')
            if next_url:
                try:
                    set_of_hundred_response = requests.get(next_url,
                                                           headers={'Authorization': 'Bearer {}'.format(access_token)})

                    if set_of_hundred_response.status_code == 401:
                        raise AuthException

                    repo_list.extend(set_of_hundred_response.json()['values'])
                except AuthException:
                    access_token = self.call_get_access_token()
                    set_of_hundred_response = requests.get(next_url,
                                                           headers={'Authorization': 'Bearer {}'.format(access_token)})

                    repo_list.extend(set_of_hundred_response.json()['values'])
            else:
                break
        return repo_list

    def _push_sonar_configs_to_bitbucket_repo(self, repo_slug, access_token, error_repo, language='py'):
        """
        Pushes the properties file to repo
        :param repo_slug:
        :param access_token:
        :param error_repo:
        :param language:
        :return:
        """

        repo_edit_url = 'https://api.bitbucket.org/2.0/repositories/{}/{}/src'.format(ORGANIZATION, repo_slug)

        # sonar properties file
        access_token = self._push_sonar_jenkins_properties_file(access_token, error_repo, language, repo_edit_url,
                                                                repo_slug)

        # sonar json file
        self._push_sonar_bitbucket_properties_file(access_token, error_repo, repo_edit_url, repo_slug)

        return error_repo

    def _push_sonar_bitbucket_properties_file(self, access_token, error_repo, repo_edit_url, repo_slug):
        """
        Pushes sonar.json file to repo
        :param access_token:
        :param error_repo:
        :param repo_edit_url:
        :param repo_slug:
        :return:
        """
        sonar_json_content = ''
        with open('sonar.json', 'r') as f:
            sonar_json_content += f.read(100000)

        final_sonar_json_content = sonar_json_content % repo_slug

        _sonar_bitbucket_properties = {
            "message": "Adding sonar json file",
            "branch": BRANCH,
            "author": USER,
            "/sonar.json": final_sonar_json_content
        }

        try:
            response = requests.post(repo_edit_url,
                                     headers={
                                         'Authorization': 'Bearer {}'.format(access_token),
                                         'Content-Type': 'application/x-www-form-urlencoded'},
                                     data=_sonar_bitbucket_properties)
            if response.status_code == 401:
                raise AuthException
            if response.status_code == 500:
                error_repo.add(repo_slug)
                print(response.content)
        except AuthException:
            access_token = self.call_get_access_token()
            response = requests.post(repo_edit_url,
                                     headers={
                                         'Authorization': 'Bearer {}'.format(access_token),
                                         'Content-Type': 'application/x-www-form-urlencoded'},
                                     data=_sonar_bitbucket_properties)

        print(final_sonar_json_content)
        print(repo_slug, '---- sonar.json -------->', response.status_code, '\n')

    def _push_sonar_jenkins_properties_file(self, access_token, error_repo, language, repo_edit_url, repo_slug):
        """
        Pushes sonar-project.properties to repo
        :param access_token:
        :param error_repo:
        :param language:
        :param repo_edit_url:
        :param repo_slug:
        :return:
        """
        properties_content = ''

        with open('sonar-project.properties', 'r') as f:
            properties_content += f.read(100000)

        final_properties_content = properties_content.format(repo_slug, repo_slug, repo_slug, repo_slug, language)

        _sonar_jenkins_properties = {
            "message": "Adding sonar properties file",
            "branch": BRANCH,
            "author": USER,
            "/sonar-project.properties": final_properties_content
        }

        try:
            response = requests.post(repo_edit_url,
                                     headers={
                                         'Authorization': 'Bearer {}'.format(access_token),
                                         'Content-Type': 'application/x-www-form-urlencoded'},
                                     data=_sonar_jenkins_properties)
            if response.status_code == 401:
                raise AuthException
            if response.status_code == 500:
                error_repo.add(repo_slug)
                print(response.content)
        except AuthException:
            access_token = self.call_get_access_token()
            response = requests.post(repo_edit_url,
                                     headers={
                                         'Authorization': 'Bearer {}'.format(access_token),
                                         'Content-Type': 'application/x-www-form-urlencoded'},
                                     data=_sonar_jenkins_properties)

        print(final_properties_content)
        print(repo_slug, '---- sonar.properties -------->', response.status_code)

        return access_token

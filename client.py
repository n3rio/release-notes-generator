import os
import sys
import json
import pickle
import requests
import datetime


class Client:
    _user = None
    _passwd = None

    def __init__(self, user, passwd, username, repo_slug, commit_id, project_dir):
        self._user = user
        self._passwd = passwd
        self._username = username
        self.repo = repo_slug
        self._pickle_count = 0
        self.commit_id = commit_id
        self.project_dir = project_dir

    def _request(self, method, endpoint, params=None, data=None, is_pags=False, is_commit=False):
        auth = (self._user, self._passwd)
        headers = {'Content-Type': 'application/json'}
        base_url = 'https://api.bitbucket.org/2.0/repositories/{0}/'.format(self.repo)
        url = base_url + endpoint
        _json = data
        if is_commit is True:
            try:
                response = requests.request(method, url, params=params, json=_json, auth=auth, headers=headers)
                return response
            except Exception as e:
                print('Error 8: ', e)
                return False
        if is_pags is False:
            try:
                response = requests.request(method, url, params=params, json=_json, auth=auth, headers=headers)
            except Exception as e:
                print('Error 0: ', e)
                return False
        else:
            try:
                response = requests.request(method, endpoint, auth=auth, headers=headers)
                self._pickle_count += 1
            except Exception as e:
                print('Error 4: ', e)
                return False
        response = json.loads(response.text)
        if is_commit is False:
            self.parse_data(response)
            if 'next' in response:
                self._pagination(response)
            else:
                self.parse_result()

    def _pagination(self, response):
        try:
            return self._request('GET', response['next'], is_pags=True)
        except Exception as e:
            print('Error 3: ', e)

    def _get(self, endpoint, params, is_commit=False):
        try:
            return self._request('GET', endpoint, params=params, is_commit=is_commit)
        except Exception as e:
            print('Error 1: ', e)

    def get_prs_commits(self, pr_id):
        endpoint = 'pullrequests/{0}/commits'.format(pr_id)
        params = {
            'state': 'MERGED',
            'state': 'OPEN',
            'state': 'SUPERSEDED',
        }
        try:
            return self._get(endpoint, params=params)
        except Exception as e:
            print('Error 2: ', e)

    def _save_to_file(self, data):
        current_dir = os.getcwd()
        with open(current_dir + '/release_note_' + str(datetime.datetime.today().date()), 'a') as out:
            try:
                out.write(json.dumps(data))
                out.write(',')
            except Exception as e:
                print('Error 5: ', e)
                return False

    def parse_data(self, data):
        current_dir = os.getcwd()
        try:
            data = json.dumps(data['values'])
        except Exception as e:
            print('Error 6: ', e)
        today = str(datetime.datetime.today().date())
        filename = current_dir + '/release_note_' + today + '_' + str(self._pickle_count)
        _pickle = open(filename, "wb")
        try:
            pickle.dump(data, _pickle)
        except Exception as e:
            print('Error 9: ', e)
            return False

    def parse_result(self):
        current_dir = os.getcwd()
        today = str(datetime.datetime.today().date())
        content = []
        result = []
        for i in range(self._pickle_count + 1):
            filename = current_dir + '/release_note_' + today + '_' + str(i)
            _unpickle = open(filename, "rb")
            for o in json.loads(pickle.load(_unpickle)):
                content.append(o)
        for i in content:
            result.append({
                'author': i['author']['raw'],
                'date': i['date'],
                'hash': i['hash'],
                'message': i['message'],
                'parents': [o['hash'] for o in i['parents']],
                'branch': self._get_branch(i['hash'], [o['hash'] for o in i['parents']])
            })
        try:
            self.export_markdown(result)
        except Exception as e:
            print('Error 11: ', e)
        return result

    def _get_branch(self, _hash, parents):
        os.chdir(str(self.project_dir))
        try:
            branches = os.popen('git branch --contains {}'.format(_hash)).read()
        except Exception as e:
            return "no such commit {}".format(_hash)
        if len(branches) == 0 and len(parents) > 0:
            return 'Check parents for birth branch (recursively)'
        return branches

    def export_markdown(self, data):
        os.chdir(str(self.project_dir))
        current_dir = os.getcwd()
        if not isinstance(data, list):
            return False
        print('Current dir: ', current_dir)
        with open(current_dir + '/mk_release_note_' + str(datetime.datetime.now()), 'w') as out:
            for i in data:
                out.write('## ' + i['message'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')
                out.write('##### Hash: ' + i['hash'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')
                out.write('##### Date: ' + i['date'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')
                out.write('##### Author: ' + i['author'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')
                if isinstance(i['parents'], list):
                    out.write('###### Parents: ' + ', '.join(i['parents']) + '\n')
                else:
                    out.write('###### Parents:  ' + i['parents'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')
                if isinstance(i['branch'], list):
                    out.write('###### Branch/s: ' + ', '.join(i['branch']) + '\n')
                else:
                    out.write('###### Branch/s:  ' + i['branch'].encode('utf-8').replace('\n', ' ') + '\n')
                out.write('\n')


if __name__ == '__main__':
    app = Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    app.get_prs_commits(app.commit_id)

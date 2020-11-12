import os
from git import Repo
import json
import subprocess
import re
import smtplib, ssl
from logger import Logger


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Tester:

    config = None
    logger = None

    def send_mail(self, subject, message, mails):

        smtp_server = self.config['mail']['smtp']
        port = self.config['mail']['port']
        sender_email = self.config['mail']['user']
        password = self.config['mail']['pass']

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)

            text = 'Subject: {}\n\n From: {}\n\n{}'.format(subject, self.config['mail']['from_name'], message)

            for mail in mails:
                server.sendmail(self.config['mail']['from_email'], mail, text)
        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit()


    def get_local_store_path(self, url, branch):
        if url.endswith(".git"):
            url = url[:-4]

        if url.startswith("https://", 0, 8):
            url = url[8:]
        elif url.startswith("http://", 0, 7):
            url = url[7:]
        elif url.startswith("git@", 0, 4):
            url = url[4:]
            url = url.replace(":", "/")
        else:
            print("Error in git url format...")
        return self.config['data_dir']+"/"+url+"/"+branch

    def get_repository_name(self, url):
        if url.endswith(".git"):
            url = url[:-4]

        segments = url.split('/')
        length = len(segments)
        repo = segments[-(length-3):]
        repo_name = "@".join(repo)
        return repo_name


    def has_changes_to_repository(self, url, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Create git reference
        if len(os.listdir(dir) ) == 0:
            # Clone repository
            self.logger.print("Cloning repository...")
            Repo.clone_from(url, dir)

            # Generate virtual env
            self.logger.print("Generating virtual environment...")
            os.system('python3 -m venv ' + dir + "/venv")
            return True
        else:
            self.logger.print("Pulling from repository...")
            repo = Repo(dir)
            current_sha = repo.head.object.hexsha
            repo.remotes.origin.pull()
            new_sha = repo.head.object.hexsha

            if current_sha != new_sha:
                return True

        self.logger.print("Nothing changed. Aborting tests.")
        return True

    def run_repo(self, rep):
        repo_name = self.get_repository_name(rep['rep_url'])
        self.logger = Logger(self.config['log_path'] + "/" + repo_name + "/" + rep['branch'])

        self.logger.print("Running: "+repo_name)
        path = self.get_local_store_path(rep['rep_url'], rep['branch'])
        self.logger.print("Path: " + path)

        should_run = self.has_changes_to_repository(rep['rep_url'], path)

        if should_run:
            self.get_repository_name(rep['rep_url'])
            self.logger.print("Activating virtual environment...")
            os.system('source '+path+'/'+rep['env_folder_path']+'/bin/activate')
            self.logger.print("Installing requirements...")
            os.system('pip3 install -r '+path+'/requirements.txt > /dev/null')

            try:
                # Run tests
                output = subprocess.getoutput('pytest -v '+path+"/"+rep['test_folder_path'])
                self.logger.print(output)
                print(output)

                if re.search(r'\bFAILED\b', output):
                    self.logger.print("One or more tests failed!", False, False)
                    print(Bcolors.WARNING + "One or more tests failed!" + Bcolors.ENDC)
                    self.send_mail("Test failed...", output, rep['mails'])
                else:
                    self.logger.print("Everything OK!", False, False)
                    print(Bcolors.OKGREEN + "Everything OK!" + Bcolors.ENDC)
            except:
                print("")

            self.logger.save_and_clear()

    def main(self):
        print("Python CI!")
        print("Loading config...")
        with open('setup.json') as f:
            self.config = json.load(f)
            print("Done!")
            print()

        for rep in self.config['repositories']:
            self.run_repo(rep)


if __name__ == "__main__":
    tester = Tester()
    tester.main()

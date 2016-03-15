from slackbot.bot import respond_to
import jenkinsapi
import urlparse
from jenkinsapi.jenkins import Jenkins
import os
import kube_deploy
import json
import time

jenkins_host = os.environ['JENKINS_SERVICE_HOST']
jenkins_port = os.environ['JENKINS_SERVICE_PORT']
external_jenkins_host = os.environ['JENKINS_EXT_HOST']
domain = os.environ['SERVICE_DOMAIN']
jenkins = Jenkins('http://{0}:{1}/'.format(jenkins_host, jenkins_port))


@respond_to('deploy (.*) from (.*)')
def deploy(message, branch, job):
    if build(message, branch, job):
        send_attachment(message, "Now I'm going to deploy {0} from {1}".format(branch, job))
        pod_file = './{0}-pod.yml'.format(job)
        service_file = './{0}-service.yml'.format(job)
        ret = kube_deploy.deploy_branch(pod_file, service_file, branch, domain)
        send_attachment(message, "I've deployed {0} from {1} to {2}".format(branch, job, ret),
                        title="Deployment Complete", url=ret, color='good')

@respond_to('build (.*) from (.*)')
def build(message, branch, job):
    send_attachment(message, "Ok, I'll build {0} from {1}".format(branch, job))
    job = jenkins.get_job(job)
    q = job.invoke(build_params={'branch': branch})
    q.block_until_building()
    build = q.get_build()
    url = q.get_build().baseurl
    new_url = urlparse.urlparse(url)
    new_url = new_url._replace(netloc="{0}:8080".format(external_jenkins_host))
    jenkins_url = new_url.geturl()
    send_attachment(message, "I've started the jenkins job at {0}".format(jenkins_url))
    build.block_until_complete()
    build = q.get_build()
    if build.is_good():
        send_attachment(message, "I've built {0} from {1} successfully.".format(branch, job),
                        title="Build Finished", url=jenkins_url, color='good')
        return True
    else:
        send_attachment(message, "Uh oh! I had problems building {0} from"
                                 " {1}".format(branch, job),
                        title="Build Finished", url=jenkins_url, color='danger')
        return False

@respond_to('open the pod bay doors')
def open_the_pod_bay_doors(msg):
    username = msg.channel._client.users[msg.body['user']][u'name']
    send_attachment(msg, "I'm sorry {0}. I'm afraid I can't do"
                         " that.".format(username), color="danger")

def send_attachment(message, reply, title=None, url=None, color=None):
    attachments = [{'fallback': reply,
                    'text': reply,
                    'color': color,
                    'title': title,
                    'title_link': url}]
    message.send_webapi('', json.dumps(attachments))


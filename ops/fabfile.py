from __future__ import with_statement

from fabric import Connection
from fabric import task
from patchwork.files import exists

from io import StringIO, BytesIO
import time
import boto3

GIT_MASTER_REPO = 'git@bitbucket.org:xcobbteam/xps-cloud.git'

EC2 = boto3.resource('ec2', region_name='us-east-1')
ELB = boto3.client('elb', region_name='us-east-1')
VPC = EC2.Vpc('vpc-2bdb7950') # vpc id

USER = "xco"
APP_NAME = "xps"

PROJECT_ROOT = '/home/%s/code/xps' % USER
CONF_ROOT = '/home/xco/conf'

VIRTUALENV = 'source /home/xco/.envs/xps/bin/activate'

APP_INSTANCES = []
ENV = 'prod'

# env.use_ssh_config = False
# # env.key_filename = "/home/xco/.ssh/id_rsa"
# env.timeout = 120
# env.migrate = True
# env.staging = False
# env.compile_templates = True
# env.no_downtime = False
# env.maintenance_mode = False
# env.cache_instances = None
# env.cache_master = None
# env.cache_slaves = []

def banner(message=None):
    print('===========================================================================\n\n')
    print('%s\n\n\n===========================================================================' % message if message else '')

def strip_alphanumeric(string):
    import re
    return re.sub(r'\W+', '', string)

@task
def deploy(environment, changeset_id=None, branch=None):
    banner('Preparing deploy')

    all_instances = VPC.instances.filter(Filters=[{'Name':'tag:app', 'Values':['%s' % APP_NAME]}, {'Name':'tag:env', 'Values': [ENV] }])
    APP_INSTANCES = all_instances.filter(Filters=[{'Name':'tag:type', 'Values':['app']}])

    for instance in APP_INSTANCES:
        banner('Deploying to application server %s' % instance.id)
        c = Connection(host=instance.private_ip_address, user='xco')

        # update environment file
        with open(r'%s/env_%s.conf' % (CONF_ROOT, ENV), 'r') as file:
            filedata = file.read()
        env_object = StringIO() # create a file-like object
        env_object.write(filedata) # write in our working env properties
        
        with c:
            c.put(env_object, '/home/%s/bin/.env' % USER) # push it to the remote server

            # update nginx settings
            _refresh_nginx_conf(c)

            # ensure we have pipenv installed
            with c.prefix(VIRTUALENV):
                c.run('pip install pipenv')

            # pull repo and establish symlink from changeset dir to live
            _pull(c, changeset_id, branch)
            recreate_sym_link(c, '/home/%s/bin/.env' % USER, '%s/live/xps_cloud/settings/.env' % PROJECT_ROOT, False)
            
            # install python packages
            with c.prefix(VIRTUALENV):
                c.run('cd %s/live && pipenv install' % PROJECT_ROOT)

            # perform migrations
            with c.prefix(VIRTUALENV):
                migrate(c)

            #uwsgi setup
            if not exists(c, '/etc/uwsgi/sites'):
                run('sudo mkdir -p /etc/uwsgi/sites')

            c.run('sudo pip3 install -U uwsgi')
            c.run('sudo cp %s/live/xps_cloud/%s.ini /etc/uwsgi/sites/%s.ini' % (PROJECT_ROOT, APP_NAME, APP_NAME))

            # systemd services
            c.sudo('cp %s/live/ops/uwsgi/uwsgi.service /etc/systemd/system' % PROJECT_ROOT)

            c.run('sudo systemctl daemon-reload') # reload configs
            c.run('sudo systemctl restart uwsgi') # restart uwsgi

            # trim the changesets
            c.run("cd /home/%s/code/%s/changesets/ sudo ls -t | sudo sed -e '1,20d' | sudo xargs -d '\n' rm -rf" % (USER, APP_NAME), warn=True)

def _make_tag_dict(ec2_object):
    """Given an tagable ec2_object, return dictionary of existing tags."""
    tag_dict = {}
    if ec2_object.tags is None: return tag_dict
    for tag in ec2_object.tags:
        tag_dict[tag['Key']] = tag['Value']
    return tag_dict

def recreate_sym_link(c, from_path, to_path, sudo=True):
    """ remove old symbolic link if necessary and create new one """

    if sudo:
        if exists(c, to_path):
            c.sudo('rm -f %s' % to_path)
        c.sudo('ln -sf %s %s' % (from_path, to_path))
    else:
        if exists(c, to_path):
            c.run('rm -f %s' % to_path)
        c.run('ln -sf %s %s' % (from_path, to_path))

def pull_changeset(c, changeset_id):
    c.run('cd %s/reference && git clone %s %s/changesets/%s' % (PROJECT_ROOT, GIT_MASTER_REPO, PROJECT_ROOT, changeset_id))
    c.run('cd %s/changesets/%s && git reset --hard %s' % (PROJECT_ROOT, changeset_id, changeset_id))

def migrate(c):
    c.run('cd /home/%s/code/%s/live/ && echo "yes" | python manage.py migrate' % (USER, APP_NAME))

def _pull(c, changeset_id=None, branch=None):
    if not exists(c, '%s' % PROJECT_ROOT):
        c.run('mkdir -p %s' % PROJECT_ROOT)

    if not exists(c, '%s/reference' % PROJECT_ROOT):
        c.run('git clone %s %s/reference' % (GIT_MASTER_REPO, PROJECT_ROOT))
    else:
        c.run('cd %s/reference && git pull' % PROJECT_ROOT)

    if changeset_id:
        if not exists(c, '%s/changesets/%s' % (PROJECT_ROOT, changeset_id)):
            pull_changeset(c, changeset_id)
    else:
        if branch:
            c.run('cd %s/reference && git checkout %s' % (PROJECT_ROOT, branch))
        else:
            c.run('cd %s/reference && git checkout master' % PROJECT_ROOT)

        c.run('cd %s/reference && git pull' % PROJECT_ROOT)

        result = c.run('cd %s/reference && git rev-parse HEAD' % PROJECT_ROOT)
        changeset_id = result.stdout.split(' ')[0].replace('\n', '') # get the changeset from the run command, clearing out end-of-line

        if not exists(c, '%s/changesets/%s' % (PROJECT_ROOT, changeset_id)):
            pull_changeset(c, changeset_id)

    recreate_sym_link(c, '%s/changesets/%s' % (PROJECT_ROOT, changeset_id), '%s/live' % (PROJECT_ROOT), True)

def _refresh_nginx_conf(c):
    banner('Refreshing nginx configuration')
    c.run('sudo apt update')
    c.run('sudo apt -y install nginx')

    c.put('%s/ops/nginx/app_nginx_%s.conf' % (PROJECT_ROOT, ENV), '/home/%s/nginx_conf' % USER)
    c.sudo('mv /home/%s/nginx_conf /etc/nginx/sites-available/%s' % (USER, USER))

    recreate_sym_link(c, '/etc/nginx/sites-available/%s' % USER, '/etc/nginx/sites-enabled/%s' % USER, True)
    c.run('sudo /etc/init.d/nginx restart')

def disable_login():
    toggle_login(True)

def enable_login():
    toggle_login(False)
"""
This is the main management script for provisioning and managing the LocalWiki server infrastructure.

==== Do this first ====

* Install vagrant >= 1.3.3
* Then:

    $ mkdir vagrant_localwiki
    $ mv localwiki vagrant_localwiki  # Move repository inside
    $ cd vagrant_localwiki
    $ ln -s localwiki/vagrant/Vagrantfile .
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r localwiki/fabric/requirements.txt

==== For development ====

This script will get you up and running with a development instance of the
LocalWiki servers.  Set up the requirements (above), then::

    $ cd vagrant_localwiki
    $ vagrant up  # Create and run vagrant instance
    $ cd localwiki/fabric/
    $ fab vagrant setup_dev  # Provision and set up for vagrant:

You now have a complete vagrant setup with the LocalWiki servers
running inside it.  To do development, you'll want to do something
like::

    $ cd vagrant_localwiki
    $ vagrant ssh

Then, when ssh'ed into vagrant::

    $ source /srv/localwiki/env/bin/activate
    $ DJANGO_DEBUG=1 localwiki-manage runserver 0.0.0.0:8000

You can then access the development server at http://localhost:8082
on your local machine.  Hack on the code that lives inside of
vagrant_localwiki/localwiki.

Apache, which runs the production-style setup, will be accessible at
https://127.0.0.1:8443, but you should use :8082, the development server,
for most active work as it will automatically refresh.

To test a full production-style deploy in vagrant::

    $ cd localwiki/fabric
    $ fab vagrant deploy:local=True

Then visit the production server, https://127.0.0.1:8443, on your
local machine.  The 'deploy:local' flag tells us to use your local
code rather than a fresh git checkout.

==== Testing ====

To run tests:

    $ fab vagrant run_tests

Alternatively, you can just have travis-ci run the tests for you on commit
on a branch.

==== Internationalization note ====

Different languages are placed on subdomains, so if you're testing out
language stuff then it's best to set up language-level subdomains on your
`localhost` E.g. add `dev.localhost`, `ja.dev.localhost`, `de.dev.localhost`
to `/etc/hosts` and set `dev.localhost` as your public_hostname in your
`config_secrets/secrets.json`.

==== EC2 ====

To provision a new EC2 instance::

    $ fab create_ec2 provision

==== Deploying to LocalWiki.org production ====

After provisioning, make sure you edit `roledefs` below to point
to the correct hosts. You'll also need the master LocalWiki credentials
(see below).  Then::

    $ fab production deploy

"""

import os
import sys
import random
import time
import shutil
import json
import datetime
from copy import copy
import string
from collections import defaultdict
from contextlib import contextmanager as _contextmanager
from fabric.api import *
from fabric.contrib.files import upload_template, exists
from fabric.network import disconnect_all
from fabric.api import settings
import boto.ec2
import htpasswd
from ilogue import fexpect

import logging
logging.basicConfig(level=logging.INFO)

####################################################################
#  Ignore `config_secrets` for development usage.
# 
#  Notes for folks deploying code to **localwiki.org (production)**:
#  
#    We will likely automate all deployments, making developer
#    access to config secrets unneccessary for all but a very small
#    handful of people.
#
#    0. Ask a devops/sysadmin for the config secrets, if necessary.
#    1. cp config_secrets.example/ to config_secrets/
#    2. Edit the secrets.json and other files accordingly.
#    3. Ensure you have valid SSL certificates in config_secrets/ssl/
#       in the format:
#           * config_secrets/ssl/<hostname>/
#           * config_secrets/ssl/<hostname>/<hostname>.crt
#           * config_secrets/ssl/<hostname>/<hostname>.key
#           * config_secrets/ssl/<hostname>/intermediate.crt (if present)
#  
#  You can provision without setting up these secrets, but this will
#  enable non-self-signed SSL, Sentry, and other stuff as we add it.
####################################################################

####################################################################
# You'll want to edit this after provisioning:
####################################################################

roledefs = {
    'web': ['ubuntu@localwiki.org'],
}


def get_ec2_ami(region):
    # From http://cloud-images.ubuntu.com/releases/precise/release/

    # These are 64-bit, EBS-root-volume instances running
    # Ubuntu 12.04 LTS.
    images = {
        'us-west-1': 'ami-ecd8efa9',
        'us-west-2': 'ami-30079e00',
        'us-east-1': 'ami-69f5a900',
        # ..add others here if you wish
    }
    return images[region]

####################################################################
# Notes to self:
#
# After creating an EC2 instance, may want to create an IP:
#
# ec2-allocate-address
# ec2-associate-address -i <instance id> <ip address>
# 
# and set up a reverse DNS:
# https://portal.aws.amazon.com/gp/aws/html-forms-controller/contactus/ec2-email-limit-rdns-request
#
####################################################################

_config_path = 'config_secrets'
def config_path(path):
    global _config_path
    _config_path = path

config_secrets = {}

def setup_config_secrets():
    global config_secrets

    if not os.path.exists(_config_path):
        shutil.copytree('config_secrets.example', _config_path)
    config_secrets = defaultdict(lambda : None)
    jsecrets = json.load(open(os.path.join(_config_path, 'secrets.json')))
    if env.host_type in jsecrets:
        secrets = jsecrets[env.host_type]
    else:
        secrets = jsecrets['*']
    config_secrets.update(secrets)

def save_config_secrets():
    global config_secrets

    jsecrets = json.load(open(os.path.join(_config_path, 'secrets.json')))
    if env.host_type in jsecrets:
        jsecrets[env.host_type] = config_secrets
    else:
        jsecrets['*'] = config_secrets
    f = open(os.path.join(_config_path, 'secrets.json'), 'w')
    json.dump(jsecrets, f, indent=4)
    f.close()

env.host_type = None

########################
# Defaults             #
########################

env.localwiki_root = '/srv/localwiki'
env.src_root = os.path.join(env.localwiki_root, 'src')
env.virtualenv = os.path.join(env.localwiki_root, 'env')
env.data_root = os.path.join(env.virtualenv, 'share', 'localwiki')
env.branch = 'master'
env.git_hash = None
env.keepalive = 300

def production():
    # Use the global roledefs
    env.roledefs = roledefs
    if not env.roles:
        env.roles = ['web']
    env.host_type = 'production'

    setup_config_secrets()
 
def vagrant():
    # connect to the port-forwarded ssh
    env.roledefs = {
        'web': ['vagrant@127.0.0.1:2222']
    }
    if not env.roles:
        env.roles = ['web']
    env.host_type = 'vagrant'

    setup_config_secrets()
    # We assume that this fabfile is inside of the vagrant
    # directory, two subdirectories deep.  See dev HOWTO
    # in main docstring.
    with lcd('../../'):
        # use vagrant ssh key
        result = local('vagrant ssh-config | grep IdentityFile', capture=True)
    env.key_filename = result.split()[1].strip('"')

def test_server():
    env.host_type = 'test_server'
    setup_config_secrets()

def ec2():
    env.host_type = 'ec2'
    env.user = 'ubuntu'

    setup_config_secrets()

    env.aws_access_key_id = config_secrets.get('aws_access_key_id', None) or os.getenv('AWS_ACCESS_KEY_ID')
    env.aws_secret_access_key = config_secrets.get('aws_secret_access_key', None) or os.getenv('AWS_SECRET_ACCESS_KEY')
    env.aws_security_token = config_secrets.get('aws_security_token', None) or os.getenv('AWS_SECURITY_TOKEN')
    env.ec2_region = config_secrets['ec2_region']
    env.ec2_instance_id = config_secrets.get('ec2_instance_id', None)
    env.backup_ec2_region = config_secrets['backup_ec2_region']
    env.ec2_security_group = config_secrets['ec2_security_group']
    env.ec2_key_name = config_secrets['ec2_key_name']
    env.key_filename = config_secrets['ec2_key_filename']

def setup_dev():
    """
    Provision and set up for development on vagrant.
    """
    provision()
    # Use our vagrant shared directory instead of the
    # git checkout.
    sudo('rm -rf /srv/localwiki/src')
    sudo('ln -s /vagrant/localwiki /srv/localwiki/src', user='www-data')
    update(local=True)

def get_context(env):
    d = {}
    d.update(config_secrets)
    d.update(dict(env))
    return d

@_contextmanager
def virtualenv():
    with prefix('source %s/bin/activate' % env.virtualenv):
        yield

def setup_postgres(test_server=False):
    sudo('service postgresql stop')

    # Move the data directory to /srv/
    sudo('mkdir -p /srv/postgres')
    if not exists('/srv/postgres/data'):
        sudo('mv /var/lib/postgresql/9.1/main /srv/postgres/data')
    sudo('chown -R postgres:postgres /srv/postgres')

    # Add our custom configuration
    if env.host_type != 'test_server':
        put('config/postgresql/postgresql.conf', '/etc/postgresql/9.1/main/postgresql.conf', use_sudo=True)
    else:
        put('config/postgresql/postgresql_test.conf', '/etc/postgresql/9.1/main/postgresql.conf', use_sudo=True)

    set_postgresql_shmmax()
    sudo('service postgresql start')

def set_postgresql_shmmax():
    # Increase system shared memory limits
    # (allow for 768MB shared_buffer in PostgreSQL)
    shmmax = 1633894400
    shmall = int(shmmax * 1.0 / 4096)
    sudo('echo "%s" > /proc/sys/kernel/shmmax' % shmmax)
    sudo('echo "%s" > /proc/sys/kernel/shmall' % shmall)
    sudo('echo "\nkernel.shmmax = %s\nkernel.shmall = %s" > /etc/sysctl.conf' % (shmmax, shmall))
    sudo('sysctl -p')

def setup_jetty():
    put("config/default/jetty", "/etc/default/", use_sudo=True)
    sudo("sed -i 's/NO_START=1/NO_START=0/g' /etc/default/jetty")
    sudo("cp /etc/solr/conf/schema.xml /etc/solr/conf/schema.xml.orig")
    put("config/solr_schema.xml", "/etc/solr/conf/schema.xml", use_sudo=True)
    put("config/daisydiff.war", "/var/lib/jetty/webapps", use_sudo=True)
    sudo("service jetty stop")
    sudo("service jetty start")

def setup_memcached():
    put("config/memcached/memcached.conf", "/etc/memcached.conf", use_sudo=True)
    sudo("service memcached restart")

def install_system_requirements():
    # Update package list
    sudo('apt-get update')
    sudo('apt-get -y install python-software-properties')

    # Custom PPA for Solr 3.5
    sudo("apt-add-repository -y ppa:webops/solr-3.5")

    # Need GDAL >= 1.10 and PostGIS 2, so we use this
    # PPA.
    sudo('apt-add-repository -y ppa:ubuntugis/ubuntugis-unstable')
    sudo('apt-get update')

    # Ubuntu system packages
    base_system_pkg = [
        'git',
        'unattended-upgrades',
    ] 
    system_python_pkg = [
        'python-dev',
        'python-setuptools',
        'python-psycopg2',
        'python-lxml',
        'python-imaging',
        'python-pip',
    ]
    solr_pkg = ['solr-jetty', 'default-jre-headless']
    apache_pkg = ['apache2', 'libapache2-mod-wsgi']
    postgres_pkg = ['gdal-bin', 'proj', 'postgresql-9.1-postgis-2.1', 'postgresql-server-dev-all']
    memcached_pkg = ['memcached']
    varnish_pkg = ['varnish']
    web_pkg = ['yui-compressor']
    monitoring = ['munin', 'munin-node']

    if env.host_type == 'test_server':
        # Travis won't start the redis server correctly
        # if it's installed like this. So we skip it
        # and use their default.
        redis_pkg = []
    else:
        redis_pkg = ['redis-server']

    mailserver_pkg = ['postfix']
    packages = (
        base_system_pkg + 
        system_python_pkg +
        solr_pkg +
        apache_pkg +
        postgres_pkg +
        memcached_pkg +
        varnish_pkg +
        web_pkg +
        redis_pkg + 
        mailserver_pkg +
        monitoring
    )
    sudo('DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -y --force-yes install %s' % ' '.join(packages))

def init_postgres_db():
    # Generate a random password, for now.
    if not config_secrets['postgres_db_pass']:
        config_secrets['postgres_db_pass'] = ''.join([random.choice(string.letters + string.digits) for i in range(40)])
    sudo("""psql -d template1 -c "CREATE USER localwiki WITH PASSWORD '%s'" """ % config_secrets['postgres_db_pass'], user='postgres')
    sudo("""psql -d template1 -c "ALTER USER localwiki CREATEDB" """, user='postgres')
    sudo("createdb -E UTF8 -O localwiki localwiki", user='postgres')
    # Init PostGIS
    sudo('psql -d localwiki -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"', user='postgres')
    sudo('psql -d localwiki -c "GRANT SELECT ON geometry_columns TO localwiki; GRANT SELECT ON geography_columns TO localwiki; GRANT SELECT ON spatial_ref_sys TO localwiki;"', user='postgres')

def update_django_settings():
    upload_template('config/localsettings.py',
        os.path.join(env.virtualenv, 'share', 'localwiki', 'conf'),
        context=get_context(env), use_jinja=True, use_sudo=True)

def update_apache_settings(restart=True):
    # Get SSL information
    get_ssl_info()

    # Create our extra config file directory if it doesn't already exist
    sudo('mkdir -p /etc/apache2/extra-conf')

    get_ssl_info()

    upload_template('config/apache/extra-conf/main_router.conf', '/etc/apache2/extra-conf/main_router.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/localwiki', '/etc/apache2/sites-available/localwiki',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/apache2.conf', '/etc/apache2/apache2.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/ports.conf', '/etc/apache2/ports.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/bad-bots', '/etc/apache2/conf.d/bad-bots',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/extra-conf/ssl.conf', '/etc/apache2/extra-conf/ssl.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/apache/extra-conf/localwiki_certs.conf', '/etc/apache2/extra-conf/localwiki_certs.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)

    if config_secrets.get('localwiki_main_production', False):
        upload_template('config/apache/aaaa_old_localwiki', '/etc/apache2/sites-available/aaaa_old_localwiki',
            context=get_context(env), use_jinja=True, use_sudo=True)

    upload_template('config/logrotate.d/apache2', '/etc/logrotate.d/apache2',
        context=get_context(env), use_jinja=True, use_sudo=True)

    if restart:
        sudo('service apache2 restart')

def init_localwiki_install():
    init_postgres_db()

    # Update to latest virtualenv.
    sudo('pip install --upgrade virtualenv')

    # Create virtualenv
    if env.host_type == 'test_server':
        # Annoying Travis issue. https://github.com/travis-ci/travis-ci/issues/2338
        run('virtualenv -p /usr/bin/python2.7 --system-site-packages %s' % env.virtualenv)
    else:
        run('virtualenv --system-site-packages %s' % env.virtualenv)

    with virtualenv():
        with cd(env.src_root):
            # Force update to setuptools
            run('pip install --upgrade setuptools')

            # Install core localwiki module as well as python dependencies
            run('pip install -r requirements.txt')
            run('python setup.py develop')

            # Set up the default media, static, conf, etc directories
            run('mkdir -p %s/share' % env.virtualenv)
            put('config/defaults/localwiki', os.path.join(env.virtualenv, 'share'))

            # Install Django settings template
            if not config_secrets['django_secret_key']:
                config_secrets['django_secret_key'] = ''.join([
                    random.choice('abcdefghijklmnopqrstuvwxyz0123456789!@$%^&*(-_=+)')
                    for i in range(50)
                ])
            update_django_settings()

            run('localwiki-manage setup_all')

def setup_repo():
    sudo('mkdir -p %s' % env.localwiki_root)
    sudo('chown -R %s:%s %s' % (env.user, env.user, env.localwiki_root))
    if not exists(env.src_root):
        run('git clone https://github.com/localwiki/localwiki-backend-server.git %s' % env.src_root)
    switch_branch(env.branch)

def switch_branch(branch):
    with cd(env.src_root):
        run('git checkout %s' % branch)

def install_ssl_certs():
    # Install our SSL certs for apache
    sudo('mkdir -p /etc/apache2/ssl')
    sudo('mkdir -p /etc/apache2/extra-ssl')
    sudo('chown -R www-data:www-data /etc/apache2/ssl')
    sudo('chmod 700 /etc/apache2/ssl')

    with settings(warn_only=True):
        # We only move over our SSL certs if we're running in production:
        if env.host_type == 'production':
            put('config_secrets/ssl/*', '/etc/apache2/ssl/', use_sudo=True)
            put('config_secrets/extra-ssl/*', '/etc/apache2/extra-ssl/', use_sudo=True)

    # If we have no actual SSL certs, let's generate a self-signed one
    # for testing purposes.
    ssl_files = sudo('ls -1 /etc/apache2/ssl/', user='www-data').strip().split('\n')
    if len(ssl_files) <= 1:
        public_hostname = get_context(env)['public_hostname']
        # Remove port, if in hostname:
        public_hostname = public_hostname.split(':')[0]
        sudo('mkdir /etc/apache2/ssl/%s' % public_hostname, user='www-data')
        with cd('/etc/apache2/ssl/%s' % public_hostname):
            sudo('openssl req -x509 -nodes -days 1825 -newkey rsa:2048 '
                 '-keyout %(hostname)s.key -out %(hostname)s.crt '
                 '-subj "/C=US/ST=California/L=San Francisco/O=Self-signed cert/CN=*.%(hostname)s"' %
                    {'hostname': public_hostname}, user='www-data')

def get_ssl_info():
    """
    Figure out what the SSL info is based on what's in the ssl/ dir.
    """
    if (getattr(env, 'ssl_name', None) and getattr(env, 'ssl_key', None) and getattr(env, 'ssl_cert', None)):
        # Already have the info
        return
    ssl_name = os.path.split(sudo('ls -d /etc/apache2/ssl/*').strip())[1]
    env.ssl_name = ssl_name
    ssl_files = sudo('ls /etc/apache2/ssl/%s' % ssl_name).split()
    crt = None
    key = None
    intermediate = None
    for fname in ssl_files:
        if fname.endswith('.crt') and fname != 'example.org.crt':
            crt = fname
        if fname.endswith('.key') and fname != 'example.org.key':
            key = fname
        if fname.endswith('intermediate.crt'):
            intermediate = fname
    env.ssl_key = key
    env.ssl_cert = crt
    env.ssl_intermediate = intermediate

def setup_apache_monitoring():
    sudo('mkdir -p /root/cron/')
    upload_template('config/root/cron/monitor_and_restart_apache.py', '/root/cron/monitor_and_restart_apache.py',
        context=get_context(env), use_jinja=True, use_sudo=True)
    sudo('chmod +x /root/cron/monitor_and_restart_apache.py')
    upload_template('config/cron.d/monitoring', '/etc/cron.d/monitoring',
        context=get_context(env), use_jinja=True, use_sudo=True)
    sudo('chown root:root /etc/cron.d/monitoring')
    sudo('chmod 644 /etc/cron.d/monitoring')

def setup_apache():
    with settings(hide('warnings', 'stdout', 'stderr')):
        # Enable mod_wsgi, mod_headers, mod_rewrite
        sudo('a2enmod wsgi')
        sudo('a2enmod headers')
        sudo('a2enmod rewrite')
        sudo('a2enmod expires')
        sudo('a2enmod proxy')
        sudo('a2enmod proxy_http')
        sudo('a2enmod ssl')

        # Disable CGI because it can be insecure
        sudo('a2dismod cgi')

        # Install localwiki.wsgi
        upload_template('config/localwiki.wsgi', os.path.join(env.localwiki_root),
            context=env, use_jinja=True, use_sudo=True)

        # Allow apache to save uploads, etc
        sudo('chown -R www-data:www-data %s' % os.path.join(env.localwiki_root))

        # Disable default apache site
        if exists('/etc/apache2/sites-enabled/000-default'):
           sudo('a2dissite default')

        install_ssl_certs()
        update_apache_settings()

        if env.host_type == 'production':
            setup_apache_monitoring()

def setup_permissions():
    # Add the user we run commands with to the apache user group
    sudo('usermod -a -G www-data %s' % env.user)
    sudo('chmod g+s %s' % env.localwiki_root)

    # Allow apache to read all the files in the localwiki root
    sudo('chown -R www-data:www-data %s' % env.localwiki_root)
    # .. but don't let other users view env/, src/.
    # Apache needs 775 access to the localwiki.wsgi script, though.
    sudo('chmod -R 770 %s %s' % (env.virtualenv, env.src_root))

def setup_mapserver():
    """
    Enable map-a.localwiki.org, map-b.localwiki.org, map-c.localwiki.org as
    cached proxies to cloudmade tiles.
    """
    # NOTE: Currently disabled, as we now use MapBox for our tiles. MapBox
    # forbids, in their ToS, caching their tiles, so we don't cache here.
    # However, we may ask them about allowing us an exemption here, so this
    # may be re-enabled soon:
    return

    upload_template('config/apache/map', '/etc/apache2/sites-available/map',
            context=get_context(env), use_jinja=True, use_sudo=True)
    sudo('a2ensite map')
    sudo('service apache2 restart')

def setup_varnish():
    if not config_secrets['varnish_secret']:
        config_secrets['varnish_secret'] = ''.join([
            random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            for i in range(50)
        ])
        # Now, write the varnish secret file
        sudo('echo %s > /etc/varnish/secret' % config_secrets['varnish_secret'])
        update_django_settings()
    sudo('mkdir -p /mnt/varnish/')
    update_varnish_settings()

def update_varnish_settings():
    # Add our custom configuration
    if env.host_type == 'test_server' or env.host_type == 'varnish':
        put('config/varnish/varnish.test', '/etc/default/varnish', use_sudo=True)
    else:
        put('config/varnish/varnish', '/etc/default/varnish', use_sudo=True)
    upload_template('config/varnish/default.vcl', '/etc/varnish/default.vcl',
            context=get_context(env), use_jinja=True, use_sudo=True)
    sudo('service varnish restart')

def clear_caches():
    """
    Clears out the primary caches. Use the `clear_caches` keyword to `deploy()`
    to activate this during a deploy. Needed when the HTML or appserver UI changes.

    Doesn't clear -all- caching. Some stuff, such as thumbnail information and 'page cards',
    are kept in a longer-term cache.
    """
    sudo("service memcached restart", pty=False)
    sudo("service varnish restart", pty=False)
_clear_caches = clear_caches

def add_ssh_keys():
    run('mkdir -p ~/.ssh && chmod 700 ~/.ssh')
    run('touch ~/.ssh/authorized_keys')
    run('mkdir ssh_to_add')
    put('config_secrets/ssh/*', 'ssh_to_add/')
    run('cat ~/ssh_to_add/* >> ~/.ssh/authorized_keys')
    run('rm -rf ~/ssh_to_add')

def attach_ebs_volumes():
    """
    Attach EBS volumes.
    """
    print "Attaching EBS volume inside of instance.."
    sudo('mkfs -t ext3 /dev/xvdh')
    sudo('mkdir -p /srv/')
    sudo('echo "/dev/xvdh       /srv    auto    defaults,nobootwait 0       2 " >> /etc/fstab')
    sudo('mount -a')

def create_ec2(ami_id=None, instance_type='m1.medium'):
    ec2()

    if not ami_id:
        ami_id = get_ec2_ami(env.ec2_region)

    conn = boto.ec2.connect_to_region(env.ec2_region,
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_secret_access_key,
        security_token=env.aws_security_token,
    )
    # Don't delete root EBS volume on termination
    root_device = boto.ec2.blockdevicemapping.BlockDeviceType(
        delete_on_termination=False,
    )
    block_device_map = boto.ec2.blockdevicemapping.BlockDeviceMapping()
    block_device_map['/dev/sda1'] = root_device
    res = conn.run_instances(ami_id,
        key_name=env.ec2_key_name,
        instance_type=instance_type,
        block_device_map=block_device_map,
        security_groups=[env.ec2_security_group]
    )

    instance = res.instances[0]
    exact_region = instance.placement

    # Create EBS volume for data storage
    print "Waiting for EBS volume to be created.."
    data_vol = conn.create_volume(300, exact_region)
    cur_vol = conn.get_all_volumes([data_vol.id])[0]
    while cur_vol.status != 'available':
        time.sleep(1)
        print ".",
        sys.stdout.flush()
        cur_vol = conn.get_all_volumes([data_vol.id])[0]

    print "Spinning up instance. Waiting for it to start. "
    while instance.state != 'running':
        time.sleep(1)
        instance.update()
        print ".",
        sys.stdout.flush()
    print "Instance running."
    print "Hostname: %s" % instance.public_dns_name

    print "Attaching EBS volume to instance at AWS level.."
    conn.attach_volume (data_vol.id, instance.id, "/dev/sdh")

    print "Waiting for instance to finish booting up. "
    time.sleep(20)
    print "Instance ready to receive connections. "
    env.hosts = [instance.public_dns_name]

def create_swap():
    put('config/init/create_swap.conf', '/etc/init/create_swap.conf', use_sudo=True)
    sudo('start create_swap')

def setup_ec2():
    """
    Things we need to do to set up the EC2 instance /after/
    we've created the instance and have its hostname.
    """
    attach_ebs_volumes()
    create_swap()

def setup_celery():
    if env.host_type == 'vagrant':   
        put('config/init/celery_vagrant.conf', '/etc/init/celery.conf', use_sudo=True)
    else:
        put('config/init/celery.conf', '/etc/init/celery.conf', use_sudo=True)
    sudo('touch /var/log/celery.log')
    sudo('chown www-data:www-data /var/log/celery.log')
    sudo('chmod 660 /var/log/celery.log')
    sudo('service celery start')

def setup_unattended_upgrades():
    """
    Enable unattended Ubuntu package updates.

    For now, this is just set to security updates (the Ubuntu defaults).
    """
    upload_template('config/apt/apt.conf.d/10periodic', '/etc/apt/apt.conf.d/10periodic',
        context=get_context(env), use_jinja=True, use_sudo=True)

def setup_hostname():
    public_hostname = get_context(env)['public_hostname']
    sudo('hostname %s' % public_hostname)
    upload_template('config/hostname/hostname', '/etc/hostname',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/hostname/hosts', '/etc/hosts',
        context=get_context(env), use_jinja=True, use_sudo=True)

def setup_munin():
    upload_template('config/munin/apache.conf', '/etc/munin/apache.conf',
        context=get_context(env), use_jinja=True, use_sudo=True)

    if not config_secrets['munin_auth_info']:
        # Generate a random password for now.
        config_secrets['munin_auth_info'] = {'munin': ''.join([random.choice(string.letters + string.digits) for i in range(40)])}

    if not os.path.exists('config_secrets/munin-htpasswd'):
        f = open('config_secrets/munin-htpasswd', 'w')
        f.close()

    with htpasswd.Basic("config_secrets/munin-htpasswd") as userdb:
        for username, password in config_secrets['munin_auth_info'].iteritems():
            if username not in userdb:
                userdb.add(username, password)
            else:
                userdb.change_password(username, password)

    upload_template('config_secrets/munin-htpasswd', '/etc/munin/munin-htpasswd',
        context=get_context(env), use_jinja=True, use_sudo=True) 

def setup_mailserver():
    upload_template('config/postfix/main.cf', '/etc/postfix/main.cf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/postfix/master.cf', '/etc/postfix/master.cf',
        context=get_context(env), use_jinja=True, use_sudo=True)
    upload_template('config/postfix/mailname', '/etc/mailname',
        context=get_context(env), use_jinja=True, use_sudo=True)
    sudo('service postfix restart')

def setup_db_based_cache():
    with virtualenv():
        sudo('localwiki-manage createcachetable django_db_cache_table', user='www-data')

def provision():
    if env.host_type == 'vagrant':
        fix_locale()

    if env.host_type == 'ec2':
        setup_ec2()

    add_ssh_keys()
    install_system_requirements()
    setup_unattended_upgrades()
    setup_hostname()
    setup_mailserver()
    setup_munin()
    setup_postgres()
    setup_memcached()
    setup_jetty()
    setup_repo()
    init_localwiki_install()
    setup_db_based_cache()
    setup_permissions() 
    setup_celery()
    setup_varnish()

    setup_apache()

    #setup_mapserver()
    save_config_secrets()

def run_tests():
    # Must be superuser to run tests b/c of PostGIS requirement? Ugh..
    # XXX TODO: Fix this, somehow.  django-nose + pre-created test db?
    sudo("""psql -d postgres -c "ALTER ROLE localwiki SUPERUSER" """, user='postgres')
    with virtualenv():
        sudo('localwiki-manage test regions pages maps tags versioning diff ckeditor redirects users api utils', user='www-data')
    sudo("""psql -d postgres -c "ALTER ROLE localwiki NOSUPERUSER" """, user='postgres')

def branch(name):
    env.branch = name

def git_hash(s):
    env.git_hash = s

def update_code():
    with cd(env.src_root):
        sudo("git fetch origin", user="www-data")
        stash_str = sudo("git stash", user="www-data")
        if env.git_hash:
            sudo("git reset --hard %s" % env.git_hash, user="www-data")
        else:
            sudo("git reset --hard origin/%s" % env.branch, user="www-data")
        print 'stash_str', stash_str
        if stash_str.strip() != 'No local changes to save':
            sudo("git stash pop", user="www-data")

def rebuild_virtualenv():
    with cd(env.localwiki_root):
        sudo("virtualenv --system-site-packages env", user="www-data")

def touch_wsgi():
    # Touching the deploy.wsgi file will cause apache's mod_wsgi to
    # reload all python modules having to restart apache.  This is b/c
    # we are running django.wsgi in daemon mode.
    with cd(env.localwiki_root):
        sudo("touch localwiki.wsgi")

def update(local=False):
    if not local:
        update_code()
    # rebuild_virtualenv()  # rebuild since it may be out of date and broken
    with cd(env.src_root):
        with virtualenv():
            sudo("python setup.py clean --all", user="www-data")
            sudo("rm -rf dist localwiki.egg-info", user="www-data")
            update_django_settings()
            sudo('pip install -r requirements.txt')
            sudo("python setup.py develop", user="www-data")
            #sudo("python setup.py install")
            sudo("localwiki-manage setup_all", user="www-data")

def note_start_deploy():
    with cd(env.localwiki_root):
        sudo("touch .in_deploy")

def note_end_deploy():
    with cd(env.localwiki_root):
        sudo("rm .in_deploy")

def deploy(local=False, update_configs=None, clear_caches=None):
    """
    Update the code (git pull) and restart / rebuild all needed services.

    Args:
        local: If True, don't update the repository on the server, but
            otherwise deploy everything else.  This is useful if you're
            doing local development via vagrant, where you don't want to
            pull down from git -- and instead want to run using your
            local changes.
        update_configs: If True, update Apache, etc configuration files.
             Default: False
        clear_caches: If True, clear primary caches after deploy.
             Default: False
    """
    if env.host_type == 'vagrant':
        # Annoying vagrant virtualbox permission issues
        sudo('chmod -R 770 %s' % env.virtualenv)
    if env.host_type == 'vagrant' and local:
        if update_configs is None and clear_caches is None:
            # We assume that for a local, varnish-based deploy
            # we'd like to re-init all configs and restart
            # caches on each deploy, as code is probably
            # changing here more quickly.
            update_configs, clear_caches = True, True
    update_configs = (False if update_configs is None else update_configs)
    clear_caches = (False if clear_caches is None else clear_caches)

    note_start_deploy()
    try:
        update(local=local)
        if update_configs:
            setup_jetty()
            update_apache_settings()
            update_varnish_settings()
            setup_memcached()
            # In case celery apps have changed:
            sudo('service celery restart')
        touch_wsgi()
        if clear_caches:
            _clear_caches()
    except Exception as e:
        note_end_deploy()
        raise e
    else:
        note_end_deploy()

def create_ami():
    """
    Creates an AMI from our primary instance.

    Includes the boot EBS volume as well as the
    data EBS volume.
    """
    ec2()
    conn = boto.ec2.connect_to_region(env.ec2_region,
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_secret_access_key,
        security_token=env.aws_security_token,
    )
    ami_id = conn.create_image(env.ec2_instance_id, 'localwiki-main-%s' % (int(time.time())), no_reboot=True)
    ami = conn.get_all_images(image_ids=[ami_id])[0]
    print "Waiting for instance AMI to be created"
    while ami.state != 'available':
        print '.',
        sys.stdout.flush()
        time.sleep(5)
        ami = conn.get_all_images(image_ids=[ami_id])[0]
    return ami

def create_ami_and_move_to_backup_region():
    in_region_ami = create_ami()

    conn = boto.ec2.connect_to_region(env.backup_ec2_region,
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_secret_access_key,
        security_token=env.aws_security_token,
    )
    copied_image = conn.copy_image(env.ec2_region, in_region_ami.id)
    ami = conn.get_all_images(image_ids=[copied_image.image_id])[0]
    print "Waiting for instance AMI to be copied"
    while ami.state != 'available':
        print '.',
        sys.stdout.flush()
        time.sleep(5)
        ami = conn.get_all_images(image_ids=[ami.id])[0]
    return ami

def run_backup(instance_type='m1.medium'):
    """
    You'll need to update the `ec2_instance_id` in your secrets.json for this to work.
    """
    ec2()

    ami = create_ami_and_move_to_backup_region()

    conn = boto.ec2.connect_to_region(env.backup_ec2_region,
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_secret_access_key,
        security_token=env.aws_security_token,
    )

    res = conn.run_instances(ami.id,
        placement=env.backup_ec2_region + 'a',
        key_name=env.ec2_key_name,
        instance_type=instance_type,
        security_groups=[env.ec2_security_group]
    )
    instance = res.instances[0]
    exact_region = instance.placement

    print "Spinning up backup instance. Waiting for it to start. "
    while instance.state != 'running':
        time.sleep(1)
        instance.update()
        print ".",
        sys.stdout.flush()
    print "Instance running."
    print "Hostname: %s" % instance.public_dns_name

    print "Waiting for instance to finish booting up. "
    time.sleep(20)
    print "Instance ready to receive connections. "

    env.roledefs['backup_host'] = ['ubuntu@' + instance.public_dns_name]
    env.host_string = 'ubuntu@' + instance.public_dns_name

    collect_backup(instance)

@roles('backup_host')
def collect_backup(instance):
    # Create backup directory on ephemeral storage
    sudo('mkdir -p /mnt/backup')
    sudo('chown -R postgres:postgres /mnt/backup')

    # Dump postgres
    sudo('pg_dumpall > /mnt/backup/pg_dumpall.sql', user='postgres')

    # Remove useless cache files
    sudo('rm -rf /srv/localwiki/env/share/localwiki/media/cache')

    # Link our data directory
    sudo('ln -s /srv/ /mnt/backup/srv')

    # Set permissions so material can be easily downloaded
    sudo('chown -R ubuntu:ubuntu /mnt/backup')
    sudo('chown -R ubuntu:ubuntu /srv/')

    print "*************************"
    print "Backup prep complete! Just run this command to download the backup on an off-site machine:"
    print ""
    print "rsync -arvzL --stats --progress %s:/mnt/backup backup-%s" % (env.roledefs['backup_host'][0], int(time.time()))
    print "NOTE: The backup is *not* encrypted, so make sure to store it on encrypted storage or GPG-encrypt it."
    print "*************************"
    print ""
    print ""
    print "*************************"
    print "AFTER downloading the backup, run the following to clean up the temporary EC2 resources:"
    print "fab backup_done:%s" % instance.id
    print "*************************"
    print ""

def backup_done(instance_id):
    ec2()

    conn = boto.ec2.connect_to_region(env.backup_ec2_region,
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_secret_access_key,
        security_token=env.aws_security_token,
    )

    reservation = conn.get_all_instances(instance_ids=[instance_id])[0]
    instance = reservation.instances[0]
    volume_ids = []
    for k in instance.block_device_mapping:
        volume_ids.append(instance.block_device_mapping[k].volume_id)
    volumes = conn.get_all_volumes(volume_ids=volume_ids)

    print "Terminating the temporary EC2 backup instance"
    instance.terminate()
    time.sleep(5)

    reservation = conn.get_all_instances(instance_ids=[instance_id])[0]
    instance = reservation.instances[0]
    while instance.state != 'terminated':
        time.sleep(1)
        print '.',
        reservation = conn.get_all_instances(instance_ids=[instance_id])[0]
        instance = reservation.instances[0]

    print "Deleting temporary EBS volumes made from the AMI/snapshots"
    for v in volumes:
        v.delete()
    print "----------"
    print "EC2 cleanup done. The AMI and snapshots have *not* been deleted, as they're good to keep around."
    print "Consider manually cleaning out old AMIs and snapshots every once and a while!"

def fix_locale():
    sudo('update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8')
    disconnect_all()

def setup_transifex():
    with virtualenv():
        sudo('apt-get install gettext')
        sudo('pip install transifex-client', user='www-data')

        with cd(os.path.join(env.src_root, 'localwiki')):
            run('tx init')
            run("tx set --execute --auto-local -r localwiki.djangopo -s en -f locale/en/LC_MESSAGES/django.po 'locale/<lang>/LC_MESSAGES/django.po'")
            run("tx set --execute --auto-local -r localwiki.djangojs -s en -f locale/en/LC_MESSAGES/djangojs.po 'locale/<lang>/LC_MESSAGES/djangojs.po'")

def pull_translations():
    with settings(warn_only=True):
        with virtualenv():
            r = run('which tx')
            if not r.return_code == 0:
                setup_transifex()

            with cd(os.path.join(env.src_root, 'localwiki')):
                with virtualenv():
                    run('tx pull -a')
                    sudo('localwiki-manage compilemessages', user='www-data')

def push_translations():
    with settings(warn_only=True):
        with virtualenv():
            r = run('which tx')
            if not r.return_code == 0:
                setup_transifex()

            with cd(os.path.join(env.src_root, 'localwiki')):
                with virtualenv():
                    sudo('localwiki-manage makemessages -l en', user='www-data')
                    sudo('localwiki-manage makemessages -d djangojs -l en', user='www-data')
                    run('tx push -s -t')

def populate_page_cards():
    with virtualenv():
        sudo('localwiki-manage runscript populate_page_cards', user='www-data')

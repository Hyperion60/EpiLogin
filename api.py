import logging
import json
import requests
from requests.auth import HTTPBasicAuth

import logs

BAN_TYPES = (
    ('group', 'GROUP'),
    ('email', 'EMAIL'),
    ('user', 'USER'),
)

def get_headers(config):
    return {'Authorization': 'Token ' + config['website']['token']}

# get all parameters if the api is in multi pages
def fetch_paginate(config, next):
    output = []

    while next:
        r = requests.get(next, headers=get_headers(config))

        if r.status_code != 200:
            print('Request failed,', next, r.status_code)
            return None

        data = r.json()

        output += data['results']
        next = data['next']

    return output

def get_member(config, discord_id):
    url = "{}/api/members/{}/".format(config['website']['url'], discord_id)
    r = requests.get(url, headers=get_headers(config))

    if r.status_code == 200:
        return r.json()
    else:
        return None

def create_member(config, member):
    url = "{}/api/members/".format(config['website']['url'])
    r = requests.post(url, {
        'id': member.id,
        'name': str(member),
        'icon_url': member.avatar,
    }, headers=get_headers(config))

    if r.status_code == 201:
        return r.json()
    else:
        return None

def update_username(config, member):
    url = "{}/api/members/{}/".format(config['website']['url'], member.id)
    r = requests.patch(url, {
        'id': member.id,
        'name': str(member),
        'icon_url': member.avatar,
    }, headers=get_headers(config))

def get_ids(config, email):
    url = "{}/api/members/?email={}".format(config['website']['url'], email)
    return fetch_paginate(config, url)

def get_groups(config, email='', group=''):
    url = "{}/api/groups/?email={}&group={}".format(config['website']['url'], email, group)
    return fetch_paginate(config, url)

def get_bans(config, server, email='', group=''):
    url = "{}/api/bans/?server={}&type={}&value={}".format(server, email, group)
    return fetch_paginate(config, url)

def get_updates(config):
    url = "{}/api/updates/".format(config['website']['url'])
    return fetch_paginate(config, url)

def del_updates(config, ids):
    for id in ids:
        url = "{}/api/updates/{}/".format(config['website']['url'], id)
        r = requests.delete(url, headers=get_headers(config))

def __format_bans(server):
    ban_set = server.pop('ban_set')
    server['bans'] = {
        'group': [],
        'email': [],
        'user':  [],
    }

    for ban in ban_set:
        server['bans'][ban['type']].append(ban['value'])

def __format_emails_domains(server):
    emails_domains = server.pop('emails_domains')
    server['domains'] = [e['domain'] for e in emails_domains]

def __format_ranks(server):
    rank_set = server.pop('rank_set')
    server['ranks'] = {
        'classic':   {},
        'confirmed': [],
        'banned':    [],
    }

    for rank in rank_set:
        type       = rank.pop('type')
        discord_id = rank.pop('discord_id')
        name       = rank.pop('name')

        if type == 'classic':
            if not name in server['ranks'][type]:
                server['ranks'][type][name] = []
            server['ranks'][type][name].append(discord_id)
        else:
            server['ranks'][type].append(discord_id)

async def update_conf_all(client, config):
    url = '{}/api/servers/'.format(config['website']['url'])
    data = fetch_paginate(config, url)

    if not data:
        return False

    new = {}

    for server in data:
        server_id = server.pop('id')
        new[server_id] = server

        __format_ranks(server)
        __format_bans(server)
        __format_emails_domains(server)

    config['servers'] = new

    await logs.config_loaded(client, config)

    return True

async def update_conf(client, config, server_id):
    url = '{}/api/servers/{}/'.format(config['website']['url'], server_id)
    r = requests.get(url, headers=get_headers(config))

    if r.status_code != 200:
        return False

    server = r.json()
    __format_ranks(server)
    __format_bans(server)
    __format_emails_domains(server)
    config['servers'][server_id] = server

    return True

def on_member_remove(config, guild_id, member_id):
    url = "{}/api/members/{}/server/".format(config['website']['url'], member_id)
    r = requests.delete(url, data={'id': guild_id}, headers=get_headers(config))

def on_member_join(config, guild_id, member_id):
    url = "{}/api/members/{}/server/".format(config['website']['url'], member_id)
    r = requests.post(url, {'id': guild_id}, headers=get_headers(config))

def on_guild_join(config, guild_id):
    url = "{}/api/servers/".format(config['website']['url'])
    r = requests.post(url, {'id': guild_id}, headers=get_headers(config))

def update_guild(config, guild):
    url = "{}/api/servers/{}/".format(config['website']['url'], guild.id)
    r = requests.patch(url, {
        'id': guild.id,
        'name': guild.name,
        'icon_url': guild.icon,
    }, headers=get_headers(config))

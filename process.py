import os
import yaml

from bioblend import galaxy

config_file = os.environ['CONFIG_FILE']

# create a role and a group in Galaxy
gpu_access_role = "gpu_access_validated"
gpu_access_group = "gpu_access_validated"

# form link: https://docs.google.com/forms/d/e/1FAIpQLSd-isWRKIX9QVRNJAEBVfh4pLpR3NsOAdOSgKpZH9sKdJ0rBg/viewform


with open(config_file, 'r') as handle:
    CONFIG = yaml.safe_load(handle)

with open(CONFIG['filename'], 'r') as handle:
    data = [x.split('\t') for x in handle.read().split('\n')[1:]]

gi = galaxy.GalaxyInstance(url=CONFIG['url'], key=CONFIG['key'])


def add_users():

    # create a list of users that have been approved to use
    approved_user_emails = set()
    for idx, line in enumerate(data):
    approved_user_emails = set()
    for idx, line in enumerate(data):
        if len(line) != 7:
            print(f"Could not validate line {idx}, skipping")
            continue
        submit_date, _, name, institution, agreement, email, date_approved = line  # a new column was added by accident and we can not remove it anymore
        if len(date_approved.strip()) == 0:
            print(f"Skipping {name} due to unapproved")
            continue
        if len(email.strip()) == 0:
            print(f"Skipping, email missing in line {idx}")
            continue
        approved_user_emails.add(email)

    rolesclient = galaxy.roles.RolesClient(gi)
    groupsclient = galaxy.groups.GroupsClient(gi)
    usersclient = galaxy.users.UserClient(gi)

    # find the correct group
    all_groups = groupsclient.get_groups()
    gpu_group = None
    for gp in all_groups:
        if gp["name"] == gpu_access_group:
            gpu_group = gp
            break
    if not gpu_group:
        exit(f'Could not find "{gpu_access_group}". Please create this group in your Galaxy instance.')

    # find all users that have been added to the correct group
    all_added_users = groupsclient.get_group_users(group_id=gpu_group["id"])

    # get a list of users that need to be added to the group

    user_ids = list()
    # get user ids
    for user_email in approved_user_emails:
        user = usersclient.get_users(f_email=user_email)
        if len(user) > 0:
            user_ids.append(user[0]["id"])

    # get the correct role
    all_roles = rolesclient.get_roles()
    gpu_role = None
    for item in enumerate(all_roles):
        if item[1]["name"] == gpu_access_role:
            gpu_role = item
            break
    # add approved users to correct group and role
    groupsclient.update_group(group_id=gpu_group["id"], user_ids=user_ids, role_ids=[gpu_role[1]["id"]])


add_users()

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
    approved_user_ids = list()
    for idx, line in enumerate(data):
        if len(line) == 7:
            submit_date, email, name, institution, agreement, _, date_approved = line # 6 line was added by accident and we can not remove it anymore
        date_approved = date_approved.strip()
        if len(date_approved) == 0:
            print("Skipping %s due to unapproved" % name)
            continue
        approved_user_ids.append(email)

    rc = galaxy.roles.RolesClient(gi)
    gc = galaxy.groups.GroupsClient(gi)
    uc = galaxy.users.UserClient(gi)

    # find the correct group
    all_groups = gc.get_groups()
    gpu_group = None
    for gp in all_groups:
        if gp["name"] == gpu_access_group:
            gpu_group = gp
            break
    if not gpu_group:
        exit(f'Could not find "{gpu_access_group}". Please create this group in your Galaxy instance.')

    # find all users that have been added to the correct group
    all_added_users = gc.get_group_users(group_id=gpu_group["id"])

    # get a list of users that need to be added to the group
    new_users = list(set(approved_user_ids).difference(set([item["email"] for item in all_added_users])))

    l_user_ids = list()
    # get user ids
    for i, item in enumerate(new_users):
        user = uc.get_users(f_email=item)
        if len(user) > 0:
            l_user_ids.append(user[0]["id"])

    # get the correct role
    all_roles = rc.get_roles()
    gpu_role = None
    for item in enumerate(all_roles):
        if item[1]["name"] == gpu_access_role:
            gpu_role = item
            break
    # add approved users to correct group and role
    gc.update_group(group_id=gpu_group["id"], user_ids=l_user_ids, role_ids=[gpu_role[1]["id"]])


add_users()

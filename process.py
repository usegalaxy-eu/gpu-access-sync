import os
import yaml

from bioblend import galaxy


# form link: https://docs.google.com/forms/d/e/1FAIpQLSd-isWRKIX9QVRNJAEBVfh4pLpR3NsOAdOSgKpZH9sKdJ0rBg/viewform
def get_str_from_env_or_error(env: str) -> str:
    if len(from_env := os.environ.get(env, "").strip()) > 0:
        return from_env
    raise ValueError("Environment variable not found!")


config_file_name = get_str_from_env_or_error("CONFIG_FILE")
gpu_role_id = get_str_from_env_or_error("GPU_ROLE_ID")
gpu_group_id = get_str_from_env_or_error("GPU_GROUP_ID")

with open(config_file_name, "r") as handle:
    CONFIG = yaml.safe_load(handle)

with open(CONFIG["filename"], "r") as handle:
    data = [x.split("\t") for x in handle.read().split("\n")[1:]]

gi = galaxy.GalaxyInstance(url=CONFIG["url"], key=CONFIG["key"])


def add_users():
    """
    Get a list of user related emails from a list of rows.
    Then queries Galaxy's API to convert this list into encoded user IDs
    And finally substitutes the members of the Group GPU_GROUP_ID to this list of user IDs
    and the roles attached to that group by the Role GPU_ROLE_ID
    """
    approved_user_emails = set()
    for idx, line in enumerate(data):
        if len(line) != 7:
            print(f"Could not validate line {idx}, skipping")
            continue
        submit_date, _, name, institution, agreement, email, date_approved = (
            line  # a new column was added by accident and we can not remove it anymore
        )
        if len(date_approved.strip()) == 0:
            print(f"Skipping {name} due to unapproved")
            continue
        if len(email.strip()) == 0:
            print(f"Skipping, email missing in line {idx}")
            continue
        approved_user_emails.add(email)

    usersclient = galaxy.users.UserClient(gi)

    user_ids = []

    for user_email in approved_user_emails:
        user = usersclient.get_users(f_email=user_email)
        if len(user) > 0:
            user_ids.append(user[0]["id"])

    groupsclient = galaxy.groups.GroupsClient(gi)

    groupsclient.update_group(
        group_id=gpu_group_id, user_ids=user_ids, role_ids=gpu_role_id
    )


add_users()

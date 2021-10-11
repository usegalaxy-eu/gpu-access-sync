import datetime
import os
import yaml

from bioblend import galaxy
from datetime import timedelta
from dateutil.parser import parse


TODAY = datetime.datetime.now()
HOW_LONG = {
    '1 month': timedelta(days=30),
    '3 months': timedelta(days=3 * 30),
    '6 months': timedelta(days=6 * 30),
}
QUOTAS = None
with open(os.environ['CONFIG_FILE'], 'r') as handle:
    CONFIG = yaml.safe_load(handle)

with open(CONFIG['filename'], 'r') as handle:
    data = [x.split('\t') for x in handle.read().split('\n')[1:]]

gi = galaxy.GalaxyInstance(url=CONFIG['url'], key=CONFIG['key'])


def process(data):
    processed = {}
    for idx, (submit_date, email, name, institution, working_group, date_start,
              how_long, space_needed, organisms, bacteria, plant,
              biological_question, data_type, file_types, how_many, agreement,
              date_approved) in enumerate(data):

        date_approved = date_approved.strip()

        # Not approved, ignore
        if len(date_approved) == 0:
            print("Skipping %s due to unapproved" % name)
            continue
        # We will key on email
        key = email

        # Two of our times
        date_start = parse(date_start)
        date_approved = parse(date_approved)
        # If this does not start yet safe to ignore.
        # HXR: Disabled because of multiple people complaining it wasn't
        # immediately available, when they specified their project didn't start
        # for N days.
        # if date_start >= TODAY:
            # print("Skipping %s due to not starting yet (%s !>= %s)" % (name, date_start, TODAY))
            # continue

        # Otherwise should be now + N months
        if key not in processed:
            processed[key] = []

        days = HOW_LONG[how_long]

        # Parse the allocatoin
        allocation = 0

        # Not specified
        if "I don't know" in space_needed or len(space_needed.strip()) == 0:
            print("Skipping %s due to unknown space" % name)
            continue

        print("Project: %30s space='%6s' start=%12s approved=%12s" % (name, space_needed, date_start, date_approved))
        (size, spec) = space_needed.strip().split(' ')
        if spec == 'GB':
            allocation = float(size)
        elif spec == 'TB':
            allocation = 1024 * float(size)

        # Generate the entry
        processed[key].append({
            # 'idx': idx,
            # 'started': date_approved,
            'expires': date_start + days,
            'size': allocation
        })

    return processed


def ensure_quota_exists(size):
    global QUOTAS
    if not QUOTAS:
        QUOTAS = {x['name']: x for x in gi.quotas.get_quotas()
                  if 'auto_' in x['name']}

    if isinstance(size, str) and 'auto_' in size:
        size = size[len('auto_'):]

    key = 'auto_%s' % size
    if key in QUOTAS:
        return QUOTAS[key]

    title = 'Automatic quota created for quota form'
    new_quota = gi.quotas.create_quota(key, title, '%s GB' % size, '+',
                                       default='no', in_users=[], in_groups=[])
    QUOTAS[key] = new_quota['id']
    return QUOTAS[key]


def ensure(data):
    expected_buckets = {}
    user_id_map = {}

    # Bucket the users into lists based on quotas.
    for email in data:
        valid_claims = [x for x in data[email] if TODAY <= x['expires']]
        needed_space = int(sum([x['size'] for x in valid_claims]))
        gx_user = gi.users.get_users(f_email=email)
        if len(gx_user) == 0:
            print("ERROR: %s was not found" % email)
            continue
        # Get only first user
        gx_user = gx_user[0]
        # Ensure the quota exists
        user_id_map[gx_user['id']] = email
        ensure_quota_exists(needed_space)
        key = 'auto_%s' % needed_space
        if key not in expected_buckets:
            expected_buckets[key] = []
        expected_buckets[key].append(gx_user)

    all_quotas = {q['name']: q for q in gi.quotas.get_quotas()
                  if 'auto_' in q['name']}

    for quota_name, quota in all_quotas.items():
        # Get the users for that quota from the expected buckets
        # Default to empty list so if users are removed we update the quota
        users = expected_buckets.get(quota_name, [])
        # And now we'll update
        # print(gi.quotas.show_quota(quota['id']))
        current_quota_users = gi.quotas.show_quota(quota['id'])['users']
        emails_before = [user_id_map.get(user['user']['id'], user['user']['id']) for user in current_quota_users]
        emails_after = [user_id_map.get(user['id'], user['id']) for user in users]
        print('[%s] BEFORE: %s' % (quota_name, ', '.join(sorted(emails_before))))
        print('[%s] AFTER : %s' % (quota_name, ', '.join(sorted(emails_after))))

        gi.quotas.update_quota(
            quota['id'],
            default='unregistered',
        )
        print(gi.quotas.update_quota(
            quota['id'],
            default='no',
            in_users=[user['id'] for user in users]
        ))


ensure(process(data))

# Galaxy-Google Response Quota Sync

Write a configuration file:

```yaml
url: https://usegalaxy.eu
key: ....
filename: 'Quota Request Form (Responses).tsv'
```

Then you can run it like:

```
./gdrive export {google_file_id} --mime text/tab-separated-values --force
CONFIG_FILE=conf.yaml python process.py
```

It will automatically generate missing quotas and synchronize the user list.

## LICENSE

GPLv3

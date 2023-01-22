# Galaxy-Google Response GPU access Sync

As Galaxy project we provide free resources to all people. But as always a few of those people abuse free resources with egoistic behaviour.
On usegalaxy.eu we have restricted the access to GPUs from our Jupyter Notebook for that reason. If a user starts a GPU-Jupyter they will get an error
that points them to http://usegalaxy.eu/gpu-request to fill a request for GPU access. Our team will review those as soon as we can.
On acceptance, this repo will be used by our CI system (which runs every 24h) to add the email of the user
into a Galaxy group named `gpu_access_validated`.
This in turn will allow our dynamic job scheduling ([TPV](https://github.com/galaxyproject/total-perspective-vortex/)) to grant permissions.

Write a configuration file (`conf.yml`):

```yaml
url: https://usegalaxy.eu
key: ....
filename: 'useGalaxy.eu: GPU Access Request Form (Responses)'
```

Then you can run it like:

```
./gdrive export {google_file_id} --mime text/tab-separated-values --force
CONFIG_FILE=conf.yml python process.py
```

It will automatically add users from the Spreadsheet to the Galaxy groups/rols (`gpu_access_validated`).

## LICENSE

GPLv3

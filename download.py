import io, os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive"]


def download_file(environment_variables: dict):
    """Downloads a file
    Args:
        Dict with environment variables:
        BEARER_TOKEN_FILE: A google service account bearer token (key file) in json format
        GOOGLE_DRIVE_FILE_ID: The ID of the file to download
        FILE_NAME: How to name the downloaded file

    Inspired by
    https://github.com/googleworkspace/python-samples/blob/main/drive/snippets/drive-v3/file_snippet/export_pdf.py
    and
    https://workspace.google.com/blog/developers-practitioners/dont-fear-authentication-google-drive-edition?hl=en

    """
    sa_creds = service_account.Credentials.from_service_account_file(
        environment_variables["BEARER_TOKEN_FILE"]
    )
    scoped_creds = sa_creds.with_scopes(SCOPES)

    try:
        # create drive api client
        service = build("drive", "v3", credentials=scoped_creds)

        # pylint: disable=maybe-no-member
        request = service.files().export_media(
            fileId=environment_variables["GOOGLE_DRIVE_FILE_ID"],
            mimeType="text/tab-separated-values",
        )
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")
        with open(environment_variables["FILE_NAME"], "wb") as f:
            f.write(file.getbuffer())
    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None


def get_str_from_env_or_error(env: str) -> str:
    if len(from_env := os.environ.get(env, "").strip()) > 0:
        return from_env
    else:
        raise ValueError("Environment variable not found!")


if __name__ == "__main__":
    envs = {"BEARER_TOKEN_FILE": "", "GOOGLE_DRIVE_FILE_ID": "", "FILE_NAME": ""}
    for name, value in envs.items():
        envs[name] = get_str_from_env_or_error(name)
    download_file(environment_variables=envs)

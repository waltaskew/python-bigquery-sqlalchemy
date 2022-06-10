# Copyright 2021 The sqlalchemy-bigquery Authors
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import functools
import re

from google.api_core import client_info
import google.auth
from google.cloud import bigquery
from google.oauth2 import credentials
from google.oauth2 import service_account
import sqlalchemy
import base64
import json


USER_AGENT_TEMPLATE = "sqlalchemy/{}"
SCOPES = (
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
)


def google_client_info():
    user_agent = USER_AGENT_TEMPLATE.format(sqlalchemy.__version__)
    return client_info.ClientInfo(user_agent=user_agent)


def create_bigquery_client(
    credentials_info=None,
    credentials_path=None,
    credentials_base64=None,
    credentials_user_info_json=None,
    default_query_job_config=None,
    location=None,
    project_id=None,
):
    default_project = None

    if credentials_base64:
        credentials_info = json.loads(base64.b64decode(credentials_base64))

    if credentials_path:
        bq_credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        bq_credentials = bq_credentials.with_scopes(SCOPES)
        default_project = bq_credentials.project_id
    elif credentials_info:
        bq_credentials = service_account.Credentials.from_service_account_info(
            credentials_info
        )
        bq_credentials = bq_credentials.with_scopes(SCOPES)
        default_project = bq_credentials.project_id
    elif credentials_user_info_json:
        bq_credentials = credentials.Credentials.from_authorized_user_info(
            json.loads(credentials_user_info_json))
    else:
        bq_credentials, default_project = google.auth.default(scopes=SCOPES)

    if project_id is None:
        project_id = default_project

    return bigquery.Client(
        client_info=google_client_info(),
        project=project_id,
        credentials=bq_credentials,
        location=location,
        default_query_job_config=default_query_job_config,
    )


def substitute_re_method(r, flags=0, repl=None):
    if repl is None:
        return lambda f: substitute_re_method(r, flags, f)

    r = re.compile(r, flags)

    @functools.wraps(repl)
    def sub(self, s, *args, **kw):
        def repl_(m):
            return repl(self, m, *args, **kw)

        return r.sub(repl_, s)

    return sub


def substitute_string_re_method(r, *, repl, flags=0):
    r = re.compile(r, flags)
    return lambda self, s: r.sub(repl, s)

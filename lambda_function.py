"""AWS Lambda handler with Sentry.

Runs in the official AWS Lambda base image. The image has the Runtime
Interface Emulator inside, so the exact same container works locally without
an AWS account:

    docker run -p 9000:8080 -e SENTRY_DSN=... sample-aws-lambda
    curl -d '{"kind":"error"}' localhost:9000/2015-03-31/functions/function/invocations
"""
import os
import time

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

OWN_DSN = os.environ.get("SENTRY_DSN")


def init(dsn):
    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "local"),
        release=os.environ.get("RELEASE", "sample-aws-lambda@dev"),
        integrations=[AwsLambdaIntegration(timeout_warning=True)],
        traces_sample_rate=1.0,
    )


init(OWN_DSN)
_active_dsn = OWN_DSN


def charge(order):
    return order["amount"] * order["qty"]  # KeyError: 'qty'


def lambda_handler(event, context):
    # dashboard "Use my DSN". One container = one invoke at a time, so swapping
    # the global client is safe here. On real AWS you would not do this.
    global _active_dsn
    want = event.get("dsn") or OWN_DSN
    if want != _active_dsn:
        init(want)
        _active_dsn = want

    run = event.get("run", "manual")
    sentry_sdk.set_tag("run_id", run)
    if event.get("fresh", True):
        sentry_sdk.get_isolation_scope().fingerprint = ["{{ default }}", run]

    if event.get("kind") == "timeout":
        # Function timeout is 3 s (AWS_LAMBDA_FUNCTION_TIMEOUT). Sentry sends a
        # "WARNING : Function is expected to get timed out" before AWS kills it.
        time.sleep(10)

    # Unhandled: AwsLambdaIntegration reports it, with the Lambda context.
    return {"total": charge({"id": f"ord-{run}", "amount": 20})}

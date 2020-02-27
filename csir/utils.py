from datetime import datetime
from re import sub


# we don't need nanosecond precision here,
# and python only supports it in 3.8+,
# so just drop the nanoseconds/microseconds, if any
def clean_timestamp(timestamp):
    return datetime.strptime(
        sub('\.\d+Z$', "Z", timestamp),
        '%Y-%m-%dT%H:%M:%SZ'
    )

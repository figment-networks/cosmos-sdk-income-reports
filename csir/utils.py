from datetime import datetime
from re import sub
from time import sleep


# we don't need nanosecond precision here,
# and python only supports it in 3.8+,
# so just drop the nanoseconds/microseconds, if any
def clean_timestamp(timestamp):
    return datetime.strptime(
        sub('\.\d+Z$', "Z", timestamp),
        '%Y-%m-%dT%H:%M:%SZ'
    )


def with_retries(func, tries):
    while tries > 0:
        try:
            return func()
        except:
            tries -= 1
            if tries > 0:
                sleep(0.1)
                continue
            raise

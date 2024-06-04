from requests import session


def construct_url(country_code: str, job_title: str, location: str, start: int):

    return f'https://{country_code}.indeed.com/jobs?q={job_title}&l={location}&sort=date&start={start}'
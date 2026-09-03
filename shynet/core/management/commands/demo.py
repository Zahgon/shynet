from logging import info
import random
import uuid

import click
from flask.cli import with_appcontext
from sqlalchemy import select

from analytics.models import Session, Hit
from analytics.tasks import ingress_request
from core.models import User, Service
from shynet.extensions import db
from shynet.timezone import now, timedelta

LOCATIONS = [
    "/",
    "/post/{rand}",
    "/login",
    "/me",
]

REFERRERS = [
    "https://news.ycombinator.com/item?id=11116274",
    "https://news.ycombinator.com/item?id=24872911",
    "https://reddit.com",
    "https://facebook.com",
    "https://twitter.com/milesmccain",
    "https://twitter.com",
    "https://stanford.edu/~mccain/",
    "https://tiktok.com",
    "https://io.stanford.edu",
    "https://en.wikipedia.org",
    "https://stackoverflow.com",
    "",
    "",
    "",
    "",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/43.4",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko)",
    "Version/10.0 Mobile/14E304 Safari/602.1",
]


@click.command("demo")
@click.argument("name", type=str)
@click.argument("owner_email", type=str)
@click.argument("avg", type=int)
@click.argument("deviation", type=float, default=0.4)
@click.argument("days", type=int)
@click.argument("load_time", type=float, default=1000)
@with_appcontext
def command(name, owner_email, avg, deviation, days, load_time):
    """Configures a Shynet demo service"""
    owner = db.session.scalar(select(User).where(User.email == owner_email))
    service = Service(name=name, owner=owner)
    db.session.add(service)
    db.session.commit()

    print(
        f"Created demo service `{service.name}` (uuid: `{service.uuid}`, owner: {owner})"
    )

    # Go through each day requested, creating sessions and hits
    for days_ago in range(days):
        day = (now() - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0)
        print(f"Populating info for {day}...")
        ips = [
            ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
            for _ in range(avg)
        ]

        n = avg + random.randrange(int(-1 * deviation * avg), int(deviation * avg))
        for _ in range(n):
            time = day + timedelta(
                hours=random.randrange(0, 23),
                minutes=random.randrange(0, 59),
                seconds=random.randrange(0, 59),
            )
            ip = random.choice(ips)
            hit_load_time = random.normalvariate(load_time, 500)
            referrer = random.choice(REFERRERS)
            location = "https://example.com" + random.choice(LOCATIONS).replace(
                "{rand}", str(random.randint(0, n))
            )
            user_agent = random.choice(USER_AGENTS)
            ingress_request(
                service.uuid,
                "JS",
                time,
                {"loadTime": hit_load_time, "referrer": referrer},
                ip,
                location,
                user_agent,
            )

        print(f"Created {n} demo hits on {day}!")

    click.secho("Successfully created demo data!", fg="green")

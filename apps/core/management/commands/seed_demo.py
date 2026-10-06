"""Seed the database with the Madiwala demo world.

Recreates the exact content the Flutter mock shipped with — members,
tasks across every vertical, auctions with live bids, partner perks,
play challenges, community ideas — so the real backend feels identical
to the demo.

    python manage.py seed_demo            # adds seed content if missing
    python manage.py seed_demo --fresh    # wipe seed content and re-add
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Member
from apps.auctions.models import AuctionItem, Bid
from apps.engagement.models import BoardIdea, PartnerPerk, PlayChallenge
from apps.posts.models import Task

P = "https://images.unsplash.com/photo-{}?w=256&h=256&fit=crop&crop=faces&auto=format"


def _members() -> list[tuple[str, str, str, str, dict]]:
    """(key, email, name, bio, extra) tuples mirroring kSeedMembers."""
    return [
        (
            "u1",
            "u1@needy.app",
            "Ayesha Khan",
            "College student. Loves chai and long walks.",
            dict(
                photo_url=P.format("1494790108377-be9c29b29330"),
                gender=Member.Gender.FEMALE,
                completed_count=42,
                rating=4.9,
                rating_count=50,
                verified_badge=True,
                karma=320,
                is_guardian=True,
                available_now=True,
            ),
        ),
        (
            "u2",
            "u2@needy.app",
            "Ravi Kumar",
            "Bike mechanic near Jyoti Nivas. Weekend cricketer.",
            dict(
                photo_url=P.format("1507003211169-0a1dd7228f2d"),
                gender=Member.Gender.MALE,
                completed_count=67,
                rating=4.7,
                rating_count=80,
                verified_badge=True,
                karma=540,
                is_guardian=True,
                available_now=False,
            ),
        ),
        (
            "u3",
            "u3@needy.app",
            "Meera Nair",
            "Final year BA. Happy to accompany for errands.",
            dict(
                photo_url=P.format("1438761681033-6461ffad8d80"),
                gender=Member.Gender.FEMALE,
                completed_count=18,
                rating=4.8,
                rating_count=22,
            ),
        ),
        (
            "u4",
            "u4@needy.app",
            "Sana Reddy",
            "Nursing student. Free Sunday mornings.",
            dict(
                photo_url=P.format("1544005313-94ddf0286df2"),
                gender=Member.Gender.FEMALE,
                completed_count=25,
                rating=4.9,
                rating_count=30,
                verified_badge=True,
                karma=180,
                is_guardian=True,
                available_now=True,
            ),
        ),
        (
            "u5",
            "u5@needy.app",
            "Karthik S",
            "IT guy. Can carry heavy stuff, has a bike.",
            dict(
                photo_url=P.format("1500648767791-00dcc994a43e"),
                gender=Member.Gender.MALE,
                completed_count=31,
                rating=4.6,
                rating_count=36,
                karma=210,
                available_now=True,
            ),
        ),
        (
            "u6",
            "u6@needy.app",
            "Lakshmi Devi",
            "Homemaker. Cooks, hosts, feeds people.",
            dict(
                photo_url=P.format("1502823403499-6ccfcf4fb453"),
                gender=Member.Gender.FEMALE,
                completed_count=54,
                rating=5.0,
                rating_count=60,
                verified_badge=True,
            ),
        ),
        (
            "u7",
            "u7@needy.app",
            "Imran Ali",
            "MCA student. Study partner material.",
            dict(
                photo_url=P.format("1506794778202-cad84cf45f1d"),
                gender=Member.Gender.MALE,
                completed_count=9,
                rating=4.5,
                rating_count=11,
            ),
        ),
        (
            "u8",
            "u8@needy.app",
            "Divya Sharma",
            "Freelance artist. Museum & cafe buddy.",
            dict(
                photo_url=P.format("1534528741775-53994a69daeb"),
                gender=Member.Gender.FEMALE,
                completed_count=22,
                rating=4.8,
                rating_count=27,
            ),
        ),
    ]


class Command(BaseCommand):
    help = "Seed the Madiwala demo world (members, tasks, auctions, perks, challenges, ideas)."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true", help="Delete seed content first.")

    def handle(self, *args, **options):
        if options["fresh"]:
            self._wipe()
        created = self._seed()
        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created}"))

    def _wipe(self) -> None:
        Bid.objects.all().delete()
        AuctionItem.objects.all().delete()
        Task.objects.all().delete()
        BoardIdea.objects.all().delete()
        PartnerPerk.objects.all().delete()
        PlayChallenge.objects.all().delete()
        Member.objects.filter(email__endswith="@needy.app").delete()
        Member.objects.filter(email__endswith="@nuvra.app").delete()

    def _seed(self) -> str:
        now = timezone.now()
        members: dict[str, Member] = {}

        for key, email, name, bio, extra in _members():
            member, created = Member.objects.get_or_create(
                email=email, defaults={"public_name": name, "bio": bio, **extra}
            )
            if not created:
                for field, value in {"public_name": name, "bio": bio, **extra}.items():
                    setattr(member, field, value)
                member.save()
            members[key] = member
            for badge in ("punctual", "friendly"):
                member.add_badge(badge)

        me, _ = Member.objects.get_or_create(
            email="demo@needy.app",
            defaults=dict(
                public_name="You",
                bio="New in Madiwala. Happy to help with errands and tea walks.",
                photo_url=P.format("1517841905240-472988babdf9"),
                gender=Member.Gender.OTHER,
                completed_count=7,
                rating=4.8,
                rating_count=9,
                verified_badge=True,
                karma=320,
                categories=["Errands", "Tea & walks"],
            ),
        )
        members["me"] = me

        n_tasks = 0
        for spec in _tasks(now, members):
            Task.objects.create(**spec)
            n_tasks += 1

        n_auc = 0
        for spec in _auctions(now, members):
            seed_bids = spec.pop("seed_bids", []) or []
            auction = AuctionItem.objects.create(**spec)
            for bidder_key, amount, _minutes_ago in seed_bids:
                Bid.objects.create(auction=auction, bidder=members[bidder_key], amount=amount)
            n_auc += 1

        for code, title, rules, target, reward in [
            (
                "tap30",
                "Reflex Rush",
                "Tap the glowing orb as it jumps around — 30 seconds. Beat the target to earn full Time Credits.",
                25,
                60,
            ),
            (
                "memory",
                "Colour Echo",
                "Repeat the colour sequence — it grows every round. How far does your memory echo?",
                6,
                80,
            ),
        ]:
            PlayChallenge.objects.update_or_create(
                code=code,
                defaults=dict(title=title, rules=rules, target=target, reward_karma=reward),
            )

        for merchant, title, details, icon, cost, area, hours in [
            (
                "Brahmins' Coffee Bar",
                "Free filter coffee",
                "Any brew on the menu, on the house when you show the voucher.",
                "local_cafe",
                120,
                "Shankarapuram, 5 min away",
                24,
            ),
            (
                "Nagarjuna Meals",
                "20% off biryani (2+ people)",
                "Flat discount on dine-in for groups of two or more needy members.",
                "restaurant",
                200,
                "Madiwala Main Rd",
                72,
            ),
            (
                "Corner House",
                "Buy 1 get 1 sundae",
                "Grab a friend — second sundae free with the voucher.",
                "icecream",
                90,
                "Jyoti Nivas Lane",
                48,
            ),
            (
                "Madiwala Cycle Works",
                "Free bike tune-up",
                "Brake & gear tune-up free with any purchase, or 100 credits standalone.",
                "pedal_bike",
                100,
                "5th Block",
                168,
            ),
        ]:
            PartnerPerk.objects.get_or_create(
                merchant=merchant,
                title=title,
                defaults=dict(
                    details=details, icon=icon, cost_karma=cost, area=area, valid_hours=hours
                ),
            )

        n_ideas = 0
        for author_key, title, details, tag, upvotes, days_ago, scheduled in [
            (
                "u1",
                "Madiwala Lake morning walk club",
                "A daily 7 AM walk around the lake — 3 laps, filter coffee after. Slowly it becomes the neighbourhood's alarm clock.",
                "Walk",
                34,
                3,
                True,
            ),
            (
                "u2",
                "Sunday football at JP Park ground",
                "Casual 7-a-side, 6:30 AM every Sunday. All skill levels — we rotate teams so it stays friendly.",
                "Sports",
                27,
                5,
                False,
            ),
            (
                "u8",
                "Weekend sketching meetup at the museum steps",
                "Bring anything that draws — pencils, pens, charcoal. Two hours of quiet sketching together, then chai.",
                "Meetup",
                19,
                2,
                False,
            ),
            (
                "u7",
                "Skill-swap evening: teach 1, learn 1",
                "Everyone teaches something for 15 minutes — guitar chords, Excel tricks, bike repair. Monthly at the library cafe.",
                "Feature",
                12,
                1,
                False,
            ),
        ]:
            BoardIdea.objects.get_or_create(
                title=title,
                defaults=dict(
                    author=members[author_key],
                    details=details,
                    tag=tag,
                    upvotes=upvotes,
                    created_at=now - timedelta(days=days_ago),
                    scheduled=scheduled,
                ),
            )
            n_ideas += 1

        return (
            f"{len(members)} members, {n_tasks} tasks, {n_auc} auctions, "
            f"{n_ideas} ideas, perks & challenges ensured"
        )


def _tasks(now, members) -> list[dict]:
    def base(**kw):
        defaults = dict(
            status=Task.TaskStatus.PUBLISHED,
            quarantined=False,
            meeting_preference="Public meeting point",
            has_checkin=False,
            gender_preference=Task.GenderPreference.ANYONE,
            payout_note="",
            applicant_count=random.randint(1, 8),  # demo texture only
        )
        defaults.update(kw)
        return defaults

    hours = lambda h: now + timedelta(hours=h)  # noqa: E731

    return [
        base(
            creator=members["u2"],
            type=Task.PostType.OFFER,
            kind=Task.PostKind.REGULAR,
            title="I'm free for 1 hour. Anyone need help/company?",
            description="Got an hour to spare in Madiwala before my evening study shift. Happy to help with quick errands, grab coffee, walk, or chat!",
            category="Company",
            scheduled_at=hours(1),
            duration_minutes=60,
            area="Madiwala · 4th Block",
            distance_km=0.3,
            exchange=Task.ExchangeMode.FREE,
            reward_amount=0,
            capacity=2,
            risk=Task.TaskRisk.LOW,
            created_at=hours(1) - timedelta(days=1),
        ),
        base(
            creator=members["u1"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.REGULAR,
            title="Bike wash + polish",
            description="Bike is dusty after a Hosur road trip. Need someone to wash and polish it near 5th Block. Bucket and supplies in the parking — no need to come inside.",
            category="Errands",
            scheduled_at=hours(20),
            duration_minutes=30,
            area="Madiwala · 5th Block",
            distance_km=0.8,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=100,
            capacity=1,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At my building parking",
            created_at=hours(20) - timedelta(days=1),
        ),
        base(
            creator=members["u8"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.REGULAR,
            title="Museum visit — need company",
            description="Going to the Government Museum on Saturday morning. Nobody around me is into history. Join me, filter coffee after.",
            category="Culture",
            scheduled_at=hours(40),
            duration_minutes=120,
            area="Madiwala · Meeting at Metro Gate B",
            distance_km=1.4,
            exchange=Task.ExchangeMode.FREE,
            reward_amount=0,
            capacity=2,
            risk=Task.TaskRisk.LOW,
            created_at=hours(40) - timedelta(days=1),
        ),
        base(
            creator=members["u3"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.REGULAR,
            title="Accompany me to college office",
            description='Collecting my degree certificates tomorrow 11 AM. The office insists on "one more person" for the ID verification queue. Just need company while I wait.',
            category="Errands",
            scheduled_at=hours(26),
            duration_minutes=90,
            area="Madiwala · Near Christ University gate",
            distance_km=2.1,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=300,
            capacity=1,
            risk=Task.TaskRisk.MEDIUM,
            meeting_preference="College main gate",
            has_checkin=True,
            created_at=hours(26) - timedelta(days=1),
        ),
        base(
            creator=members["u6"],
            type=Task.PostType.OFFER,
            kind=Task.PostKind.REGULAR,
            title="Sunday lunch — my treat",
            description="Cooking biryani for 6 this Sunday. Family is out of town, food should not be wasted. Come, eat, tell me about your city. Solo folks especially welcome.",
            category="Food",
            scheduled_at=hours(52),
            duration_minutes=90,
            area="Madiwala · Jyoti Nivas lane",
            distance_km=1.1,
            exchange=Task.ExchangeMode.TREAT,
            reward_amount=0,
            capacity=4,
            risk=Task.TaskRisk.LOW,
            gender_preference=Task.GenderPreference.FEMALE_ONLY,
            created_at=hours(52) - timedelta(days=1),
        ),
        base(
            creator=members["u2"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.REGULAR,
            title="Morning cricket — 2 more players",
            description="Regular Sunday 7 AM game at JP Park ground. We are 9, need 2 more. Medium pace, no fights, chai after.",
            category="Sports",
            scheduled_at=hours(15),
            duration_minutes=150,
            area="BTM Layout · JP Park",
            distance_km=2.8,
            exchange=Task.ExchangeMode.FREE,
            reward_amount=0,
            capacity=2,
            risk=Task.TaskRisk.LOW,
            gender_preference=Task.GenderPreference.MALE_ONLY,
            created_at=hours(15) - timedelta(days=1),
        ),
        base(
            creator=members["u4"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.REGULAR,
            title="Help my mom with groceries",
            description="I am travelling for work this week. Mom needs help carrying groceries from Madiwala market on Friday evening. She makes amazing snacks for helpers.",
            category="Errands",
            scheduled_at=hours(9),
            duration_minutes=45,
            area="Madiwala Market",
            distance_km=0.5,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=150,
            capacity=1,
            risk=Task.TaskRisk.MEDIUM,
            meeting_preference="Market entrance",
            has_checkin=True,
            created_at=hours(9) - timedelta(days=1),
        ),
        base(
            creator=members["u7"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.REGULAR,
            title="Study buddy — DSA evenings",
            description="Placements in December. Looking for a serious study partner, 7-9 PM at Madiwala library cafe. We split the table coffee.",
            category="Study",
            scheduled_at=hours(6),
            duration_minutes=120,
            area="Madiwala · Library cafe",
            distance_km=0.9,
            exchange=Task.ExchangeMode.BARTER,
            reward_amount=0,
            capacity=1,
            risk=Task.TaskRisk.LOW,
            meeting_preference="Public cafe",
            created_at=hours(6) - timedelta(days=1),
        ),
        base(
            creator=members["u5"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.REGULAR,
            title="Metro station pickup tonight",
            description="Reaching Indiranagar metro at 9:40 PM with two heavy bags. Need someone with a bike or car to drop me home. Fuel plus a bit extra covered.",
            category="Transport",
            scheduled_at=hours(5),
            duration_minutes=40,
            area="Indiranagar Metro Station",
            distance_km=3.6,
            exchange=Task.ExchangeMode.NEGOTIABLE,
            reward_amount=0,
            capacity=1,
            risk=Task.TaskRisk.HIGH,
            meeting_preference="Metro gate pickup",
            has_checkin=True,
            created_at=hours(5) - timedelta(days=1),
        ),
        # ── Emergency ──
        base(
            creator=members["u1"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.EMERGENCY,
            title="Drive my grandma to St. John's Hospital — now",
            description="Grandma slipped in the bathroom. Need someone with a car or bike to take her to St. John's emergency wing in Koramangala. I will sit with her, just need the driver.",
            category="Emergency",
            scheduled_at=now,
            duration_minutes=90,
            area="Madiwala · Jyoti Nivas Lane",
            distance_km=0.6,
            exchange=Task.ExchangeMode.FREE,
            reward_amount=0,
            capacity=1,
            risk=Task.TaskRisk.HIGH,
            meeting_preference="Shared in chat",
            has_checkin=True,
        ),
        base(
            creator=members["u6"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.EMERGENCY,
            title="Urgent: two hands to move fridge before repair van arrives",
            description="Service van comes in 90 minutes and the fridge is too heavy for one person. Two quick trips from kitchen to balcony would save the visit.",
            category="Emergency",
            scheduled_at=hours(1),
            duration_minutes=30,
            area="Madiwala · 4th Block",
            distance_km=0.4,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=300,
            capacity=2,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At my flat (building gate)",
        ),
        # ── Gigs ──
        base(
            creator=members["u3"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.GIG,
            creator_name_override="Sri Ganesh Stores",
            payout_note="₹900/day · 7 days",
            title="2 sales reps for Diwali rush — evening shift",
            description="Diwali stock is arriving and the shop needs two friendly people at the counter, 5–10 PM for one week. Basic Kannada helps, smile required.",
            category="Gigs",
            scheduled_at=hours(12),
            duration_minutes=7 * 8 * 60,
            area="Madiwala · Market Rd",
            distance_km=0.7,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=900 * 7,
            capacity=2,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At the shop",
        ),
        base(
            creator=members["u7"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.GIG,
            creator_name_override="Madiwala Cafe Corner",
            payout_note="₹700/day · 3 days",
            title="Weekend barista helper",
            description="Weekend rush cover — washing, packing, and handing orders. Breakfast + evening snacks on the house every shift.",
            category="Gigs",
            scheduled_at=hours(30),
            duration_minutes=3 * 8 * 60,
            area="Madiwala · Jyoti Nivas Lane",
            distance_km=1.1,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=700 * 3,
            capacity=1,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At the cafe",
        ),
        # ── Rooms ──
        base(
            creator=members["u8"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.ROOM,
            payout_note="1RK under ₹10,000",
            title="Urgent: 1RK near Madiwala market — new to city",
            description="Transferred to Bengaluru with two weeks to find a place. Need 1RK or single room walking distance from the market. Ground floor preferred. Happy to pay a scout fee for a working lead.",
            category="Rooms",
            scheduled_at=hours(24),
            duration_minutes=60,
            area="Madiwala / BTM border",
            distance_km=1.3,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=1000,
            capacity=1,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At the room",
        ),
        base(
            creator=members["u5"],
            type=Task.PostType.TASK,
            kind=Task.PostKind.ROOM,
            payout_note="2BHK under ₹28,000",
            title="Girls-only: 2BHK flatmate hunt near JP Park",
            description="Found a great 2BHK near JP Park — need one more flatmate to split rent. Female flat only. Scouts who know vacant flats in BTM get the fee.",
            category="Rooms",
            scheduled_at=hours(40),
            duration_minutes=60,
            area="BTM Layout · JP Park",
            distance_km=2.6,
            exchange=Task.ExchangeMode.PAID,
            reward_amount=800,
            capacity=1,
            risk=Task.TaskRisk.LOW,
            meeting_preference="At the room",
            gender_preference=Task.GenderPreference.FEMALE_ONLY,
        ),
        # ── Team & trips ──
        base(
            creator=members["u6"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.TEAM,
            title="Need 8 people for reels shoot — Sunday morning",
            description="Shooting a fun street-food reel series around Madiwala. Need 8 energetic people to be the crowd + one spot as taster-in-chief. Breakfast covered!",
            category="Teams",
            scheduled_at=hours(18),
            duration_minutes=180,
            area="Madiwala Market stretch",
            distance_km=0.9,
            exchange=Task.ExchangeMode.FREE,
            reward_amount=0,
            capacity=8,
            risk=Task.TaskRisk.LOW,
        ),
        base(
            creator=members["u2"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.TRIP,
            payout_note="Nandi Hills sunrise",
            title="Bike convoy to Nandi Hills — sunrise trip",
            description="Leaving 4:30 AM, reaching for sunrise, breakfast on the way back. Own bike or pillion (fuel split). Venue cost of ~₹2,400 split per head.",
            category="Trips",
            scheduled_at=hours(30),
            duration_minutes=8 * 60,
            area="Departure: Madiwala Metro Gate B",
            distance_km=25,
            exchange=Task.ExchangeMode.EXPENSES_COVERED,
            reward_amount=400,
            capacity=6,
            risk=Task.TaskRisk.MEDIUM,
            has_checkin=True,
        ),
        base(
            creator=members["u4"],
            type=Task.PostType.COMPANY,
            kind=Task.PostKind.TRIP,
            payout_note="Skandagiri trek",
            title="Girls-only night trek — Skandagiri full moon",
            description="Guided night trek under the full moon. Fees, transport and breakfast ≈ ₹1,800 total, split per head. Two verified Guardians already joining.",
            category="Trips",
            scheduled_at=hours(50),
            duration_minutes=8 * 60,
            area="Departure: Madiwala · 5th Block",
            distance_km=30,
            exchange=Task.ExchangeMode.EXPENSES_COVERED,
            reward_amount=600,
            capacity=10,
            risk=Task.TaskRisk.MEDIUM,
            has_checkin=True,
            gender_preference=Task.GenderPreference.FEMALE_ONLY,
        ),
    ]


def _auctions(now, members) -> list[dict]:
    h = lambda n: now + timedelta(hours=n)  # noqa: E731

    def bid(key, amount, minutes_ago):
        return (key, amount, minutes_ago)

    return [
        dict(
            seller=members["u1"],
            title="Wooden Gaming Desk & Ergonomic Chair Set",
            description="Vacating flat in Madiwala 5th Block. Selling high-grade teak desk + ergonomic mesh chair. Perfect condition, 6 months old.",
            category="Home & Room",
            image_url="https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=600&auto=format&fit=crop",
            base_price=1500,
            current_bid=2800,
            buy_it_now_price=4500,
            start_time=now - timedelta(hours=12),
            end_time=h(4.4),
            total_bids=14,
            status=AuctionItem.Status.ACTIVE,
            area="Madiwala · 5th Block",
            distance_km=0.6,
            seed_bids=[bid("u5", 2800, 12), bid("u2", 2500, 45)],
        ),
        dict(
            seller=members["u2"],
            title="1-on-1 Flutter & UI/UX Portfolio Consultation (2 Hours)",
            description="Offering 2 hours of live code review, portfolio critique, and Flutter architecture mentoring. Verified senior dev.",
            category="Time & Service",
            image_url="https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=600&auto=format&fit=crop",
            base_price=500,
            current_bid=1200,
            buy_it_now_price=2000,
            start_time=now - timedelta(hours=6),
            end_time=h(1.2),
            total_bids=9,
            status=AuctionItem.Status.ENDING_SOON,
            area="Online / Madiwala Cafe",
            distance_km=0.3,
            seed_bids=[bid("u7", 1200, 5)],
        ),
        dict(
            seller=members["u4"],
            title="Sony WH-1000XM4 Noise Canceling Headphones",
            description="Barely used for 2 months, original box and bill available. Selling because I upgraded.",
            category="Gadgets",
            image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop",
            base_price=5000,
            current_bid=9500,
            buy_it_now_price=14000,
            start_time=now - timedelta(hours=24),
            end_time=h(18.7),
            total_bids=22,
            status=AuctionItem.Status.ACTIVE,
            area="Madiwala · Jyoti Nivas Lane",
            distance_km=1.1,
            seed_bids=[],
        ),
        dict(
            seller=members["u8"],
            title="Vintage Leather Jacket (Unisex, Size M)",
            description="Genuine vintage dark brown leather jacket. Excellent condition, polished.",
            category="Fashion & Wear",
            image_url="https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&auto=format&fit=crop",
            base_price=800,
            current_bid=1400,
            buy_it_now_price=2500,
            start_time=now - timedelta(hours=18),
            end_time=h(8.25),
            total_bids=7,
            status=AuctionItem.Status.ACTIVE,
            area="Madiwala · Koramangala Border",
            distance_km=1.4,
            seed_bids=[],
        ),
    ]

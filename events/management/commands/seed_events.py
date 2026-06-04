from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time
from django.core.files.base import ContentFile
from events.models import Event, Venue

import requests


class Command(BaseCommand):
    help = 'Seeds the database with sample events including real posters'

    def handle(self, *args, **kwargs):

        try:
            organizer = User.objects.filter(groups__name='Teacher').first()

            if not organizer:
                organizer = User.objects.filter(is_superuser=True).first()

            if not organizer:
                self.stdout.write(
                    self.style.ERROR(
                        'No teacher or superuser found. Create one first.'
                    )
                )
                return

            venues = list(Venue.objects.filter(is_active=True))

            if not venues:
                self.stdout.write(
                    self.style.ERROR(
                        'No venues found. Create venues first.'
                    )
                )
                return

            today = timezone.localdate()

            profile = (
                organizer.profile
                if hasattr(organizer, 'profile')
                else None
            )

            events_data = [

                {

                    'title': 'NexusFlow Hackathon 2025',

                    'description':
                    '24-hour coding competition open to all students. Build real-world solutions using AI and web technologies.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1515879218367-8466d910aaa4',

                    'date': today + timedelta(days=8),
                    'start_time': time(9, 0),
                    'end_time': time(18, 0),
                    'expected_crowd': 200,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[0],
                },

                {
                    'title': 'Utsav 2025 — Annual Cultural Festival',

                    'description':
                    'Three days of music, dance, drama, poetry slam, and fine arts.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f',

                    'date': today + timedelta(days=14),
                    'start_time': time(10, 0),
                    'end_time': time(21, 0),
                    'expected_crowd': 1500,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[3] if len(venues) > 3 else venues[0],
                },

                {
                    'title': 'Django REST Framework Workshop — Hands-On',

                    'description':
                    'Full-day workshop covering DRF, serializers, JWT auth and deployment.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1516321318423-f06f85e504b3',

                    'date': today + timedelta(days=5),
                    'start_time': time(10, 0),
                    'end_time': time(17, 0),
                    'expected_crowd': 50,
                    'status': 'APPROVED',
                    'is_general': False,
                    'venue': venues[4] if len(venues) > 4 else venues[1],
                },

                {
                    'title': 'Tech Talk Series — AI in Healthcare',

                    'description':
                    'Guest lecture on ML diagnostics, medical AI and ethical healthcare systems.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f',

                    'date': today + timedelta(days=3),
                    'start_time': time(14, 0),
                    'end_time': time(16, 30),
                    'expected_crowd': 120,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[1] if len(venues) > 1 else venues[0],
                },

                {
        
                    'title': 'NexusFlow Debate Championship 2025',

                    'description':
                    'Annual parliamentary debate championship for all colleges.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1522202176988-66273c2fd55f',

                    'date': today + timedelta(days=20),
                    'start_time': time(9, 30),
                    'end_time': time(17, 0),
                    'expected_crowd': 80,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[1] if len(venues) > 1 else venues[0],
                },

                {
                    
                    'title': 'Photography Exhibition — Frames of Life',

                    'description':
                    'Visual storytelling exhibition by the Photography Club.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee',

                    'date': today + timedelta(days=12),
                    'start_time': time(11, 0),
                    'end_time': time(18, 0),
                    'expected_crowd': 300,
                    'status': 'PENDING',
                    'is_general': False,
                    'venue': venues[0],
                },

                {
                   
                    'title': 'E-Summit 2025 — Build, Pitch, Fund',

                    'description':
                    'Startup summit featuring founders, VCs, mentors and live pitches.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1552664730-d307ca884978',

                    'date': today + timedelta(days=25),
                    'start_time': time(8, 30),
                    'end_time': time(18, 0),
                    'expected_crowd': 400,
                    'status': 'PENDING',
                    'is_general': True,
                    'venue': venues[0],
                },

                {
                    
                    'title': 'Freshman Orientation Day 2024',

                    'description':
                    'Welcome event for incoming students with faculty sessions and campus tours.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1523240795612-9a054b0db644',

                    'date': today - timedelta(days=30),
                    'start_time': time(9, 0),
                    'end_time': time(15, 0),
                    'expected_crowd': 600,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[0],
                },

                {
                    
                    'title': '6-Hour Competitive Coding Sprint',

                    'description':
                    'Competitive programming event with algorithmic challenges.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1517694712202-14dd9538aa97',

                    'date': today - timedelta(days=15),
                    'start_time': time(10, 0),
                    'end_time': time(16, 0),
                    'expected_crowd': 100,
                    'status': 'APPROVED',
                    'is_general': False,
                    'venue': venues[4] if len(venues) > 4 else venues[1],
                },

                {
                    
                    
                    'title': 'Mind Matters — Mental Health & Wellbeing Workshop',

                    'description':
                    'Workshop on stress management, anxiety handling and emotional wellbeing.',

                    'poster_url':
                    'https://images.unsplash.com/photo-1493836512294-502baa1986e2',

                    'date': today - timedelta(days=7),
                    'start_time': time(15, 0),
                    'end_time': time(17, 30),
                    'expected_crowd': 60,
                    'status': 'APPROVED',
                    'is_general': True,
                    'venue': venues[2] if len(venues) > 2 else venues[1],
                },

            ]

            created = 0

            for data in events_data:

                venue = data.pop('venue')

                poster_url = data.pop('poster_url')

                event_date = data['date']

                start_dt = timezone.make_aware(
                    __import__('datetime').datetime.combine(
                        event_date,
                        data['start_time']
                    )
                )

                end_dt = timezone.make_aware(
                    __import__('datetime').datetime.combine(
                        event_date,
                        data['end_time']
                    )
                )

                reg_start = start_dt - timedelta(days=7)
                reg_end = start_dt - timedelta(hours=2)

                event = Event.objects.create(
                    organizer=organizer,
                    college_profile=profile,
                    venue=venue,
                    title=data['title'],
                    description=data['description'],
                    date=event_date,
                    start_time=data['start_time'],
                    end_time=data['end_time'],
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    expected_crowd=data['expected_crowd'],
                    status=data['status'],
                    is_general=data['is_general'],
                    registration_start=reg_start,
                    registration_end=reg_end,
                    ai_venue_reason='Auto-assigned by seed command.',
                    night_event_warning=(
                        data['end_time'].hour >= 18
                    ),
                )

                try:
                    response = requests.get(poster_url)

                    if response.status_code == 200:

                        event.poster.save(
                            f"{event.title}.jpg",
                            ContentFile(response.content),
                            save=True
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Poster added for: {event.title}"
                            )
                        )

                except Exception as poster_error:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Poster failed for {event.title}: {poster_error}"
                        )
                    )

                created += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created: {event.title} [{event.status}]"
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDone. Created {created} events.'
                )
            )

        except Exception as e:

            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )

            import traceback
            traceback.print_exc()
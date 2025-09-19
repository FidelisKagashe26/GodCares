from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from content.models import Category, Post, Season, Series, Lesson, Event, MediaItem
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create sample data for development'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@godcares365.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(f'Created admin user: admin/admin123')
        else:
            admin_user = User.objects.get(username='admin')

        # Create categories
        categories_data = [
            {'name': 'Kiroho', 'description': 'Makala za kiroho na imani'},
            {'name': 'Jamii', 'description': 'Habari za jamii na matukio'},
            {'name': 'Mafunzo', 'description': 'Masomo ya Biblia na mafunzo'},
            {'name': 'Matukio', 'description': 'Matukio maalum na mikutano'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create seasons
        seasons_data = [
            {
                'name': 'Agano Jipya 2024',
                'description': 'Mafunzo ya kina ya vitabu vya Agano Jipya',
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=365),
                'is_active': True,
                'order': 1
            },
            {
                'name': 'Agano la Kale 2024',
                'description': 'Safari kupitia historia ya Israeli na mafunzo ya nabii',
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=365),
                'is_active': True,
                'order': 2
            }
        ]
        
        for season_data in seasons_data:
            season, created = Season.objects.get_or_create(
                name=season_data['name'],
                defaults=season_data
            )
            if created:
                self.stdout.write(f'Created season: {season.name}')

        # Create series
        nt_season = Season.objects.get(name='Agano Jipya 2024')
        ot_season = Season.objects.get(name='Agano la Kale 2024')
        
        series_data = [
            {
                'name': 'Injili za Kwanza',
                'description': 'Masomo ya Mathayo, Marko, Luka na Yohana',
                'season': nt_season,
                'order': 1
            },
            {
                'name': 'Matendo ya Mitume',
                'description': 'Historia ya kanisa la kwanza',
                'season': nt_season,
                'order': 2
            },
            {
                'name': 'Vitabu vya Torati',
                'description': 'Mwanzo, Kutoka, Mambo ya Walawi, Hesabu na Kumbukumbu',
                'season': ot_season,
                'order': 1
            }
        ]
        
        for series_data in series_data:
            series, created = Series.objects.get_or_create(
                name=series_data['name'],
                season=series_data['season'],
                defaults=series_data
            )
            if created:
                self.stdout.write(f'Created series: {series.name}')

        # Create sample posts
        kiroho_category = Category.objects.get(name='Kiroho')
        posts_data = [
            {
                'title': 'Jinsi ya Kujenga Imani Imara',
                'content': '''
                <h2>Utangulizi</h2>
                <p>Imani ni msingi wa kila kitu tunachofanya kama wakristo. Bila imani, haiwezekani kumpendeza Mungu (Waebrania 11:6).</p>
                
                <h2>Msingi wa Imani</h2>
                <p>Imani ni kuamini kile tusichokiona, lakini tunakijua ni kweli kwa sababu Mungu amesema.</p>
                
                <h2>Jinsi ya Kuimarisha Imani</h2>
                <ul>
                    <li><strong>Kusoma Biblia kila siku:</strong> Neno la Mungu ni chakula cha roho yetu</li>
                    <li><strong>Maombi ya kila siku:</strong> Mawasiliano na Mungu ni muhimu</li>
                    <li><strong>Kushiriki na waumini wengine:</strong> Umoja unatupa nguvu</li>
                    <li><strong>Kutenda mema:</strong> Imani bila matendo ni maiti</li>
                </ul>
                
                <h2>Hitimisho</h2>
                <p>Imani ni safari, si hatua moja. Kila siku ni fursa ya kuimarisha uhusiano wetu na Mungu.</p>
                ''',
                'excerpt': 'Jifunze jinsi ya kujenga imani isiyoyumba katika magumu ya maisha.',
                'category': kiroho_category,
                'author': admin_user,
                'status': 'published',
                'featured': True,
                'published_at': timezone.now()
            },
            {
                'title': 'Umuhimu wa Maombi ya Pamoja',
                'content': '''
                <h2>Maombi ya Pamoja</h2>
                <p>Yesu alisema: "Tena nawaambieni, ikiwa wawili kati yenu watakubaliana duniani juu ya jambo lolote wataloomba, litawafanyiwa na Baba yangu aliye mbinguni." - Mathayo 18:19</p>
                
                <h2>Faida za Maombi ya Pamoja</h2>
                <ul>
                    <li>Kuimarisha umoja wa kiroho</li>
                    <li>Kushirikiana katika mizigo</li>
                    <li>Kuongeza nguvu ya imani</li>
                </ul>
                ''',
                'excerpt': 'Maombi ya pamoja yana nguvu maalum katika maisha ya mwamini.',
                'category': kiroho_category,
                'author': admin_user,
                'status': 'published',
                'featured': False,
                'published_at': timezone.now()
            }
        ]
        
        for post_data in posts_data:
            post, created = Post.objects.get_or_create(
                title=post_data['title'],
                defaults=post_data
            )
            if created:
                self.stdout.write(f'Created post: {post.title}')

        # Create sample lessons
        injili_series = Series.objects.get(name='Injili za Kwanza')
        lessons_data = [
            {
                'title': 'Utangulizi wa Injili ya Mathayo',
                'description': 'Jifunze kuhusu muandishi, lengo, na ujumbe mkuu wa Injili ya Mathayo.',
                'content': '''
                <h2>Utangulizi</h2>
                <p>Injili ya Mathayo ni kitabu cha kwanza katika Agano Jipya na kimoja kwa vitabu muhimu zaidi katika Ukristo.</p>
                
                <h2>Muandishi</h2>
                <p>Mathayo, aliyeitwa pia Lawi, alikuwa mtoza ushuru kabla ya kumfuata Yesu.</p>
                
                <h2>Lengo la Kitabu</h2>
                <ul>
                    <li>Kuonyesha kwamba Yesu ndiye Masihi wa Israeli</li>
                    <li>Kueleza jinsi ufalme wa imbingu unavyofanya kazi</li>
                    <li>Kutoa mafundisho ya Yesu kwa utaratibu</li>
                </ul>
                ''',
                'series': injili_series,
                'bible_references': 'Mathayo 1:1-17',
                'duration_minutes': 45,
                'status': 'published',
                'order': 1
            },
            {
                'title': 'Uzazi wa Yesu - Mathayo 1:18-25',
                'description': 'Mujiza wa uzazi wa Yesu na maana yake kwa wanadamu.',
                'content': '''
                <h2>Uzazi wa Ajabu</h2>
                <p>Uzazi wa Yesu ulikuwa wa kipekee katika historia ya binadamu.</p>
                
                <h2>Maana ya Jina "Yesu"</h2>
                <p>"Yesu" maana yake ni "Bwana anaokoa" - jina lililotolewa na malaika.</p>
                ''',
                'series': injili_series,
                'bible_references': 'Mathayo 1:18-25',
                'duration_minutes': 30,
                'status': 'published',
                'order': 2
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                title=lesson_data['title'],
                series=lesson_data['series'],
                defaults=lesson_data
            )
            if created:
                self.stdout.write(f'Created lesson: {lesson.title}')

        # Create sample events
        events_data = [
            {
                'title': 'Semina ya Maombi ya Kina',
                'description': 'Jiunge nasi katika semina ya siku tatu ya kujifunza jinsi ya kuomba kwa kina na kupata majibu ya maombi yako.',
                'location': 'Kanisa la Kimataifa, Dar es Salaam',
                'date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=32),
                'is_featured': True,
                'max_attendees': 200
            },
            {
                'title': 'Mkutano wa Vijana wa Imani',
                'description': 'Mkutano maalum wa vijana kujadili changamoto za kisasa na jinsi ya kuishi maisha ya kikristo.',
                'location': 'Uwanja wa Michezo, Mwanza',
                'date': timezone.now() + timedelta(days=45),
                'end_date': timezone.now() + timedelta(days=45),
                'is_featured': False,
                'max_attendees': 500
            }
        ]
        
        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Created event: {event.title}')

        # Create sample media items
        media_data = [
            {
                'title': 'Mahubiri ya Jumapili: Upendo wa Mungu',
                'description': 'Mahubiri kamili kuhusu upendo wa Mungu na jinsi unavyoathiri maisha yetu ya kila siku.',
                'media_type': 'video',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'category': kiroho_category,
                'tags': 'upendo, Mungu, mahubiri'
            },
            {
                'title': 'Mwongozo wa Kusoma Biblia',
                'description': 'Kitabu cha mwongozo wa jinsi ya kusoma na kuelewa Biblia kwa ufanisi.',
                'media_type': 'document',
                'category': kiroho_category,
                'tags': 'mwongozo, biblia, kusoma'
            }
        ]
        
        for media_item_data in media_data:
            media_item, created = MediaItem.objects.get_or_create(
                title=media_item_data['title'],
                defaults=media_item_data
            )
            if created:
                self.stdout.write(f'Created media item: {media_item.title}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
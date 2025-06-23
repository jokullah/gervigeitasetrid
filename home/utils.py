from django.db.models import Count

from base.models import Tag, TaggedItem

def get_tag_cloud_data():
    tag_counts = (
            TaggedItem.objects
            .values('tag')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
    tags = Tag.objects.in_bulk([item['tag'] for item in tag_counts])
    return [
        {
            "name": tags[item['tag']].name,
            "count": item['count'],
            "id": tags[item['tag']].id,
            "color": tags[item['tag']].color,
        }
        for item in tag_counts if item['tag'] in tags
    ]



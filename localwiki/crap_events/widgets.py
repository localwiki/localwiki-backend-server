from pages.widgets import WikiEditor    


class EventWikiEditor(WikiEditor):
    def get_toolbar(self):
        basic_styles = ['Bold', 'Italic']
        links = ['PageLink']
        media = ['InsertImage']
        lists = ['NumberedList', 'BulletedList']

        return [basic_styles, links, media, lists]

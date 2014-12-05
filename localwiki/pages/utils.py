def is_user_page(page):
    return page.name.lower().startswith('users/') and len(page.name.split('/')) == 1

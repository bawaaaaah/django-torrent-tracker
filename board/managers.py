from django.db import models
from django.db.models import Q
from django.conf import settings

class ThreadManager(models.Manager):
    def get_query_set(self):
	"""
	This generates a QuerySet containing Threads and additional data used
	in generating a web page with a listing of discussions.
	django qset allows the caller to specify an initial 
	queryset to work with.  If this is not set, all Threads will be
	returned.
	"""
	# number of posts in thread
	# censored threads don't count toward the total
	extra_post_count = """
	    SELECT COUNT(1) FROM board_post
	    WHERE board_post.thread_id = board_thread.id
	    AND NOT board_post.censored
	"""
	# figure out who started the discussion
	if settings.DATABASE_ENGINE == 'mysql':
	    extra_starter = """
	     SELECT CASE WHEN first_name!='' THEN first_name
	     WHEN openid!='' THEN trim('http://' FROM openid)
	     WHEN username!='' THEN username END FROM auth_user
	     WHERE auth_user.id = (SELECT author_id
	     FROM board_post WHERE board_post.thread_id = board_thread.id
	     ORDER BY board_post.created ASC
	     LIMIT 1)
	    """
	else:
	    extra_starter = """
	     SELECT CASE WHEN first_name!='' THEN first_name
	     WHEN openid!='' THEN trim(openid, 'http://')
	     WHEN username!='' THEN username END FROM auth_user
	     WHERE auth_user.id = (SELECT author_id
	     FROM board_post WHERE board_post.thread_id = board_thread.id
	     ORDER BY board_post.created ASC
	     LIMIT 1)
	    """
	if settings.DATABASE_ENGINE == 'mysql':
	    extra_last_poster = """
	     SELECT CASE WHEN first_name!='' THEN first_name
	     WHEN openid!='' THEN trim('http://' FROM openid)
	     WHEN username!='' THEN username END FROM auth_user
	     WHERE auth_user.id = (SELECT author_id
	     FROM board_post WHERE board_post.thread_id = board_thread.id
	     ORDER BY board_post.created DESC
	     LIMIT 1)
	    """
	else:
	    extra_last_poster = """
	     SELECT CASE WHEN first_name!='' THEN first_name
	     WHEN openid!='' THEN trim(openid, 'http://')
	     WHEN username!='' THEN username END FROM auth_user
	     WHERE auth_user.id = (SELECT author_id
	     FROM board_post WHERE board_post.thread_id = board_thread.id
	     ORDER BY board_post.created DESC
	     LIMIT 1)
	    """
	extra_last_updated = """
	    SELECT created FROM board_post
	    WHERE board_post.thread_id = board_thread.id
	    ORDER BY created DESC LIMIT 1
	"""
	return super(ThreadManager, self).get_query_set().extra(
	    select = {
		'post_count': extra_post_count,
		'starter': extra_starter,
		'created': extra_last_updated,
		'last_poster': extra_last_poster,
	    },).order_by('-gsticky', 'created')

    def get_watched(self, user):
	ids = user.attrs.get('watchlist')
	if ids:
	    return self.get_query_set().filter(pk__in=ids)
	else:
	    return []

    def get_forum(self, forum_slug):
	return self.get_query_set().filter(forum__slug=forum_slug)

class PostManager(models.Manager):
    def get_query_set(self):
	extra_post_author_prefs = """
	    SELECT prefs FROM auth_user WHERE id = board_post.author_id
	"""
	extra_abuse_count = """
	    SELECT COUNT(1) FROM board_abusereport
	    WHERE board_post.id = board_abusereport.post_id
	"""
	return super(PostManager, self).get_query_set().extra(
	select = {
	    'prefs': extra_post_author_prefs,
	    'abuse': extra_abuse_count,
	}).order_by('created')

    def posts_for_thread(self, thread_id, user):
	qs = self.get_query_set().filter(thread__id=thread_id)
	if not getattr(user, 'is_staff', False):
	    qs = qs.exclude(censored=True)
	return qs

class ForumManager(models.Manager):
    def get_query_set(self):
	thread_count = """
	SELECT COUNT(1) FROM board_thread
	WHERE board_thread.forum_id = board_forum.id
	"""
	return super(ForumManager, self).get_query_set().extra(
	    select = {'thread_count': thread_count})


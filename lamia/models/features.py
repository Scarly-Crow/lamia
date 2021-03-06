"""Models in this module are the sugar that makes lamia worth using over
just a plain federator. They're directly or indirectly associated with the
user-level things that make ActivityPub taste better.
"""
import bcrypt
from lamia.database import db


class Account(db.Model):
    """Login details for user actors are stored here. Accounts in lamia are
    best explained as being containers for blogs and identities, where both of
    these are 1-to-1 connections to ActivityPub actors.

    Basically, an account on lamia can own multiple identities and blogs. These
    identities and blogs are what others see when someone with an account makes
    a post.

    TODO: to prevent intentional/unintentional abuse, this needs to be VERY
    transparent.
    """
    __tablename__ = 'accounts'

    id = db.Column(db.Integer(), primary_key=True)
    primary_identity_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'identities.id',
            ondelete='SET NULL',
            name='fk_actor_primary_identity'),
        nullable=True,
    )
    email_address = db.Column(db.String())
    # Should be a hash encrypted by scrypt
    password = db.Column(db.String())
    created = db.Column(db.DateTime())
    # Activates low bandwidth mode to control image transmissions
    low_bandwidth = db.Column(db.Boolean())
    # Content should be hidden and attachments marked as sensitive by default
    sensitive_content = db.Column(db.Boolean())
    # All follows require confirmation if this is true
    approval_for_follows = db.Column(db.Boolean())

    # Either someone is banned or not banned.
    # Problematic users, nazis, etc should be banned without mercy or guilt.
    # Just fucking do it, they aren't worth having around.
    # You shouldn't even have to think about it. Do it. Do it now.
    # Unless a deletion is desired. In which case, there is a way to do this.
    banned = db.Column(db.Boolean())
    # Profile customizations enabled/disabled for this account
    disable_profile_customizations = db.Column(db.Boolean())

    def set_password(self, password: str) -> None:
        """Hash a plaintext password and set the class property."""
        self.password = bcrypt.hashpw(password.encode(),
                                      bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        """Compare a plaintext password to the class property."""
        return bcrypt.checkpw(password.encode(), self.password.encode())


class Identity(db.Model):
    """An account can have more than one identity. Each identity connects an
    account to a single ActivityPub actor.

    Identities hold all of the profile customization details that are not
    contained within an actor model.
    """
    __tablename__ = 'identities'

    id = db.Column(db.Integer(), primary_key=True)
    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE', name='fk_identity_actor'),
    )
    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'accounts.id', ondelete='CASCADE', name='fk_identity_account'),
    )
    display_name = db.Column(db.String())
    user_name = db.Column(db.String())
    # Non-standard profile customizations
    page_background_color = db.Column(db.String())
    page_background_image = db.Column(db.String())
    page_background_tiled = db.Column(db.Boolean())
    page_background_static = db.Column(db.Boolean())
    section_background_color = db.Column(db.String())
    section_header_image = db.Column(db.String())
    section_text_color = db.Column(db.String())
    section_text_shadow = db.Column(db.Boolean())
    section_text_shadow_color = db.Column(db.Boolean())
    # Can be disabled
    disabled = db.Column(db.Boolean())
    # Can be soft deleted. To permanently delete, delete the associated account.
    # This is done to prevent abuse in the form of rapidly created temporary
    # accounts being used to torment and then removed after a block/mute.
    deleted = db.Column(db.Boolean())
    created = db.Column(db.DateTime())
    last_updated = db.Column(db.DateTime())


class Blog(db.Model):
    """An account can have more than one blog. Each blog connects an
    account to a single ActivityPub actor.
    """
    __tablename__ = 'blogs'

    id = db.Column(db.Integer(), primary_key=True)
    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey('actors.id', ondelete='CASCADE', name='fk_blog_actor'),
    )

    # Non-standard profile customizations
    page_background_color = db.Column(db.String())
    page_background_image = db.Column(db.String())
    page_background_tiled = db.Column(db.Boolean())
    page_background_static = db.Column(db.Boolean())
    section_background_color = db.Column(db.String())
    section_header_image = db.Column(db.String())
    section_text_color = db.Column(db.String())
    section_text_shadow = db.Column(db.Boolean())
    section_text_shadow_color = db.Column(db.Boolean())
    # Can be disabled
    disabled = db.Column(db.Boolean())
    # Can be soft deleted. To permanently delete, delete the associated account.
    # This is done to prevent abuse in the form of rapidly created temporary
    # accounts being used to torment and then removed after a block/mute.
    deleted = db.Column(db.Boolean())
    created = db.Column(db.DateTime())
    last_updated = db.Column(db.DateTime())


class Interest(db.Model):
    """A hashtag but for actors. Maps tags to actors. Works similarly to
    the FeedTag model but has a much broader use-case. Basically, can be
    used to find users with similar interests.
    """
    __tablename__ = 'interests'
    id = db.Column(db.Integer(), primary_key=True)

    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE', name='fk_interest_map_actor'),
    )
    tag_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'tags.id', ondelete='CASCADE', name='fk_interest_map_tag'),
    )


class Block(db.Model):
    """Blocking a user is the strongest user to user moderation action.

    It's a way of saying, "remove all of this user's stuff from my sight."

    Blocking a user prevents all interaction between the users, breaks follows,
    and more or less cleanses the timeline of that user.

    Blocks are officially a part of the ActivityPub specification, but I am
    calling them out explicitly with a seperate model for consistency.
    """
    __tablename__ = 'blocks'

    id = db.Column(db.Integer(), primary_key=True)
    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'accounts.id', ondelete='CASCADE', name='fk_block_account'))
    target_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'accounts.id', ondelete='CASCADE', name='fk_block_actor'))
    created = db.Column(db.DateTime())


class Mute(db.Model):
    """Muting a user is a lightweight user to user moderation action.

    It's a way of saying, "you're a bit much. i need some space." This can be a
    temporary mute, for example, just for a moment to allow someone else to
    cool down.

    Muting a user silences notifications, maintains follows, and either
    squelches them from timelines or minimizes them.
    """
    __tablename__ = 'mutes'

    id = db.Column(db.Integer(), primary_key=True)
    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'accounts.id', ondelete='CASCADE', name='fk_mute_account'),
    )
    target_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey('actors.id', ondelete='CASCADE', name='fk_mute_actor'),
    )
    created = db.Column(db.DateTime())


class Filter(db.Model):
    """Filters are best described as a more nuanced version of muting, allowing
    specific words to be removed from a timeline or minimized within the
    timeline.
    """
    __tablename__ = 'filters'

    id = db.Column(db.Integer(), primary_key=True)
    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'accounts.id', ondelete='CASCADE', name='fk_filter_account'),
    )

    query = db.Column(db.String)
    hide = db.Column(db.Boolean)
    minimize = db.Column(db.Boolean)
    filter_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE',
            name='fk_filter_applied_to_actor'),
    )

    created = db.Column(db.DateTime())
    duration = db.Column(db.Interval())
    forever = db.Column(db.Boolean())


class Feed(db.Model):
    """A feed is a set of actors that you want to create a custom timeline
    for. As an example, you could create a feed labeled "friends" for calling
    out your friends' blog posts and statuses.

    It's worth noting that you need to subscribe to an actor before this works.
    """
    __tablename__ = 'feeds'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    identity_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'identities.id', ondelete='CASCADE', name='fk_feed_identity'),
    )
    created = db.Column(db.DateTime())


class FeedActor(db.Model):
    """A single actor watched by a feed."""
    __tablename__ = 'feed_actors'

    id = db.Column(db.Integer(), primary_key=True)
    feed_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'feeds.id', ondelete='CASCADE', name='fk_feedactor_feed'),
    )
    target_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE', name='fk_feedactor_actor'))
    created = db.Column(db.DateTime())


class Tag(db.Model):
    """The metaphysical concept of the hashtag, made real and without conceit."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer(), primary_key=True)
    tag = db.Column(db.String())
    created = db.Column(db.DateTime())


class ObjectTag(db.Model):
    """A crosswalk table that ties tags to objects, for ease of querying."""
    __tablename__ = 'object_tags'

    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(
        db.Integer(),
        db.ForeignKey('tags.id', ondelete='CASCADE', name='fk_objecttag_tag'),
    )
    object_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'objects.id', ondelete='CASCADE', name='fk_objecttag_object'))
    created = db.Column(db.DateTime())


class FeedTag(db.Model):
    """A single tag watched by a feed."""
    __tablename__ = 'feed_tags'

    id = db.Column(db.Integer(), primary_key=True)
    feed_id = db.Column(
        db.Integer(),
        db.ForeignKey('feeds.id', ondelete='CASCADE', name='fk_feedtag_feed'),
    )
    target_tag_id = db.Column(
        db.Integer(),
        db.ForeignKey('tags.id', ondelete='CASCADE', name='fk_feedtag_tag'),
    )
    created = db.Column(db.DateTime())


class Attachments(db.Model):
    """An attachment is an image tied to some kind of ActivityPub object.

    TODO: We can look into non-image attachments and probably dismiss the
    possibility of them later on.
    """
    __tablename__ = 'attachments'

    id = db.Column(db.Integer(), primary_key=True)
    uploaded_by_actor_uri = db.Column(db.String())
    alt_text = db.Column(db.String())

    storage_path = db.Column(db.String())
    storage_uri = db.Column(db.String())
    remote_uri = db.Column(db.String())

    size_in_bytes = db.Column(db.Integer())
    local = db.Column(db.Boolean())

    created = db.Column(db.DateTime())


class BookmarkGroup(db.Model):
    """Bookmark groups can be implicitly created to organize bookmarks"""
    __tablename__ = 'bookmark_groups'

    id = db.Column(db.Integer(), primary_key=True)
    group = db.Column(db.String())

    created = db.Column(db.DateTime())


class Bookmark(db.Model):
    """A bookmark is a "saved" link to an ActivityPub object that is not
    an actor."""
    __tablename__ = 'boookmarks'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String())

    object_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'objects.id', ondelete='CASCADE', name='fk_bookmark_object'))

    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE', name='fk_bookmark_actor'))

    group_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'bookmark_groups.id',
            ondelete='SET NULL',
            name='fk_bookmark_group'),
        nullable=True)

    created = db.Column(db.DateTime())


class Notification(db.Model):
    """Our fancy notification class."""
    id = db.Column(db.Integer(), primary_key=True)

    category = db.Column(db.String())
    object_uri = db.Column(db.String())
    icon = db.Column(db.String())

    seen = db.Column(db.Boolean())
    acknowledged = db.Column(db.Boolean())

    created_by_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='SET NULL', name='fk_notification_by_actor'),
        nullable=True,
    )
    for_identity_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'identities.id',
            ondelete='CASCADE',
            name='fk_notification_for_identity'),
    )
    created = db.Column(db.DateTime())


class Follow(db.Model):
    """Subscriptions are a link between actors. When you subscribe, you are
    saying, "yes, please, show me the things that you create."

    This activity is explicitly supported by ActivityPub, but I call it out
    explicitly for convenience. Explicitly..
    """
    __tablename__ = 'follows'

    id = db.Column(db.Integer(), primary_key=True)
    actor_id = db.Column(
        db.Integer(),
        db.ForeignKey('actors.id', ondelete='CASCADE', name='fk_follow_actor'),
    )
    target_actor_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'actors.id', ondelete='CASCADE', name='fk_follow_target_actor'),
    )

    # Waiting for account review
    pending_review = db.Column(db.Boolean())
    # Approved by actor owner
    approved = db.Column(db.Boolean())
    # Hard rejected by owner, all future requests will also be blocked
    blocked = db.Column(db.Boolean())

    created = db.Column(db.DateTime())
    last_updated = db.Column(db.DateTime())
